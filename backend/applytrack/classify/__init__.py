"""Email intent classification (LLM + bilingual heuristic fallback)."""

from .base import Classification, Intent, get_classifier
from .heuristic import HeuristicClassifier
from .llm import LLMClassifier

__all__ = [
    "Classification",
    "Intent",
    "HeuristicClassifier",
    "LLMClassifier",
    "get_classifier",
]
