"""Per-application status state machine.

Status is derived from *all* classified emails of an application using a fixed
precedence (terminal / strong signals win). A separate ``ghosted`` flag marks
applications that went quiet after the last outbound application email.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from .classify.base import Intent


class Status(str, enum.Enum):
    """Derived status shown on the dashboard."""

    APPLICATION_SENT = "application_sent"
    APPLICATION_RECEIVED = "application_received"
    INFO_REQUEST = "info_request"
    INTERVIEW_INVITE = "interview_invite"
    NEXT_ROUND = "next_round"
    REJECTION = "rejection"
    OFFER = "offer"
    GHOSTED = "ghosted"


# Precedence: higher number wins. Mirrors the spec's ordering
# offer > rejection > next_round > interview_invite > info_request
# > application_received > application_sent.
_INTENT_PRECEDENCE: dict[Intent, int] = {
    Intent.APPLICATION_SENT: 1,
    Intent.APPLICATION_RECEIVED: 2,
    Intent.INFO_REQUEST: 3,
    Intent.INTERVIEW_INVITE: 4,
    Intent.NEXT_ROUND: 5,
    Intent.REJECTION: 6,
    Intent.OFFER: 7,
}

# Intent → resulting Status (1:1 for the intents that map to a status).
_INTENT_TO_STATUS: dict[Intent, Status] = {
    Intent.APPLICATION_SENT: Status.APPLICATION_SENT,
    Intent.APPLICATION_RECEIVED: Status.APPLICATION_RECEIVED,
    Intent.INFO_REQUEST: Status.INFO_REQUEST,
    Intent.INTERVIEW_INVITE: Status.INTERVIEW_INVITE,
    Intent.NEXT_ROUND: Status.NEXT_ROUND,
    Intent.REJECTION: Status.REJECTION,
    Intent.OFFER: Status.OFFER,
}


@dataclass(slots=True)
class EmailEvent:
    """Minimal email view the state machine reasons over."""

    intent: Intent
    received_at: datetime
    direction: str  # "sent" or "received"


def _as_aware(dt: datetime) -> datetime:
    """Treat naive datetimes as UTC so comparisons never raise."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def derive_status(
    events: list[EmailEvent],
    *,
    ghost_threshold_days: int = 21,
    now: datetime | None = None,
) -> Status:
    """Compute the current status for an application from its email events.

    ``not_application_related`` events are ignored. If no application-relevant
    event exists, the status defaults to ``application_sent`` (the application
    table only ever holds threads we believe are applications).
    """
    now = _as_aware(now or datetime.now(UTC))

    relevant = [e for e in events if e.intent in _INTENT_PRECEDENCE]
    if not relevant:
        return Status.APPLICATION_SENT

    winner = max(relevant, key=lambda e: _INTENT_PRECEDENCE[e.intent])
    status = _INTENT_TO_STATUS[winner.intent]

    # Ghosting only applies while we are still waiting on the other side: the
    # strongest signal is our own application and nothing came back since.
    if status in (Status.APPLICATION_SENT, Status.APPLICATION_RECEIVED):
        if is_ghosted(events, ghost_threshold_days=ghost_threshold_days, now=now):
            return Status.GHOSTED

    return status


def is_ghosted(
    events: list[EmailEvent],
    *,
    ghost_threshold_days: int = 21,
    now: datetime | None = None,
) -> bool:
    """True when the last meaningful event is an unanswered outbound application.

    "Unanswered" means no inbound email arrived after our last
    ``application_sent``, and more than ``ghost_threshold_days`` have passed.
    """
    now = _as_aware(now or datetime.now(UTC))

    sent_applications = [
        e for e in events if e.intent == Intent.APPLICATION_SENT and e.direction == "sent"
    ]
    if not sent_applications:
        return False

    last_sent = max(sent_applications, key=lambda e: _as_aware(e.received_at))
    last_sent_at = _as_aware(last_sent.received_at)

    # Any inbound reply after we applied means we were not ghosted.
    replied = any(
        e.direction == "received" and _as_aware(e.received_at) > last_sent_at for e in events
    )
    if replied:
        return False

    return now - last_sent_at > timedelta(days=ghost_threshold_days)
