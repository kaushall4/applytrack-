"""Re-classify stored emails and rebuild applications — no Gmail sync.

Two phases, both running only on the local database:

1. **Re-classify** every email's intent/confidence/language with the current
   logic. Manual overrides are never touched.
2. **Rebuild applications** (:func:`regroup_all`) so that every job is counted
   exactly once, even when its mails are spread over several Gmail threads:

   * threads with the same job reference number (``335649BR``) are one job;
   * threads whose job titles match (:func:`grouping.roles_match`) are one job;
   * a thread with neither — e.g. "Wir haben die Bewerbung erhalten!" or a
     recruiter's "RE: UBP" — joins the company's job it belongs to in time:
     an acknowledgment joins the job whose next mail follows within 60 days
     (confirmation → later rejection); an interview/process thread joins the
     job applied for most recently before it (within 120 days).

   Your own replies and forwards inside a job's thread are kept in its timeline
   but never count as a separate application.

Only the stored ``body_snippet`` is available (full bodies are never persisted),
so signals beyond the snippet length cannot be seen.
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

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
    roles_match,
    thread_group_key,
)
from .models import Application, Email
from .status import Status, _as_aware

logger = logging.getLogger("applytrack.reclassify")

_ACK_INTENTS = {Intent.APPLICATION_RECEIVED, Intent.APPLICATION_SENT}
_ACK_WINDOW = timedelta(days=60)  # confirmation → the job's next mail
_PROCESS_WINDOW = timedelta(days=120)  # application → interview/recruiter thread


@dataclass(slots=True)
class ReclassifyResult:
    total: int = 0
    changed: int = 0
    skipped_overrides: int = 0
    applications: int = 0


@dataclass
class _Thread:
    thread_id: str
    emails: list[Email]  # every mail of the thread (incl. your replies)
    company: str
    role: str | None
    role_from_subject: bool  # subject titles are cleaner than ones read from text
    ref: str | None
    first: datetime
    intents: set[Intent]

    @property
    def identified(self) -> bool:
        return bool(self.role or self.ref)

    @property
    def ack_only(self) -> bool:
        return self.intents <= _ACK_INTENTS


@dataclass
class _Job:
    threads: list[_Thread] = field(default_factory=list)

    @property
    def company(self) -> str:
        named = [t.company for t in self.threads if t.company != "Unknown"]
        return Counter(named).most_common(1)[0][0] if named else "Unknown"

    @property
    def role(self) -> str | None:
        from_subject = [t.role for t in self.threads if t.role and t.role_from_subject]
        roles = from_subject or [t.role for t in self.threads if t.role]
        return max(roles, key=len) if roles else None

    @property
    def refs(self) -> set[str]:
        return {t.ref for t in self.threads if t.ref}

    @property
    def identified(self) -> bool:
        return any(t.identified for t in self.threads)

    @property
    def first(self) -> datetime:
        return min(t.first for t in self.threads)


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

    # --- Phase 2: one application per job ---
    result.applications = regroup_all(session, emails)
    return result


def regroup_all(session: Session, emails: list[Email] | None = None) -> int:
    """Rebuild all applications from the stored emails. Returns their count."""
    if emails is None:
        emails = list(session.execute(select(Email)).scalars().all())

    # Detach every email, then drop all applications so grouping starts clean.
    for email in emails:
        email.application_id = None
    session.flush()
    session.query(Application).delete()
    session.flush()

    threads = _describe_threads(session, emails)
    jobs = _merge_into_jobs(threads)

    used_keys: set[str] = set()
    for job in jobs:
        key = job_group_key(job.company, job.role, min(job.refs, default=None),
                            job.threads[0].thread_id)
        if key in used_keys:  # two distinct jobs with an identical title
            key = thread_group_key(job.threads[0].thread_id)
        used_keys.add(key)

        all_mail = [e for t in job.threads for e in t.emails]
        app = Application(
            company=job.company,
            role=job.role,
            group_key=key,
            language=all_mail[0].language or "en",
            current_status=Status.APPLICATION_SENT.value,
        )
        session.add(app)
        session.flush()
        for email in all_mail:
            email.application_id = app.id
        session.flush()
        _recompute_application(session, app.id)

    return len(jobs)


def _describe_threads(session: Session, emails: list[Email]) -> list[_Thread]:
    """Group mail by Gmail thread; keep threads with at least one relevant mail."""
    by_thread: dict[str, list[Email]] = defaultdict(list)
    for email in emails:
        if is_ignored_sender(email.sender, email.recipient):
            # Configured ignore patterns (e.g. recruiting agencies) are noise.
            if not email.manual_override:
                email.intent = "not_application_related"
                email.reasoning = "Ignored sender (configured ignore list)."
                session.add(email)
            continue
        by_thread[email.thread_id].append(email)

    threads: list[_Thread] = []
    for thread_id, thread_emails in by_thread.items():
        relevant = [
            e for e in thread_emails
            if Intent.from_str(e.effective_intent) is not Intent.NOT_APPLICATION_RELATED
        ]
        if not relevant:
            continue  # pure noise, or only your own replies/forwards
        company = _best_company(relevant)
        role, role_from_subject = _best_role(relevant, company)
        threads.append(
            _Thread(
                thread_id=thread_id,
                emails=thread_emails,
                company=company,
                role=role,
                role_from_subject=role_from_subject,
                ref=_best_ref(relevant),
                first=min(_as_aware(e.received_at) for e in relevant),
                intents={Intent.from_str(e.effective_intent) for e in relevant},
            )
        )
    return sorted(threads, key=lambda t: t.first)


def _merge_into_jobs(threads: list[_Thread]) -> list[_Job]:
    jobs: list[_Job] = []

    # 1) Identified threads: same reference number, or matching job title.
    for thread in (t for t in threads if t.identified):
        match = _find_identified_job(jobs, thread)
        if match is None:
            jobs.append(_Job(threads=[thread]))
        else:
            match.threads.append(thread)

    # 2) Threads without reference or title join a job of the same company.
    loose: list[_Job] = []
    for thread in (t for t in threads if not t.identified):
        target = _job_for_unidentified(jobs, thread)
        if target is None:
            loose.append(_Job(threads=[thread]))
        else:
            target.threads.append(thread)

    # 3) Still-loose, untitled threads of one company: a bare confirmation joins
    #    the next untitled reply (e.g. a rejection) that follows within 60 days.
    merged: set[int] = set()
    for ack in loose:
        t = ack.threads[0]
        if not t.ack_only or t.company == "Unknown":
            continue
        followers = [
            j for j in loose
            if j is not ack and id(j) not in merged and j.company == t.company
            and not all(x.ack_only for x in j.threads)
            and t.first < j.first <= t.first + _ACK_WINDOW
        ]
        if followers:
            min(followers, key=lambda j: j.first).threads.extend(ack.threads)
            merged.add(id(ack))

    return jobs + [j for j in loose if id(j) not in merged]


def _find_identified_job(jobs: list[_Job], thread: _Thread) -> _Job | None:
    same_company = [j for j in jobs if j.identified and j.company == thread.company
                    and thread.company != "Unknown"]
    if thread.ref:
        for job in same_company:
            if thread.ref in job.refs:
                return job
    if not thread.role:
        return None
    # Title match — never across two different reference numbers, and only if
    # exactly one job matches (an ambiguous title merges nothing).
    candidates = [
        j for j in same_company
        if roles_match(thread.role, j.role)
        and not (thread.ref and j.refs and thread.ref not in j.refs)
    ]
    return candidates[0] if len(candidates) == 1 else None


def _job_for_unidentified(jobs: list[_Job], thread: _Thread) -> _Job | None:
    if thread.company == "Unknown":
        return None
    company_jobs = [j for j in jobs if j.identified and j.company == thread.company]
    if not company_jobs:
        return None

    if thread.intents <= _ACK_INTENTS:
        # A bare confirmation belongs to the job whose next mail follows soon.
        after = [
            (min(t.first for t in j.threads if t.first > thread.first) - thread.first, j)
            for j in company_jobs
            if any(thread.first < t.first <= thread.first + _ACK_WINDOW for t in j.threads)
        ]
        return min(after, key=lambda pair: pair[0])[1] if after else None

    # Interview / recruiter thread → the job applied for most recently before it.
    before = [j for j in company_jobs if thread.first - _PROCESS_WINDOW <= j.first <= thread.first]
    if before:
        return max(before, key=lambda j: j.first)
    after = [j for j in company_jobs if thread.first < j.first <= thread.first + _ACK_WINDOW]
    return min(after, key=lambda j: j.first) if after else None


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


def _best_role(emails: list[Email], company: str) -> tuple[str | None, bool]:
    """Most descriptive role of a thread, and whether it came from a subject."""
    candidates = [r for e in emails if (r := extract_role(e.subject, company))]
    if candidates:
        return max(candidates, key=len), True
    candidates = [r for e in emails if (r := extract_role_from_body(e.body_snippet, company))]
    return (max(candidates, key=len) if candidates else None), False
