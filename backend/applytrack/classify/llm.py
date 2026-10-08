"""Anthropic-backed bilingual classifier with defensive JSON parsing.

Any failure — missing key, network error, malformed JSON, unknown intent — is
caught and the email is routed through the heuristic fallback so callers always
receive a valid :class:`Classification`.
"""

from __future__ import annotations

import json
import logging
import re

from ..config import get_settings
from .base import Classification, EmailInput, Intent
from .heuristic import HeuristicClassifier
from .prompts import FEW_SHOT_MESSAGES, SYSTEM_PROMPT, build_user_message

logger = logging.getLogger("applytrack.classify")

_JSON_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)


class LLMClassifier:
    """Classifier using the Anthropic Messages API, with heuristic fallback."""

    source = "llm"

    def __init__(self) -> None:
        self._settings = get_settings()
        self._fallback = HeuristicClassifier()
        self._client = None  # lazily created so import never requires the key

    def _get_client(self):
        if self._client is None:
            from anthropic import Anthropic

            self._client = Anthropic(api_key=self._settings.anthropic_api_key)
        return self._client

    def classify(self, email: EmailInput) -> Classification:
        # Outbound mail is unambiguous; don't spend a token on it.
        if email.direction == "sent":
            return self._fallback.classify(email)

        try:
            return self._classify_llm(email)
        except Exception as exc:  # noqa: BLE001 — fallback must catch everything
            logger.warning("LLM classification failed (%s); using heuristic.", type(exc).__name__)
            return self._fallback.classify(email)

    def _classify_llm(self, email: EmailInput) -> Classification:
        client = self._get_client()
        message = client.messages.create(
            model=self._settings.applytrack_model,
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[
                *FEW_SHOT_MESSAGES,
                {
                    "role": "user",
                    "content": build_user_message(email.sender, email.subject, email.body),
                },
            ],
        )
        text = "".join(block.text for block in message.content if block.type == "text")
        data = _parse_json(text)
        result = _to_classification(data)
        return _apply_rejection_precedence(email, result)


# Intents the LLM may pick that are "weaker than rejection" and most likely to
# be a missed compliment-sandwich. We do NOT override interview/next_round/offer
# — there the LLM has full context (e.g. "leider verzögert, aber Einladung…").
_REJECTION_SAFETY_NET = {
    Intent.APPLICATION_RECEIVED,
    Intent.APPLICATION_SENT,
    Intent.NOT_APPLICATION_RELATED,
}


def _apply_rejection_precedence(email: EmailInput, result: Classification) -> Classification:
    """Safety net: if the text carries a rejection fragment but the model picked
    a weak acknowledgment-like intent, enforce rejection (precedence)."""
    if result.intent not in _REJECTION_SAFETY_NET:
        return result

    from .fragments import FRAGMENTS, fold

    folded = fold(f"{email.subject}\n{email.body}")
    if any(frag in folded for frag in FRAGMENTS[Intent.REJECTION]):
        result.intent = Intent.REJECTION
        result.reasoning = (result.reasoning or "") + " [precedence: rejection fragment present]"
    return result


def _parse_json(text: str) -> dict:
    """Extract and parse the JSON object, tolerating stray prose or fences."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = _JSON_OBJ_RE.search(text)
    if not match:
        raise ValueError("No JSON object found in model response")
    return json.loads(match.group(0))


def _to_classification(data: dict) -> Classification:
    """Validate and coerce the model's JSON into a Classification."""
    if not isinstance(data, dict):
        raise ValueError("Model response was not a JSON object")

    intent = Intent.from_str(data.get("intent"))

    raw_conf = data.get("confidence", 0.5)
    try:
        confidence = float(raw_conf)
    except (TypeError, ValueError):
        confidence = 0.5

    language = str(data.get("language") or "en").lower()
    company = _clean_str(data.get("company"))
    role = _clean_str(data.get("role"))
    reasoning = _clean_str(data.get("reasoning"))

    return Classification(
        intent=intent,
        confidence=confidence,
        language=language,
        company=company,
        role=role,
        reasoning=reasoning,
        source="llm",
    ).clamp()


def _clean_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"null", "none", "n/a", "unknown"}:
        return None
    return text
