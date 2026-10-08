"""Tests for defensive parsing of the LLM's JSON output."""

from __future__ import annotations

import pytest

from applytrack.classify.base import Intent
from applytrack.classify.llm import _parse_json, _to_classification


def test_parses_clean_json():
    data = _parse_json('{"intent": "rejection", "confidence": 0.9, "language": "de"}')
    assert data["intent"] == "rejection"


def test_parses_json_with_surrounding_prose():
    raw = 'Here is the result:\n{"intent": "offer", "confidence": 0.8, "language": "en"} Done.'
    data = _parse_json(raw)
    assert data["intent"] == "offer"


def test_parses_json_in_markdown_fence():
    raw = '```json\n{"intent": "interview_invite", "confidence": 0.7, "language": "en"}\n```'
    data = _parse_json(raw)
    assert data["intent"] == "interview_invite"


def test_no_json_raises():
    with pytest.raises(ValueError):
        _parse_json("the model said something unhelpful")


def test_unknown_intent_falls_back_to_not_related():
    c = _to_classification({"intent": "banana", "confidence": 0.9, "language": "en"})
    assert c.intent == Intent.NOT_APPLICATION_RELATED


def test_confidence_clamped():
    high = _to_classification({"intent": "offer", "confidence": 5, "language": "en"})
    assert high.confidence == 1.0
    low = _to_classification({"intent": "offer", "confidence": -2, "language": "en"})
    assert low.confidence == 0.0


def test_non_numeric_confidence_defaults():
    c = _to_classification({"intent": "offer", "confidence": "very sure", "language": "en"})
    assert 0.0 <= c.confidence <= 1.0


def test_invalid_language_defaults_to_en():
    c = _to_classification({"intent": "offer", "confidence": 0.9, "language": "fr"})
    assert c.language == "en"


def test_null_company_role_become_none():
    c = _to_classification(
        {"intent": "offer", "confidence": 0.9, "language": "en", "company": "null", "role": ""}
    )
    assert c.company is None
    assert c.role is None
