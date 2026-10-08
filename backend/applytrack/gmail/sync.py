"""Gmail sync: full initial pull, then incremental via historyId.

Lands raw emails in SQLite, classifies each new one inline (per the chosen
design), groups them into applications, and recomputes per-application status.
Full email bodies are never persisted — only a snippet — and never logged.
"""

from __future__ import annotations

import base64
import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

from googleapiclient.errors import HttpError
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..classify.base import Classifier, EmailInput, get_classifier
from ..config import get_settings
from ..grouping import (
    counterparty_address,
    extract_job_ref,
    extract_role,
    extract_role_from_body,
    is_ignored_sender,
    job_group_key,
    resolve_company,
)
from ..lang import detect_language
from ..models import Application, Email, SyncState
from ..status import EmailEvent, Status, _as_aware, derive_status
from .auth import get_connected_address, get_gmail_service

logger = logging.getLogger("applytrack.sync")

_SNIPPET_LEN = 500
_MAX_RETRIES = 5


@dataclass(slots=True)
class SyncResult:
    new_emails: int = 0
    classified: int = 0
    applications: int = 0
    message: str = ""


@dataclass(slots=True)
class _ParsedMessage:
    gmail_id: str
    thread_id: str
    direction: str
    sender: str
    recipient: str
    subject: str
    body: str
    received_at: datetime


# --- Public entry point ------------------------------------------------------


def sync_mailbox(session: Session, *, full: bool = False) -> SyncResult:
    """Synchronise new mail and return a summary.

    If ``full`` is True (or no prior cursor exists), performs a full message
    listing; otherwise uses the Gmail history API for an incremental delta.
    """
    service = get_gmail_service()
    self_address = (get_connected_address() or "").lower()
    state = _get_or_create_state(session, self_address)
    classifier = get_classifier()

    if full or not state.last_history_id:
        message_ids = _list_all_message_ids(service)
        logger.info("Full sync: %d messages in mailbox.", len(message_ids))
    else:
        message_ids, reset = _list_history_message_ids(service, state.last_history_id)
        if reset:
            logger.info("History cursor expired; falling back to full sync.")
            message_ids = _list_all_message_ids(service)

    result = SyncResult()
    touched_apps: set[int] = set()

    for gid in message_ids:
        if _email_exists(session, gid):
            continue
        try:
            parsed = _fetch_and_parse(service, gid)
        except HttpError as exc:
            logger.warning("Skipping message %s: %s", gid, exc.resp.status if exc.resp else exc)
            continue
        if parsed is None:
            continue

        email = _persist_email(session, parsed, classifier)
        result.new_emails += 1
        result.classified += 1
        if email.application_id is not None:
            touched_apps.add(email.application_id)

    # Recompute aggregates/status for every application that gained emails.
    for app_id in touched_apps:
        _recompute_application(session, app_id)

    result.applications = len(touched_apps)

    # Advance the incremental cursor.
    new_history_id = _current_history_id(service)
    if new_history_id:
        state.last_history_id = new_history_id
    state.last_synced_at = datetime.now(UTC)
    session.add(state)
    session.commit()

    result.message = (
        f"Synced {result.new_emails} new email(s) across "
        f"{result.applications} application(s)."
    )
    return result


# --- Gmail listing -----------------------------------------------------------


def _list_all_message_ids(service) -> list[str]:
    ids: list[str] = []
    page_token = None
    while True:
        resp = _execute(
            service.users().messages().list(userId="me", maxResults=500, pageToken=page_token)
        )
        ids.extend(m["id"] for m in resp.get("messages", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return ids


def _list_history_message_ids(service, start_history_id: str) -> tuple[list[str], bool]:
    """Return (message_ids, needs_full_resync)."""
    ids: list[str] = []
    page_token = None
    try:
        while True:
            resp = _execute(
                service.users()
                .history()
                .list(
                    userId="me",
                    startHistoryId=start_history_id,
                    historyTypes=["messageAdded"],
                    pageToken=page_token,
                )
            )
            for record in resp.get("history", []):
                for added in record.get("messagesAdded", []):
                    ids.append(added["message"]["id"])
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
    except HttpError as exc:
        if exc.resp is not None and exc.resp.status == 404:
            return [], True  # historyId too old → caller does full sync
        raise
    return list(dict.fromkeys(ids)), False


def _current_history_id(service) -> str | None:
    try:
        profile = _execute(service.users().getProfile(userId="me"))
        return str(profile.get("historyId")) if profile.get("historyId") else None
    except HttpError:
        return None


# --- Message fetch + parse ---------------------------------------------------


def _fetch_and_parse(service, gmail_id: str) -> _ParsedMessage | None:
    msg = _execute(service.users().messages().get(userId="me", id=gmail_id, format="full"))
    payload = msg.get("payload", {})
    headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
    label_ids = set(msg.get("labelIds", []))

    direction = "sent" if "SENT" in label_ids else "received"
    sender = headers.get("from", "")
    recipient = headers.get("to", "")
    subject = headers.get("subject", "")
    received_at = _parse_date(headers.get("date"), msg.get("internalDate"))
    body = _extract_body(payload) or msg.get("snippet", "")

    return _ParsedMessage(
        gmail_id=gmail_id,
        thread_id=msg.get("threadId", gmail_id),
        direction=direction,
        sender=sender,
        recipient=recipient,
        subject=subject,
        body=body,
        received_at=received_at,
    )


def _extract_body(payload: dict) -> str:
    """Depth-first search for a text/plain part; fall back to text/html stripped."""
    mime = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")

    if mime == "text/plain" and body_data:
        return _decode(body_data)

    html_fallback = ""
    for part in payload.get("parts", []) or []:
        text = _extract_body(part)
        if text and part.get("mimeType") == "text/plain":
            return text
        if text and part.get("mimeType") == "text/html" and not html_fallback:
            html_fallback = text

    if mime == "text/html" and body_data:
        return _strip_html(_decode(body_data))
    if html_fallback:
        return _strip_html(html_fallback)
    return ""


def _decode(data: str) -> str:
    try:
        return base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return ""


def _strip_html(html: str) -> str:
    import re

    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_date(date_header: str | None, internal_date: str | None) -> datetime:
    if date_header:
        try:
            dt = parsedate_to_datetime(date_header)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt
        except (TypeError, ValueError):
            pass
    if internal_date:
        try:
            return datetime.fromtimestamp(int(internal_date) / 1000, tz=UTC)
        except (TypeError, ValueError):
            pass
    return datetime.now(UTC)


# --- Persistence + grouping --------------------------------------------------


def _persist_email(session: Session, parsed: _ParsedMessage, classifier: Classifier) -> Email:
    classification = classifier.classify(
        EmailInput(
            sender=parsed.sender,
            subject=parsed.subject,
            body=parsed.body,
            direction=parsed.direction,
        )
    )
    language = classification.language or detect_language(f"{parsed.subject}\n{parsed.body}")

    email = Email(
        gmail_id=parsed.gmail_id,
        thread_id=parsed.thread_id,
        direction=parsed.direction,
        sender=parsed.sender,
        recipient=parsed.recipient,
        subject=parsed.subject,
        body_snippet=parsed.body[:_SNIPPET_LEN],
        received_at=parsed.received_at,
        intent=classification.intent.value,
        confidence=classification.confidence,
        language=language,
        classifier_source=classification.source,
        reasoning=classification.reasoning,
    )

    # Configured ignore patterns (e.g. recruiting agencies) are filed as noise.
    if is_ignored_sender(parsed.sender, parsed.recipient):
        email.intent = "not_application_related"
        email.reasoning = "Ignored sender (configured ignore list)."
    # Application-related mail is grouped per job (see grouping.job_group_key);
    # pure noise is stored unattached.
    elif classification.intent.value != "not_application_related":
        company_address = counterparty_address(
            parsed.direction, parsed.sender, parsed.recipient
        )
        company = resolve_company(classification, company_address, parsed.subject)
        role = (
            classification.role
            or extract_role(parsed.subject, company)
            or extract_role_from_body(parsed.body, company)
        )
        ref = extract_job_ref(parsed.subject) or extract_job_ref(parsed.body)
        email.application = application_for_email(
            session, parsed.thread_id, company, role, ref, language
        )

    session.add(email)
    session.flush()
    return email


def application_for_email(
    session: Session,
    thread_id: str,
    company: str,
    role: str | None,
    ref: str | None,
    language: str,
) -> Application:
    """Find/create the application a new email belongs to.

    Mail in a thread that already has an application joins it. Otherwise the
    email is matched by job key (reference number, else company + role), so a
    rejection arriving in a new thread lands on the original application.
    """
    job_key = job_group_key(company, role, ref, thread_id)
    thread_app_id = session.execute(
        select(Email.application_id)
        .where(Email.thread_id == thread_id, Email.application_id.is_not(None))
        .limit(1)
    ).scalar_one_or_none()

    if thread_app_id is not None:
        app = session.get(Application, thread_app_id)
        if app is not None:
            _upgrade_application(app, company, role)
            # Promote a thread-keyed application once we know which job it is.
            if app.group_key.startswith("thread:") and job_key.startswith("job:"):
                taken = session.execute(
                    select(Application.id).where(Application.group_key == job_key)
                ).first()
                if not taken:
                    app.group_key = job_key
            return app

    return _find_or_create_application(session, job_key, company, role, language)


def _upgrade_application(app: Application, company: str, role: str | None) -> None:
    """Fill in details we didn't know when the application was created."""
    if role and not app.role:
        app.role = role
    if company and company != "Unknown" and app.company in ("", "Unknown"):
        app.company = company


def _find_or_create_application(
    session: Session, group_key: str, company: str, role: str | None, language: str
) -> Application:
    app = session.execute(
        select(Application).where(Application.group_key == group_key)
    ).scalar_one_or_none()
    if app is not None:
        _upgrade_application(app, company, role)
        return app

    app = Application(
        company=company,
        role=role,
        group_key=group_key,
        language=language,
        current_status=Status.APPLICATION_SENT.value,
    )
    session.add(app)
    session.flush()
    return app


def _recompute_application(session: Session, app_id: int) -> None:
    app = session.get(Application, app_id)
    if app is None:
        return
    emails = list(app.emails)
    if not emails:
        return

    settings = get_settings()
    events = [
        EmailEvent(
            intent=_intent_for(e),
            received_at=e.received_at,
            direction=e.direction,
        )
        for e in emails
    ]
    status = derive_status(events, ghost_threshold_days=settings.ghost_threshold_days)

    # SQLite returns naive datetimes on read while freshly-parsed mail is
    # tz-aware; normalise before comparing so min/max never mix the two.
    all_dates = [_as_aware(e.received_at) for e in emails]
    sent_dates = [_as_aware(e.received_at) for e in emails if e.direction == "sent"]

    app.current_status = status.value
    app.email_count = len(emails)
    app.first_applied_at = min(sent_dates) if sent_dates else min(all_dates)
    app.last_event_at = max(all_dates)
    session.add(app)


def _intent_for(email: Email):
    from ..classify.base import Intent

    return Intent.from_str(email.effective_intent)


# --- State + retry helpers ---------------------------------------------------


def _get_or_create_state(session: Session, address: str) -> SyncState:
    state = session.get(SyncState, 1)
    if state is None:
        state = SyncState(id=1, email_address=address or None)
        session.add(state)
        session.flush()
    elif address and state.email_address != address:
        state.email_address = address
    return state


def _email_exists(session: Session, gmail_id: str) -> bool:
    return (
        session.execute(select(Email.id).where(Email.gmail_id == gmail_id)).first() is not None
    )


def _execute(request):
    """Execute a Gmail API request with backoff on rate limits / 5xx."""
    delay = 1.0
    for attempt in range(_MAX_RETRIES):
        try:
            return request.execute()
        except HttpError as exc:
            status = exc.resp.status if exc.resp is not None else None
            if status in (429, 500, 503) and attempt < _MAX_RETRIES - 1:
                logger.warning("Gmail API %s; retrying in %.1fs", status, delay)
                time.sleep(delay)
                delay *= 2
                continue
            raise
