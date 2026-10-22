"""Later interview rounds recognised from the sequence of mails within one job."""

from __future__ import annotations

from datetime import UTC, datetime

from applytrack.models import Email
from applytrack.rounds import mark_interview_rounds


def _mail(day: str, subject: str, intent: str, thread: str, direction: str = "received",
          override: str | None = None) -> Email:
    return Email(
        gmail_id=f"{thread}-{day}-{subject[:8]}",
        thread_id=thread,
        direction=direction,
        subject=subject,
        intent=intent,
        manual_override=override,
        received_at=datetime.fromisoformat(day).replace(tzinfo=UTC),
    )


def _intents(mails: list[Email]) -> list[str]:
    return [m.intent for m in mails]


def test_second_invitation_for_same_job_is_next_round():
    # Real shape of the UBS Hong Kong Desk process (343828BR).
    mails = [
        _mail("2026-09-24T08:00", "Your Application for Client Account Manager (343828BR)",
              "application_received", "a"),
        _mail("2026-10-08T06:00", "We'd like to meet you - In-Person Interview availability",
              "interview_invite", "b"),
        _mail("2026-10-08T12:00", "Re: We'd like to meet you", "not_application_related", "b",
              direction="sent"),
        _mail("2026-10-09T06:00", "Your upcoming in-person interview - 343828BR",
              "interview_invite", "c"),
        _mail("2026-10-19T10:00", "We'd like to meet you - interview availability for 343828BR",
              "interview_invite", "d"),
    ]
    assert mark_interview_rounds(mails) == 1
    assert _intents(mails)[-1] == "next_round"
    assert _intents(mails)[3] == "interview_invite"  # confirmation stays in round 1


def test_confirmation_and_reminder_stay_in_the_same_round():
    # UBS UK: invitation, then "Get ready for your interview" the next day.
    mails = [
        _mail("2026-08-03T14:00", "We'd like to meet - interview invitation", "interview_invite", "a"),
        _mail("2026-08-04T06:00", "Get ready for your interview", "interview_invite", "b"),
        _mail("2026-08-27T16:00", "Your application for Client Account Manager", "rejection", "c"),
    ]
    assert mark_interview_rounds(mails) == 0


def test_replies_and_late_reminders_do_not_start_a_round():
    mails = [
        _mail("2026-08-13T08:00", "UBP Interview", "interview_invite", "a"),
        _mail("2026-08-20T11:00", "RE: UBP Interview", "interview_invite", "a"),
        _mail("2026-08-25T09:00", "Reminder: your interview tomorrow", "interview_invite", "b"),
        _mail("2026-08-26T09:00", "AW: Termin", "interview_invite", "c"),
    ]
    assert mark_interview_rounds(mails) == 0


def test_same_day_threads_are_one_round():
    # Sygnum: invitation and a second thread for the same slot on the same day.
    mails = [
        _mail("2026-10-15T06:30", "First-round interview", "interview_invite", "a"),
        _mail("2026-10-15T09:39", "First-round interview (Kaushall)", "interview_invite", "b"),
    ]
    assert mark_interview_rounds(mails) == 0


def test_third_round_and_keyword_rounds_count_as_round_starts():
    mails = [
        _mail("2026-08-13T08:00", "Interview", "interview_invite", "a"),
        _mail("2026-09-09T14:00", "UBP", "next_round", "b"),  # keyword already said so
        _mail("2026-09-10T16:00", "RE: UBP", "interview_invite", "b"),  # same round
        _mail("2026-09-30T09:00", "Einladung zum Gespräch", "interview_invite", "c"),
    ]
    assert mark_interview_rounds(mails) == 1
    assert _intents(mails) == ["interview_invite", "next_round", "interview_invite", "next_round"]


def test_manual_override_is_respected():
    mails = [
        _mail("2026-10-01T08:00", "Interview invitation", "interview_invite", "a"),
        _mail("2026-10-20T08:00", "Interview invitation", "interview_invite", "b",
              override="interview_invite"),
    ]
    assert mark_interview_rounds(mails) == 0
    assert mails[1].intent == "interview_invite"
