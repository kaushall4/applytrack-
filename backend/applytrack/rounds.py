"""Recognise later interview rounds from the order of mails within one job.

Recruiters often phrase a second-round invitation exactly like the first one
("We'd like to meet you – interview availability"), so keywords alone can't
tell them apart. Within one application (= one job: same reference number or
role), the *sequence* can: a fresh invitation that arrives after an earlier
interview round is the next round.

Mails that only continue the current round don't start a new one: replies in
the thread, scheduling confirmations and reminders ("Your upcoming interview",
"Get ready for your interview"), and anything within a few days of the round's
first invitation.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

from .classify.fragments import fold
from .models import Email

# A new round's invitation comes at least this long after the previous round began.
ROUND_GAP = timedelta(days=5)

_INTERVIEW_STAGE = {"interview_invite", "next_round"}
_REPLY_RE = re.compile(r"^\s*(?:re|aw|antw|wg|fw|fwd)\s*:", re.IGNORECASE)
# Subjects that follow up on an already scheduled interview.
_FOLLOW_UP_RE = re.compile(
    r"upcoming|get ready|reminder|erinnerung|confirm|bestaetig|reschedul|verschieb|"
    r"verschoben|absage des termins|cancel|calendar|kalender|anfahrt|wegbeschreibung|"
    r"directions|first[- ]round|erste runde|erstes gespraech"
)

NEXT_ROUND_REASON = "New invitation for the same job after an earlier interview round → next round."


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _starts_new_round(email: Email, round_start: datetime, round_threads: set[str]) -> bool:
    subject = fold(email.subject or "")
    return (
        email.thread_id not in round_threads
        and _aware(email.received_at) - round_start >= ROUND_GAP
        and not _REPLY_RE.match(subject)
        and not _FOLLOW_UP_RE.search(subject)
    )


def mark_interview_rounds(emails: Iterable[Email]) -> int:
    """Re-label later-round invitations of one job as ``next_round``.

    ``emails`` are all mails of a single application. Manual overrides are left
    alone. Returns how many mails were re-labelled.
    """
    stage = sorted(
        (
            e
            for e in emails
            if e.direction == "received" and e.effective_intent in _INTERVIEW_STAGE
        ),
        key=lambda e: _aware(e.received_at),
    )
    changed = 0
    round_start: datetime | None = None
    round_threads: set[str] = set()
    for email in stage:
        if round_start is None:
            round_start, round_threads = _aware(email.received_at), {email.thread_id}
            continue
        if _starts_new_round(email, round_start, round_threads):
            round_start, round_threads = _aware(email.received_at), {email.thread_id}
            if email.intent == "interview_invite" and not email.manual_override:
                email.intent = "next_round"
                email.reasoning = NEXT_ROUND_REASON
                changed += 1
        else:
            round_threads.add(email.thread_id)
    return changed
