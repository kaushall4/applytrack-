"""Supplementary heuristic tests (language detection, noise, confidence).

Intent classification + precedence live in test_classifier.py.
"""

from __future__ import annotations

from applytrack.classify.base import EmailInput, Intent
from applytrack.classify.heuristic import HeuristicClassifier, classify_heuristic
from applytrack.lang import detect_language

from .fixtures.classification_fixtures import FIXTURES


def test_language_detection_german():
    assert detect_language("Sehr geehrte Damen und Herren, leider müssen wir absagen.") == "de"


def test_language_detection_english():
    assert detect_language("Dear team, unfortunately we have decided to proceed.") == "en"


def test_confidence_in_range():
    for text, _expected, _lang in FIXTURES:
        result = classify_heuristic(text)
        assert 0.0 <= result.confidence <= 1.0


def test_noise_sender_without_signal_is_filtered():
    result = HeuristicClassifier().classify(
        EmailInput(
            sender="no-reply@linkedin.example",
            subject="Neue Jobs",
            body="Schau dir neue Stellen an.",
        )
    )
    assert result.intent == Intent.NOT_APPLICATION_RELATED


def test_noreply_sender_with_rejection_still_detected():
    # A real rejection from a no-reply address must NOT be dropped as noise.
    result = HeuristicClassifier().classify(
        EmailInput(
            sender="no-reply@beispiel-bank.ch",
            subject="Ihre Bewerbung",
            body="Leider müssen wir Ihnen absagen.",
        )
    )
    assert result.intent == Intent.REJECTION
