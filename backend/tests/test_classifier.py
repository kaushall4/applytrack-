"""Fragment-heuristic classification + precedence tests."""

import pytest

from applytrack.classify.heuristic import classify_heuristic

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
