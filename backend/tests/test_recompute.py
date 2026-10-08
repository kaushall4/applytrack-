"""Regression test: status recompute must tolerate mixed naive/aware datetimes.

SQLite returns naive datetimes on read while freshly-parsed Gmail mail is
tz-aware; recomputing an application's aggregates must not raise when both are
present (which happens on every incremental re-sync).
"""

from __future__ import annotations

from datetime import UTC, datetime

from applytrack.gmail.sync import _recompute_application
from applytrack.models import Application, Email


def test_recompute_handles_mixed_naive_aware_datetimes(session):
    app = Application(company="X", group_key="x", current_status="application_sent")
    session.add(app)
    session.flush()

    naive = Email(
        gmail_id="a", thread_id="t", application_id=app.id, direction="sent",
        received_at=datetime(2026, 5, 1), intent="application_sent",  # naive (as read back from SQLite)
    )
    aware = Email(
        gmail_id="b", thread_id="t", application_id=app.id, direction="received",
        received_at=datetime(2026, 5, 2, tzinfo=UTC), intent="rejection",  # aware
    )
    session.add_all([naive, aware])
    session.flush()

    _recompute_application(session, app.id)  # must not raise

    assert app.current_status == "rejection"
    assert app.email_count == 2
    assert app.first_applied_at is not None
    assert app.last_event_at is not None
