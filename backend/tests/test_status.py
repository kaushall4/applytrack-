"""Tests for the status state machine and ghosting logic."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from applytrack.classify.base import Intent
from applytrack.status import EmailEvent, Status, derive_status, is_ghosted

NOW = datetime(2026, 6, 21, tzinfo=UTC)


def _ev(intent: Intent, days_ago: int, direction: str = "received") -> EmailEvent:
    return EmailEvent(intent=intent, received_at=NOW - timedelta(days=days_ago), direction=direction)


def test_offer_beats_everything():
    events = [
        _ev(Intent.APPLICATION_SENT, 30, "sent"),
        _ev(Intent.INTERVIEW_INVITE, 20),
        _ev(Intent.OFFER, 2),
    ]
    assert derive_status(events, now=NOW) == Status.OFFER


def test_rejection_beats_interview():
    events = [
        _ev(Intent.INTERVIEW_INVITE, 20),
        _ev(Intent.REJECTION, 5),
    ]
    assert derive_status(events, now=NOW) == Status.REJECTION


def test_offer_beats_rejection():
    # Even out of order, terminal precedence (offer > rejection) holds.
    events = [
        _ev(Intent.REJECTION, 10),
        _ev(Intent.OFFER, 12),
    ]
    assert derive_status(events, now=NOW) == Status.OFFER


def test_next_round_beats_interview():
    events = [
        _ev(Intent.INTERVIEW_INVITE, 20),
        _ev(Intent.NEXT_ROUND, 10),
    ]
    assert derive_status(events, now=NOW) == Status.NEXT_ROUND


def test_application_received_only():
    events = [
        _ev(Intent.APPLICATION_SENT, 5, "sent"),
        _ev(Intent.APPLICATION_RECEIVED, 5),
    ]
    assert derive_status(events, now=NOW) == Status.APPLICATION_RECEIVED


def test_not_related_events_ignored():
    events = [
        _ev(Intent.APPLICATION_SENT, 3, "sent"),
        _ev(Intent.NOT_APPLICATION_RELATED, 1),
    ]
    assert derive_status(events, now=NOW) == Status.APPLICATION_SENT


def test_ghosted_after_threshold():
    events = [_ev(Intent.APPLICATION_SENT, 30, "sent")]
    assert is_ghosted(events, ghost_threshold_days=21, now=NOW) is True
    assert derive_status(events, ghost_threshold_days=21, now=NOW) == Status.GHOSTED


def test_not_ghosted_before_threshold():
    events = [_ev(Intent.APPLICATION_SENT, 5, "sent")]
    assert is_ghosted(events, ghost_threshold_days=21, now=NOW) is False
    assert derive_status(events, ghost_threshold_days=21, now=NOW) == Status.APPLICATION_SENT


def test_reply_prevents_ghosting():
    events = [
        _ev(Intent.APPLICATION_SENT, 30, "sent"),
        _ev(Intent.APPLICATION_RECEIVED, 29),
    ]
    assert is_ghosted(events, ghost_threshold_days=21, now=NOW) is False
    # Acknowledged but quiet → stays application_received, not ghosted, because a
    # reply arrived after we applied.
    assert derive_status(events, ghost_threshold_days=21, now=NOW) == Status.APPLICATION_RECEIVED


def test_empty_defaults_to_sent():
    assert derive_status([], now=NOW) == Status.APPLICATION_SENT


def test_naive_datetimes_do_not_raise():
    naive = EmailEvent(
        intent=Intent.APPLICATION_SENT,
        received_at=datetime(2026, 5, 1),  # naive
        direction="sent",
    )
    # Should treat as UTC and not raise.
    assert derive_status([naive], now=NOW) in set(Status)
