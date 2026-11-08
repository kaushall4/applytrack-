"""Fixes from the November test round: unclear portal mail, filter list,
time-based "no response", second desktop start."""

from __future__ import annotations

import socket
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from applytrack.api.app import create_app
from applytrack.classify.base import EmailInput
from applytrack.classify.heuristic import HeuristicClassifier
from applytrack.desktop import _port_in_use
from applytrack.models import Application, Email

PORTAL = "Citi Human Resources <citi@myworkday.com>"


def _classify(subject: str, body: str, sender: str = PORTAL) -> tuple[str, float]:
    c = HeuristicClassifier().classify(EmailInput(sender=sender, subject=subject, body=body))
    return c.intent.value, c.confidence


def test_citi_confirmation_is_recognised():
    intent, confidence = _classify(
        "Thank you for your interest in Citi!",
        "Thank you for taking the time to apply for the role of Client Experience Associate. "
        "We look forward to finding out more about you.",
    )
    assert intent == "application_received" and confidence >= 0.6


def test_unfamiliar_portal_mail_goes_to_review_not_filter():
    intent, confidence = _classify(
        "An update from Example Bank", "Regarding your application for Analyst: please hold on.")
    assert intent == "application_received"
    assert confidence < 0.6  # lands in "Needs review"


def test_portal_housekeeping_stays_filtered():
    for subject in ("Verify your candidate account", "Kandidatenkonto verifizieren",
                    "Final step to complete your job application", "Candidate registration code"):
        intent, _ = _classify(subject, "Your application account: please confirm the code.")
        assert intent == "not_application_related", subject


def test_ordinary_newsletter_without_application_stays_filtered():
    intent, _ = _classify("Neue Stellen bei der Bank", "Diese Woche neu: 12 offene Stellen.",
                          sender="Jobs <jobs@example.com>")
    assert intent == "not_application_related"


def _client():
    return TestClient(create_app(), client=("127.0.0.1", 5))


def test_filtered_list_hides_own_replies_and_thread_mail(session):
    now = datetime.now(UTC)
    app = Application(company="Acme", group_key="acme", current_status="interview_invite",
                      first_applied_at=now, last_event_at=now)
    session.add(app)
    session.flush()
    session.add_all([
        Email(gmail_id="own", thread_id="t", direction="sent", subject="Re: Interview",
              intent="not_application_related", received_at=now),
        Email(gmail_id="thread", thread_id="t", direction="received", subject="RE: Interview",
              intent="not_application_related", received_at=now, application_id=app.id),
        Email(gmail_id="noise", thread_id="n", direction="received", subject="Newsletter",
              intent="not_application_related", received_at=now),
    ])
    session.commit()
    assert [e["subject"] for e in _client().get("/api/emails/noise").json()] == ["Newsletter"]


def test_no_response_is_up_to_date_without_a_sync(session):
    old = datetime.now(UTC) - timedelta(days=40)
    app = Application(company="Quiet AG", group_key="quiet", current_status="application_received",
                      first_applied_at=old, last_event_at=old)
    session.add(app)
    session.flush()
    session.add(Email(gmail_id="ack", thread_id="q", direction="received", subject="Thanks",
                      intent="application_received", received_at=old, application_id=app.id))
    session.commit()

    stats = _client().get("/api/applications/stats").json()
    assert stats["ghosted"] == 1 and stats["awaiting_response"] == 0


def test_port_in_use_detection():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        s.listen()
        assert _port_in_use(s.getsockname()[1])
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        free = s.getsockname()[1]
    assert not _port_in_use(free)
