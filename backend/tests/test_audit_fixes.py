"""Regression tests for cases found while auditing real mailbox data."""

from __future__ import annotations

from datetime import UTC, datetime

from applytrack.classify.heuristic import classify_heuristic
from applytrack.grouping import (
    company_from_body,
    extract_company,
    extract_role,
    extract_role_from_body,
    forwarded_sender,
)
from applytrack.models import Email
from applytrack.reclassify import _split_by_ref, _split_reapplications

# --- Classification ------------------------------------------------------------

def test_process_description_is_not_a_next_round():
    # Swiss Re confirmation describing the hiring process ("assessment").
    text = ("Thank you for submitting your application. We are currently reviewing your "
            "background. What can you expect from the hiring process after a positive "
            "assessment of your application?")
    assert classify_heuristic(text).intent == "application_received"


def test_networking_newsletter_is_not_an_invitation():
    text = ("It was great to connect with you during the event. We warmly invite you to stay "
            "connected with us on LinkedIn, where we share updates about our programme.")
    assert classify_heuristic(text).intent != "interview_invite"


def test_portal_wording_variants():
    assert classify_heuristic("We're pleased to receive your application for the following "
                              "role: Client Account Manager 341014BR.").intent == "application_received"
    assert classify_heuristic("Gerne bestätige ich Ihnen den Empfang Ihrer Bewerbung.").intent \
        == "application_received"
    assert classify_heuristic("After having reviewed your application, we are sorry to inform you "
                              "that you have not been selected.").intent == "rejection"
    assert classify_heuristic("Da wir über Bewerbungen von Kandidaten verfügen, welche dem "
                              "Anforderungsprofil noch besser entsprechen.").intent == "rejection"


# --- Company -------------------------------------------------------------------

def test_company_from_noreply_display_name():
    assert extract_company("Deutsche_Bank_Workday-do-not-reply <db@myworkday.com>") == "Deutsche Bank"


def test_company_from_body_stops_at_sentence_end():
    text = "Thank you for your interest in working with us at Bank of America. Your application"
    assert company_from_body(text) == "Bank of America"
    assert company_from_body("Thanks for applying for the role at AlTi Tiedemann Global.") \
        == "AlTi Tiedemann Global"


def test_forwarded_original_sender():
    body = "---------- Forwarded message --------- Von: <vontobel@myworkday.com> Date: Di."
    assert forwarded_sender(body) == "<vontobel@myworkday.com>"
    assert extract_company(forwarded_sender(body)) == "Vontobel"


# --- Role ----------------------------------------------------------------------

def test_role_cleanups():
    assert extract_role("Ihre Bewerbung bei der Deutschen Bank", "Deutsche Bank") is None
    assert extract_role("Bewerbung als Assistant Client Advisor & Office Manager 80 bis 100 %") \
        == "Assistant Client Advisor & Office Manager"
    assert extract_role("Ihre Bewerbung Assistant Relationship Manager 80 - 100% for Zurich Desk "
                        "(f/m/d)", "Julius Bär") == "Assistant Relationship Manager for Zurich Desk"
    assert extract_role("Working Student in Private Equity Investment (40-50%, Jan/Feb 2027 for 12 "
                        "months) - 2193 at Schroders", "Schroders") \
        == "Working Student in Private Equity Investment (Jan/Feb for 12 months)"


def test_role_from_body_variants():
    assert extract_role_from_body("Für die Zustellung Ihrer Bewerbung als Client Service Executive "
                                  "und das uns damit entgegengebrachte Interesse danken wir.") \
        == "Client Service Executive"
    assert extract_role_from_body("Thank you for applying to Investor Onboarding Specialist. We") \
        == "Investor Onboarding Specialist"
    assert extract_role_from_body("Re: 26005957 Analyst - Treasury Sales Associate (Open) Thank") \
        == "Analyst - Treasury Sales Associate"


# --- Grouping --------------------------------------------------------------------

def _mail(gid: str, day: str, intent: str, subject: str = "", body: str = "") -> Email:
    return Email(gmail_id=gid, thread_id="t", direction="received", subject=subject,
                 body_snippet=body, intent=intent,
                 received_at=datetime.fromisoformat(day).replace(tzinfo=UTC))


def test_one_gmail_thread_with_confirmations_for_several_jobs_is_split():
    subject = "Your candidate reference number - UBS."
    mails = [
        _mail("a", "2026-08-11T09:00", "application_received", subject, "role: APAC 342263BR."),
        _mail("b", "2026-08-11T09:05", "application_received", subject, "role: Africa 341720BR."),
        _mail("c", "2026-08-11T09:10", "application_received", subject, "role: NZ 342327BR."),
    ]
    parts = _split_by_ref("t", mails)
    assert len(parts) == 3
    assert {p[0] for p in parts} == {"t#342263BR", "t#341720BR", "t#342327BR"}


def test_applying_again_after_a_rejection_is_a_new_application():
    mails = [
        _mail("a", "2026-06-14T09:00", "application_received"),
        _mail("b", "2026-06-22T09:00", "rejection"),
        _mail("c", "2026-08-11T09:00", "application_received"),
        _mail("d", "2026-08-20T09:00", "rejection"),
    ]
    assert [len(s) for s in _split_reapplications(mails)] == [2, 2]


def test_second_rejection_without_new_application_stays_one():
    # LUKB: confirmation, "not this round", final rejection — one application.
    mails = [
        _mail("a", "2026-09-24T09:00", "application_received"),
        _mail("b", "2026-10-08T09:00", "rejection"),
        _mail("c", "2026-10-27T09:00", "rejection"),
    ]
    assert len(_split_reapplications(mails)) == 1
