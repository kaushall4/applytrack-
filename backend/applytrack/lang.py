"""Lightweight German/English language detection.

Deliberately dependency-free: a small stop-word vote is plenty to distinguish
DE from EN for short job-application emails, and it keeps the offline path fully
self-contained. Defaults to English on a tie or empty input.
"""

from __future__ import annotations

import re

# Common, discriminative stop words / markers for each language.
_DE_MARKERS = {
    "und", "der", "die", "das", "ich", "sie", "wir", "für", "mit", "nicht",
    "ihre", "ihnen", "freuen", "leider", "bewerbung", "gespräch", "stelle",
    "sehr", "geehrte", "geehrter", "freundlichen", "grüssen", "grüße",
    "haben", "wurde", "danke", "einladung", "absage", "rückmeldung",
}
_EN_MARKERS = {
    "the", "and", "you", "your", "we", "for", "with", "not", "are", "have",
    "unfortunately", "application", "interview", "position", "role", "team",
    "dear", "regards", "thank", "please", "candidate", "offer", "hiring",
}

_WORD_RE = re.compile(r"[a-zäöüß]+", re.IGNORECASE)


def detect_language(text: str) -> str:
    """Return ``"de"`` or ``"en"`` for the given text."""
    if not text:
        return "en"
    words = [w.lower() for w in _WORD_RE.findall(text)]
    if not words:
        return "en"

    de_score = sum(1 for w in words if w in _DE_MARKERS)
    en_score = sum(1 for w in words if w in _EN_MARKERS)

    # German-specific characters are a strong signal.
    if re.search(r"[äöü]", text, re.IGNORECASE) or "ß" in text:
        de_score += 2

    if de_score > en_score:
        return "de"
    return "en"
