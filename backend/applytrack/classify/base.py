"""Classifier interface, the intent taxonomy, and the result type.

The taxonomy is the contract shared by the LLM classifier, the heuristic
fallback, the status state machine, and the API. Keep it in one place.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Protocol


class Intent(str, enum.Enum):
    """The single intent assigned to one email."""

    APPLICATION_SENT = "application_sent"
    APPLICATION_RECEIVED = "application_received"
    INTERVIEW_INVITE = "interview_invite"
    NEXT_ROUND = "next_round"
    REJECTION = "rejection"
    OFFER = "offer"
    INFO_REQUEST = "info_request"
    NOT_APPLICATION_RELATED = "not_application_related"

    @classmethod
    def from_str(cls, value: str | None) -> Intent:
        """Parse loosely; unknown / missing values become NOT_APPLICATION_RELATED."""
        if not value:
            return cls.NOT_APPLICATION_RELATED
        try:
            return cls(value.strip().lower())
        except ValueError:
            return cls.NOT_APPLICATION_RELATED


# Languages are first-class: "de" and "en" are equally supported.
SUPPORTED_LANGUAGES = ("de", "en")


@dataclass(slots=True)
class Classification:
    """Structured result of classifying one email."""

    intent: Intent
    confidence: float
    language: str
    company: str | None = None
    role: str | None = None
    reasoning: str | None = None
    source: str = "heuristic"  # "llm" or "heuristic" — for transparency/debugging

    def clamp(self) -> Classification:
        """Defensive normalisation of fields coming from an LLM."""
        self.confidence = max(0.0, min(1.0, float(self.confidence)))
        if self.language not in SUPPORTED_LANGUAGES:
            self.language = "en"
        return self


@dataclass(slots=True)
class EmailInput:
    """Minimal email view handed to a classifier."""

    sender: str
    subject: str
    body: str
    direction: str = "received"  # "sent" or "received"


class Classifier(Protocol):
    """Anything that can turn an email into a :class:`Classification`."""

    def classify(self, email: EmailInput) -> Classification: ...


def get_classifier() -> Classifier:
    """Return the best available classifier.

    Uses the Anthropic LLM when an API key is configured, otherwise the
    offline bilingual heuristic. The LLM classifier itself also falls back to
    the heuristic on any runtime error, so callers always get a result.
    """
    from ..config import get_settings
    from .heuristic import HeuristicClassifier
    from .llm import LLMClassifier

    settings = get_settings()
    if settings.llm_enabled:
        return LLMClassifier()
    return HeuristicClassifier()
