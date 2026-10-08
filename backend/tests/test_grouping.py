"""Tests for employer-name extraction and thread-based grouping keys."""

import pytest

from applytrack.grouping import (
    extract_company,
    extract_job_ref,
    extract_role,
    extract_role_from_body,
    job_group_key,
    thread_group_key,
)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Your application for Client Account Manager UHNW Poland (335649BR)", "335649BR"),
        ("Your Application for Client Account Manager(338637BR)", "338637BR"),
        ("Your job application status (Job number: 210722077)", "210722077"),
        ("for the role of Client Account Manager WM - 340891BR. Please", "340891BR"),
        ("Thank you for your application", None),
    ],
)
def test_extract_job_ref(text, expected):
    assert extract_job_ref(text) == expected


def test_job_group_key_prefers_ref_then_role_then_thread():
    assert job_group_key("UBS", "CAM", "335649BR", "t1") == job_group_key("UBS", None, "335649BR", "t2")
    assert job_group_key("UBS", "CAM", None, "t1") == job_group_key("UBS", "CAM", None, "t2")
    assert job_group_key("UBS", None, None, "t1") != job_group_key("UBS", None, None, "t2")
    assert job_group_key("Unknown", "CAM", None, "t1") == thread_group_key("t1")


def test_role_from_body_du_form():
    body = (
        "Hallo Alex Vielen Dank für deine Bewerbung als Assistent:in Private Banking "
        "(m/w/d). Wir freuen uns sehr über dein Interesse."
    )
    assert extract_role_from_body(body, "LUKB") == "Assistent:in Private Banking"


def test_role_from_body_english_invitation():
    body = (
        "We'd like to invite you for an interview for the role of Client Account Manager "
        "WM – UK International UHNW - 340891BR. Please schedule your interview."
    )
    assert extract_role_from_body(body, "UBS") == "Client Account Manager WM – UK International UHNW"


def test_role_cleans_open_gender_tag_and_balances_paren():
    subject = "Your application for Financial Analyst (12 months Working Student - m/f/x/d;"
    assert extract_role(subject, "Swiss Re") == "Financial Analyst (12 months Working Student)"


def test_role_from_interview_invitation_subject():
    subject = "We'd like to meet - interview invitation for Client Account Manager WM"
    assert extract_role(subject, "UBS") == "Client Account Manager WM"


@pytest.mark.parametrize(
    "header, expected",
    [
        # A real company domain wins over systems, departments and people.
        ("UBS Careers <donotreply@ubs.com>", "UBS"),
        ("SH-UBS-Interview-Scheduling <sh-ubs-interview-scheduling@ubs.com>", "UBS"),
        ("MUSTER Anna <anna.muster@ubp.ch>", "UBP"),
        ('"Beispiel, Lea" <lea.beispiel@ubs.com>', "UBS"),
        ("Personalabteilung Luzerner Kantonalbank <jobs@lukb.ch>", "LUKB"),
        ("HR Connect <noreply.hrconnect@juliusbaer.com>", "Julius Bär"),
        ('"personal@maerki-baumann.ch" <personal@maerki-baumann.ch>', "Maerki Baumann"),
        ("UBP Recruiting <ubprecruiting@hcm.ubp.com>", "UBP"),
        ("DZ PRIVATBANK Recruiting <recruiting@dz-privatbank.com>", "DZ PRIVATBANK"),
        ("Swiss Re MyHR System <donotreply_careers@swissreservices.com>", "Swiss Re"),
        ("bewerbermanagement@sgkb.ch", "SGKB"),
        # ATS platforms: display name…
        ('"Workday - Rothschild & Co" <RothschildandCo@myworkday.com>', "Rothschild & Co"),
        ('"JPMorgan Chase & Co. Human Resources" <x@workflow.mail.us2.cloud.oracle.com>',
         "JPMorgan Chase & Co"),
        ("UBS <donotreply@trm.brassring.com>", "UBS"),
        # …or the local part / subdomain.
        ("pimco@myworkday.com", "PIMCO"),
        ("swisslife@myworkday.com", "Swiss Life"),
        ("lgtcp@myworkday.com", "LGT Capital Partners"),
        ("noreply@zkb.refline.ch", "ZKB"),
    ],
)
def test_extract_company(header, expected):
    assert extract_company(header) == expected


def test_company_from_subject_on_opaque_ats_sender():
    header = "ekbq.fa.sender@workflow.email.eu-frankfurt-1.ocs.oraclecloud.com"
    subject = "Relationship Management Assistant - 1172 at Schroders"
    assert extract_company(header, subject) == "Schroders"


def test_generic_workday_sender_is_unknown():
    assert extract_company("Global HR Workday <ghr@myworkday.com>") is None


def test_forwarded_freemail_personal_name_is_unknown():
    # A forwarded mail from the applicant's own free-mail address is not a company.
    assert extract_company("Alex Muster <alex.muster@gmail.com>") is None


def test_thread_group_key_is_per_thread():
    assert thread_group_key("abc") == thread_group_key("abc")
    assert thread_group_key("abc") != thread_group_key("def")


@pytest.mark.parametrize(
    "subject, company, expected",
    [
        ("Your application for Client Account Manager (WM Eastern Europe) (338637BR)", "UBS",
         "Client Account Manager (WM Eastern Europe)"),
        ("Ihre Bewerbung bei UBS Associate Client Relationship Manager(335951BR)", "UBS",
         "Associate Client Relationship Manager"),
        ("Deine Bewerbung als Assistent*in Private Banking 80 – 100%", "SGKB",
         "Assistent*in Private Banking"),
        ("UBP – WM Assistant - Greece Team (100%) - Application Confirmation", "UBP",
         "WM Assistant - Greece Team"),
        ("Relationship Management Assistant - 1172 at Schroders", "EKBQ",
         "Relationship Management Assistant"),
        ("Ihre Bewerbung | Assistenz VR-Private Banking Schweiz, 80-100% (m/w/d)", "DZ PRIVATBANK",
         "Assistenz VR-Private Banking Schweiz"),
    ],
)
def test_extract_role(subject, company, expected):
    assert extract_role(subject, company) == expected


@pytest.mark.parametrize(
    "subject",
    [
        "Thank you for your application",
        "Confirmation of your online application",
        "Ihre Bewerber-Referenznummer - UBS.",
        "Your job application status (Job number: 210722077)",
        "Muster_Alex_CV_2026",
        "Re: UBS Interview",
        "",
    ],
)
def test_extract_role_returns_none_for_noise(subject):
    assert extract_role(subject, "UBS") is None
