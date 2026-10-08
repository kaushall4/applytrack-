"""Bilingual fragment heuristic — the no-API-key classifier (and LLM fallback).

Matches short umlaut-folded fragments (see :mod:`applytrack.classify.fragments`)
against the email text and resolves the result by precedence, so a rejection
hidden inside a compliment sandwich still wins over the polite thank-you.
Outbound mail is classified as ``application_sent`` purely by direction.
"""

from __future__ import annotations

import re

from ..lang import detect_language
from .base import Classification, EmailInput, Intent
from .fragments import classify_by_precedence

# Senders that are almost always noise (only used when no application fragment
# matched — a real acknowledgment/rejection from a no-reply address still wins).
_NOISE_SENDER_RE = re.compile(
    r"(no[-_.]?reply|newsletter|notification|jobs?-?alert|digest|mailer|marketing)",
    re.IGNORECASE,
)
_NOISE_DOMAIN_RE = re.compile(
    r"@(linkedin|indeed|glassdoor|stepstone|xing|jobs\.ch|monster)\.",
    re.IGNORECASE,
)

_FREEMAIL = {"gmail", "outlook", "yahoo", "gmx", "hotmail", "icloud", "proton", "bluewin"}


def _confidence(num_fragments: int) -> float:
    """More matched fragments for the winning intent → higher confidence."""
    return min(0.95, 0.72 + 0.08 * (num_fragments - 1))


class HeuristicClassifier:
    """Offline DE/EN fragment classifier."""

    source = "heuristic"

    def classify(self, email: EmailInput) -> Classification:
        text = f"{email.subject}\n{email.body}"
        language = detect_language(text)

        if email.direction == "sent":
            return self._classify_outbound(email, language)

        intent, fragments, weak = classify_by_precedence(text, subject=email.subject)

        if intent is Intent.NOT_APPLICATION_RELATED:
            # No application signal. If the sender is a known job-board / no-reply
            # marketing address, label it noise with slightly higher confidence.
            is_noise = bool(
                _NOISE_SENDER_RE.search(email.sender) or _NOISE_DOMAIN_RE.search(email.sender)
            )
            return Classification(
                intent=Intent.NOT_APPLICATION_RELATED,
                confidence=0.75 if is_noise else 0.45,
                language=language,
                source=self.source,
                reasoning=(
                    "Sender matches a job-board / no-reply pattern; no application fragment."
                    if is_noise
                    else "No application fragments matched."
                ),
            ).clamp()

        company = _guess_company(email)
        if weak:
            # Only ambiguous cues ("next steps", "availability") → flag for review.
            confidence = 0.5
            reasoning = f"Only weak interview cue(s): {', '.join(fragments[:4])} — please verify."
        else:
            confidence = _confidence(len(fragments))
            reasoning = f"Matched {intent.value} fragment(s): {', '.join(fragments[:4])}."
        return Classification(
            intent=intent,
            confidence=confidence,
            language=language,
            company=company,
            role=None,
            source=self.source,
            reasoning=reasoning,
        ).clamp()


    def _classify_outbound(self, email: EmailInput, language: str) -> Classification:
        """Mail the user sent: a new application, or just a reply / forward."""
        if _REPLY_OR_FORWARD_RE.match(email.subject or ""):
            # Answering a recruiter or forwarding a mail is part of an existing
            # process, never a new application (it still shows in the timeline).
            return Classification(
                intent=Intent.NOT_APPLICATION_RELATED,
                confidence=0.9,
                language=language,
                source=self.source,
                reasoning="Your reply or forward — not a new application.",
            ).clamp()
        if not _APPLICATION_WORDS_RE.search(f"{email.subject}\n{email.body}"):
            return Classification(
                intent=Intent.NOT_APPLICATION_RELATED,
                confidence=0.6,
                language=language,
                source=self.source,
                reasoning="Outgoing mail without application content.",
            ).clamp()
        return Classification(
            intent=Intent.APPLICATION_SENT,
            confidence=0.9,
            language=language,
            source=self.source,
            reasoning="Application sent from the tracked account.",
        ).clamp()


# "Re:", "AW:", "Antw:", "Fwd:", "WG:", "FW:" (possibly repeated) at the start.
_REPLY_OR_FORWARD_RE = re.compile(r"^\s*(?:(?:re|aw|antw|fwd?|wg|tr)\s*:\s*)+", re.IGNORECASE)
# What an application mail mentions (DE/EN).
_APPLICATION_WORDS_RE = re.compile(
    r"bewerb|application|apply|applying|lebenslauf|\bcv\b|resume|curriculum|"
    r"motivationsschreiben|anschreiben|cover letter|\bstelle\b|position|vacancy",
    re.IGNORECASE,
)


def classify_heuristic(
    text: str, *, sender: str = "", direction: str = "received"
) -> Classification:
    """Classify raw email text with the fragment heuristic.

    Convenience wrapper used by tests and the LLM fallback path. ``text`` may be
    just the body, or subject + body concatenated.
    """
    return HeuristicClassifier().classify(
        EmailInput(sender=sender, subject="", body=text, direction=direction)
    )


def _guess_company(email: EmailInput) -> str | None:
    """Best-effort company from the sender domain (role is left to the LLM)."""
    match = re.search(r"@([\w.-]+)", email.sender)
    if not match:
        return None
    domain = match.group(1).split(".")[0]
    if domain and domain.lower() not in _FREEMAIL:
        return domain.capitalize()
    return None
