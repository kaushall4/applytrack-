"""Fragment-heuristic classification + precedence tests."""

import pytest

from applytrack.classify.base import EmailInput
from applytrack.classify.heuristic import HeuristicClassifier, classify_heuristic

from .fixtures.classification_fixtures import FIXTURES


@pytest.mark.parametrize("text,expected,lang", FIXTURES)
def test_heuristic_classification(text, expected, lang):
    assert classify_heuristic(text).intent == expected


def test_compliment_sandwich_is_rejection():
    text = (
        "Vielen Dank fuer Ihre Bewerbung. Ihr Profil hat uns sehr beeindruckt und Ihre "
        "Qualifikationen sind hervorragend. Dennoch muessen wir Ihnen leider mitteilen, "
        "dass Ihre Bewerbung diesmal nicht erfolgreich war."
    )
    assert classify_heuristic(text).intent == "rejection"


def test_pure_acknowledgment_is_received():
    text = (
        "Vielen Dank fuer Ihre Bewerbung. Wir haben Ihre Unterlagen erhalten und melden "
        "uns in Kuerze bei Ihnen."
    )
    assert classify_heuristic(text).intent == "application_received"


def test_umlaut_spelling_equivalence():
    # Real umlauts must match the same fragment as the ae/oe/ue spelling.
    umlaut = "Leider können wir Ihre Bewerbung nicht weiter berücksichtigen."
    folded = "Leider koennen wir Ihre Bewerbung nicht weiter beruecksichtigen."
    assert classify_heuristic(umlaut).intent == "rejection"
    assert classify_heuristic(folded).intent == "rejection"


def test_precedence_rejection_over_received():
    # Acknowledgment phrasing AND a rejection signal → rejection wins.
    text = "Danke fuer Ihre Bewerbung, wir haben Ihre Unterlagen erhalten. Leider eine Absage."
    assert classify_heuristic(text).intent == "rejection"


def test_info_request_over_received():
    text = "Vielen Dank fuer Ihre Bewerbung. Bitte senden Sie uns noch Ihr Arbeitszeugnis."
    assert classify_heuristic(text).intent == "info_request"


def test_acknowledgment_promising_next_steps_is_not_an_interview():
    # Du-form acknowledgment that merely promises to follow up with next steps.
    text = (
        "Hallo Alex, vielen Dank für deine Bewerbung als Assistent:in Private Banking. "
        "Gerne prüfen wir deine Bewerbungsunterlagen sorgfältig und melden uns so bald wie "
        "möglich mit den nächsten Schritten bei dir."
    )
    assert classify_heuristic(text).intent == "application_received"


def test_english_acknowledgment_with_next_steps_is_received():
    text = "Thank you for applying. We will get back to you regarding the next steps."
    assert classify_heuristic(text).intent == "application_received"


def test_weak_interview_cue_alone_goes_to_review():
    # Only an ambiguous cue → interview, but with low confidence (needs review).
    result = classify_heuristic("Bitte teile uns deine Verfügbarkeit für nächste Woche mit.")
    assert result.intent == "interview_invite"
    assert result.confidence < 0.6


def test_strong_invite_still_wins_over_acknowledgment():
    text = (
        "Vielen Dank für deine Bewerbung. Gerne möchten wir dich zu einem "
        "Vorstellungsgespräch einladen."
    )
    assert classify_heuristic(text).intent == "interview_invite"


def test_continuing_after_interview_is_next_round():
    text = (
        "Vielen Dank für deine Zeit gestern, es hat uns sehr gefreut dich persönlich "
        "kennenzulernen! Gerne möchten wir im Prozess weitermachen und eine Referenz einholen."
    )
    assert classify_heuristic(text).intent == "next_round"


def test_outbound_is_application_sent():
    result = classify_heuristic("Hiermit bewerbe ich mich um die Stelle.", direction="sent")
    assert result.intent == "application_sent"


# --- Interview invitations seen in real mailboxes -----------------------------

def _classify(subject: str, body: str, direction: str = "received") -> str:
    return HeuristicClassifier().classify(
        EmailInput(sender="recruiting@bank.example", subject=subject, body=body,
                   direction=direction)
    ).intent


@pytest.mark.parametrize(
    "subject, body",
    [
        ("Get ready for your interview - Client Account Manager",
         "Your interview for the role of Client Account Manager is scheduled for "
         "August 11, 2026, 11:00 AM."),
        ("We'd like to meet you - In-Person Interview availability",
         "We'd like to meet you for an in-person interview. You'll find the available "
         "time slots below."),
        ("RE: Interview",
         "Bitte melden Sie sich bei Ihrer Ankunft an der Rezeption im 5. Stock und geben "
         "Sie an, dass Sie ein Gespräch mit Frau Muster haben."),
        ("UBP Interview",
         "Vielen Dank für Ihr Interesse und für Ihre Bewerbung für die Position Wealth "
         "Management Assistant."),
        ("Ihre Bewerbung", "Gerne möchten wir Sie zu einem persönlichen Gespräch einladen."),
    ],
)
def test_real_world_interview_invitations(subject, body):
    assert _classify(subject, body) == "interview_invite"


@pytest.mark.parametrize(
    "body",
    [
        "Gerne möchten wir dich zu einem weiteren Interview einladen. Würde dir Dienstag passen?",
        "Vielen Dank für deine Zeit heute. Wir führen diese Woche noch finale Gespräche und "
        "melden uns nächsten Montag mit Feedback bei dir.",
    ],
)
def test_later_rounds_are_next_round(body):
    assert _classify("RE: Bewerbung", body) == "next_round"


@pytest.mark.parametrize(
    "body",
    [
        "Vielen Dank für Ihre Bewerbung. Falls Ihr Profil passt, laden wir Sie gerne zu "
        "einem Gespräch ein.",
        "Thank you for applying. If selected, we will contact you to schedule your interview.",
    ],
)
def test_conditional_interview_mention_is_still_an_acknowledgment(body):
    assert _classify("Ihre Bewerbung", body) == "application_received"


def test_best_fit_rejection():
    body = ("We have reviewed your resume and after careful consideration, we have determined "
            "that we do not have the best fit at this time.")
    assert _classify("Your application with PIMCO", body) == "rejection"


def test_document_request_du_form():
    body = "Darf ich dich bitten, mir deine Beurteilungen für 2024 und 2025 zuzusenden?"
    assert _classify("Bewerbung im Team Europe", body) == "info_request"


# --- Your own outgoing mail -----------------------------------------------------

@pytest.mark.parametrize(
    "subject, body",
    [
        ("Re: UBP Interview", "Vielen Dank für die Einladung. Der Termin passt mir gut."),
        ("AW: Ihre Bewerbung", "Gerne bestätige ich den Termin."),
        ("Fwd: Get ready for your interview", "------- Weitergeleitete Nachricht -------"),
        ("Rückfrage zum weiteren Ablauf", "Vielen Dank für das heutige Gespräch. Wie geht es weiter?"),
    ],
)
def test_own_replies_and_forwards_are_not_new_applications(subject, body):
    assert _classify(subject, body, direction="sent") == "not_application_related"


def test_own_application_mail_is_application_sent():
    assert _classify("Bewerbung als Client Advisor", "Anbei mein Lebenslauf.", "sent") == (
        "application_sent"
    )
