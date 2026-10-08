"""Re-classify stored emails and rebuild applications — no Gmail sync.

Two phases, both running only on the local database:

1. **Re-classify** every email's intent/confidence/language with the current
   logic. Manual overrides are never touched.
2. **Rebuild applications** from scratch: one application per job (threads
   sharing a job reference or company + role are merged), labelled with the
   best employer name and role we can derive.

Only the stored ``body_snippet`` is available (full bodies are never persisted),
so signals beyond the snippet length cannot be seen.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from .classify.base import EmailInput, Intent, get_classifier
from .gmail.sync import _recompute_application
from .grouping import (
    counterparty_address,
    extract_company,
    extract_job_ref,
    extract_role,
    extract_role_from_body,
    is_ignored_sender,
    job_group_key,
    normalise,
)
from .models import Application, Email
from .status import Status

logger = logging.getLogger("applytrack.reclassify")


@dataclass(slots=True)
class ReclassifyResult:
    total: int = 0
    changed: int = 0
    skipped_overrides: int = 0
    applications: int = 0


def reclassify_all(session: Session) -> ReclassifyResult:
    classifier = get_classifier()
    result = ReclassifyResult()

    emails = list(session.execute(select(Email)).scalars().all())
    result.total = len(emails)

    # --- Phase 1: re-classify intents (keeping manual overrides) ---
    for email in emails:
        if email.manual_override:
            result.skipped_overrides += 1
            continue
        classification = classifier.classify(
            EmailInput(
                sender=email.sender,
                subject=email.subject,
                body=email.body_snippet,
                direction=email.direction,
            )
        )
        if email.intent != classification.intent.value:
            result.changed += 1
        email.intent = classification.intent.value
        email.confidence = classification.confidence
        email.language = classification.language or email.language
        email.classifier_source = classification.source
        email.reasoning = classification.reasoning
        session.add(email)

    session.flush()

    # --- Phase 2: rebuild applications, one per Gmail thread ---
    result.applications = _rebuild_applications(session, emails)
    return result


def _rebuild_applications(session: Session, emails: list[Email]) -> int:
    # Detach every email, then drop all applications so grouping starts clean.
    for email in emails:
        email.application_id = None
    session.flush()
    session.query(Application).delete()
    session.flush()

    # Group application-relevant mail by Gmail thread. Configured ignore
    # patterns (e.g. recruiting agencies) are demoted to noise and skipped.
    by_thread: dict[str, list[Email]] = defaultdict(list)
    for email in emails:
        if is_ignored_sender(email.sender, email.recipient):
            if not email.manual_override:
                email.intent = "not_application_related"
                email.reasoning = "Ignored sender (configured ignore list)."
                session.add(email)
            continue
        if Intent.from_str(email.effective_intent) is Intent.NOT_APPLICATION_RELATED:
            continue
        by_thread[email.thread_id].append(email)

    # Describe each thread (company, role, job reference) …
    threads = []
    for thread_id, thread_emails in by_thread.items():
        company = _best_company(thread_emails)
        role = _best_role(thread_emails, company)
        threads.append((thread_id, thread_emails, company, role, _best_ref(thread_emails)))

    # … let a thread without a reference borrow one from a sibling thread about
    # the same company + role, so confirmation and rejection end up together.
    ref_by_role = {
        (normalise(c), normalise(r)): ref for _, _, c, r, ref in threads if r and ref
    }

    # … then merge threads that share a job key into one application.
    groups: dict[str, dict] = {}
    for thread_id, thread_emails, company, role, ref in threads:
        ref = ref or (ref_by_role.get((normalise(company), normalise(role))) if role else None)
        key = job_group_key(company, role, ref, thread_id)
        group = groups.setdefault(key, {"company": company, "role": role, "emails": []})
        if role and len(role) > len(group["role"] or ""):
            group["role"] = role
        group["emails"].extend(thread_emails)

    for key, group in groups.items():
        app = Application(
            company=group["company"],
            role=group["role"],
            group_key=key,
            language=group["emails"][0].language or "en",
            current_status=Status.APPLICATION_SENT.value,
        )
        session.add(app)
        session.flush()
        for email in group["emails"]:
            email.application_id = app.id
        session.flush()
        _recompute_application(session, app.id)

    return len(groups)


def _best_company(emails: list[Email]) -> str:
    """Best employer label for a thread; inbound recruiter headers win."""
    # Received mail carries recruiter/company headers; prefer it over our own
    # outbound mail (whose recipient may be a bare ATS address).
    for email in sorted(emails, key=lambda e: e.direction != "received"):
        address = counterparty_address(email.direction, email.sender, email.recipient)
        company = extract_company(address, email.subject)
        if company and company != "Unknown":
            return company
    return "Unknown"


def _best_ref(emails: list[Email]) -> str | None:
    """First job reference number found in the thread (subjects, then text)."""
    for text in [e.subject for e in emails] + [e.body_snippet for e in emails]:
        if ref := extract_job_ref(text):
            return ref
    return None


def _best_role(emails: list[Email], company: str) -> str | None:
    """Most descriptive role across a thread: subjects first, then mail text."""
    candidates = [r for e in emails if (r := extract_role(e.subject, company))]
    if not candidates:
        candidates = [r for e in emails if (r := extract_role_from_body(e.body_snippet, company))]
    return max(candidates, key=len) if candidates else None
