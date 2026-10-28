"""Rebuilding applications: one per job, even across Gmail threads."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from applytrack.models import Application, Email
from applytrack.reclassify import reclassify_all

UBS = "UBS Careers <donotreply@ubs.com>"
ME = "Alex <applicant@example.com>"


def _mail(gmail_id, thread_id, subject, body, day):
    return Email(
        gmail_id=gmail_id,
        thread_id=thread_id,
        direction="received",
        sender=UBS,
        recipient=ME,
        subject=subject,
        body_snippet=body,
        received_at=datetime(2026, 5, day, tzinfo=UTC),
    )


def test_confirmation_and_rejection_in_separate_threads_merge(session):
    session.add_all([
        _mail("a", "t1", "Your application for Client Account Manager UHNW Poland (335649BR)",
              "Thank you for your application. We will be in touch.", 1),
        _mail("b", "t2", "Your Application for Client Account Manager UHNW Poland(335649BR)",
              "Unfortunately we have decided to move forward with other candidates.", 9),
    ])
    session.commit()

    reclassify_all(session)
    session.commit()

    apps = session.execute(select(Application)).scalars().all()
    assert len(apps) == 1
    assert apps[0].current_status == "rejection"
    assert apps[0].email_count == 2


def test_different_jobs_at_same_company_stay_separate(session):
    session.add_all([
        _mail("a", "t1", "Your application for Client Account Manager UHNW Poland (335649BR)",
              "Thank you for your application.", 1),
        _mail("b", "t2", "Your application for Associate Client Relationship Manager (335951BR)",
              "Thank you for your application.", 2),
    ])
    session.commit()

    reclassify_all(session)
    session.commit()

    apps = session.execute(select(Application)).scalars().all()
    assert len(apps) == 2
    assert {a.company for a in apps} == {"UBS"}


# --- Double counting across threads (patterns from a real mailbox) -------------

ZKB = "noreply@bank.refline.ch"
UBP = "UBP Recruiting <recruiting@hcm.ubp.com>"
RECRUITER = "MUSTER Anna <anna.muster@ubp.ch>"


def _m(gid, thread, subject, body, month, day, sender, direction="received"):
    me_sender, me_recipient = (ME, sender) if direction == "sent" else (sender, ME)
    return Email(
        gmail_id=gid, thread_id=thread, direction=direction,
        sender=me_sender, recipient=me_recipient, subject=subject, body_snippet=body,
        received_at=datetime(2026, month, day, tzinfo=UTC),
    )


def _apps(session):
    reclassify_all(session)
    session.commit()
    return session.execute(select(Application)).scalars().all()


def test_untitled_confirmation_joins_the_following_rejection(session):
    # The confirmation names no job; the rejection a few weeks later does.
    session.add_all([
        _m("a", "t1", "Wir haben die Bewerbung erhalten!",
           "Vielen Dank für deine Bewerbung. Wir haben die Bewerbung erhalten.", 5, 14, ZKB),
        _m("b", "t2", "Deine Bewerbung als Client Account Manager Financial Institutions",
           "Leider müssen wir dir mitteilen, dass wir uns anders entschieden haben.", 6, 11, ZKB),
    ])
    session.commit()

    apps = _apps(session)
    assert len(apps) == 1
    assert apps[0].current_status == "rejection"
    assert apps[0].email_count == 2


def test_untitled_confirmation_without_later_job_stays_separate(session):
    session.add_all([
        _m("a", "t1", "Deine Bewerbung als Assistent:in Private Banking",
           "Leider müssen wir dir absagen.", 3, 1, ZKB),
        _m("b", "t2", "Wir haben die Bewerbung erhalten!",
           "Vielen Dank für deine Bewerbung. Wir haben die Bewerbung erhalten.", 8, 11, ZKB),
    ])
    session.commit()

    apps = _apps(session)
    assert len(apps) == 2
    # The lone confirmation is months old with nothing since → no response.
    assert {a.current_status for a in apps} == {"rejection", "ghosted"}


def test_interview_process_across_threads_is_one_application(session):
    session.add_all([
        # Confirmation with the job title …
        _m("a", "t1", "UBP – Wealth Management Assistant - Eastern Europe Team (Zurich) - "
           "Application Confirmation", "Thank you for your application.", 8, 7, UBP),
        # … invitation in its own thread, title only in the text …
        _m("b", "t2", "UBP Interview", "Vielen Dank für Ihre Bewerbung für die Position "
           "Wealth Management Assistant – Eastern Europe. Gerne laden wir Sie zu einem "
           "persönlichen Gespräch ein.", 8, 13, RECRUITER),
        _m("c", "t2", "Re: UBP Interview", "Vielen Dank, der Termin passt.", 8, 13, RECRUITER,
           direction="sent"),
        # … recruiter follow-up without any title …
        _m("d", "t3", "RE: UBP", "Gerne möchten wir dich zu einem weiteren Interview einladen.",
           9, 10, RECRUITER),
        # … and the final rejection, again with the title.
        _m("e", "t4", "UBP - Wealth Management Assistant - Eastern Europe Team (Zurich) - "
           "Follow-up on Your Interview",
           "After careful consideration we regret to inform you that we will not be moving "
           "forward.", 9, 21, UBP),
    ])
    session.commit()

    apps = _apps(session)
    assert len(apps) == 1
    app = apps[0]
    assert app.current_status == "rejection"
    assert app.email_count == 5  # your reply is in the timeline …
    intents = {e.effective_intent for e in app.emails}
    assert "application_sent" not in intents  # … but never counted as an application


def test_different_job_at_same_company_is_not_swallowed(session):
    session.add_all([
        _m("a", "t1", "UBP – Wealth Management Assistant - Eastern Europe Team (Zurich) - "
           "Application Confirmation", "Thank you for your application.", 8, 7, UBP),
        _m("b", "t2", "UBP – SPECULATIVE APPLICATION - Wealth Management Assistant Zurich "
           "(80-100%) - Application Confirmation", "Thank you for your application.", 10, 1, UBP),
    ])
    session.commit()

    assert len(_apps(session)) == 2


def test_untitled_confirmation_and_untitled_rejection_merge(session):
    workday = "PIMCO Recruiting <pimco@myworkday.com>"
    session.add_all([
        _m("a", "t1", "Thank you for applying", "Thank you for applying to PIMCO.", 5, 20, workday),
        _m("b", "t2", "Your application with PIMCO",
           "After careful consideration, we have determined that we do not have the best fit "
           "at this time.", 6, 19, workday),
    ])
    session.commit()

    apps = _apps(session)
    assert len(apps) == 1
    assert apps[0].current_status == "rejection"


def test_applied_date_ignores_your_later_reply(session):
    session.add_all([
        _m("a", "t1", "Your Application for Client Account Manager WM(342286BR)",
           "Thank you for your application.", 9, 24, UBS),
        _m("b", "t1", "Re: Your Application for Client Account Manager WM(342286BR)",
           "Thanks, looking forward to it.", 9, 28, UBS, direction="sent"),
    ])
    session.commit()

    (app,) = _apps(session)
    assert app.first_applied_at.date().isoformat() == "2026-09-24"


def test_forwarded_and_replied_mails_create_no_application(session):
    session.add_all([
        _m("a", "t1", "Fwd: Get ready for your interview", "------- Weitergeleitete Nachricht",
           8, 4, "me@other.example", direction="sent"),
        _m("b", "t2", "Re: Besprechung", "Danke, passt.", 8, 5, RECRUITER, direction="sent"),
    ])
    session.commit()

    assert _apps(session) == []


SYGNUM_PORTAL = "Sygnum People Portal <peopleportal@sygnum.com>"
SYGNUM_HR = "Sergio Example <sergio.example@sygnum.com>"


def test_interview_thread_joins_application_with_longer_title(session):
    # Portal confirmation with the full title, then a personal invitation that
    # only says "the Assistant Relationship Manager opportunity".
    session.add_all([
        _m("a", "t1", "Your Application - Assistant Relationship Manager, Private Banking (80-100%)",
           "Thank you for your application to the Assistant Relationship Manager, Private "
           "Banking (80-100%) position at Sygnum.", 10, 1, SYGNUM_PORTAL),
        _m("b", "t2", "First-round interview – Assistant Relationship Manager",
           "Thank you for your application for the Assistant Relationship Manager opportunity "
           "with us. We would be very pleased to get to know you in a first-round interview.",
           10, 15, SYGNUM_HR),
        _m("c", "t2", "RE: First-round interview – Assistant Relationship Manager",
           "Besten Dank fuer das angenehme Gespraech. Wir wuenschen dir weiterhin viel Erfolg.",
           10, 21, SYGNUM_HR),
    ])
    session.commit()

    apps = _apps(session)
    assert len(apps) == 1
    assert apps[0].role.startswith("Assistant Relationship Manager, Private Banking")
    assert apps[0].current_status == "rejection"


def test_two_confirmed_applications_are_not_merged_by_loose_titles(session):
    # Two separate applications, each with its own confirmation: a generic
    # title must not swallow the specific one.
    session.add_all([
        _m("a", "t1", "UBP – Wealth Management Assistant - Eastern Europe Team (Zurich) - "
           "Application Confirmation", "Thank you for your application.", 8, 7, UBP),
        _m("b", "t2", "UBP – SPECULATIVE APPLICATION - Wealth Management Assistant Zurich - "
           "Application Confirmation", "Thank you for your application.", 10, 1, UBP),
    ])
    session.commit()
    assert len(_apps(session)) == 2
