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
