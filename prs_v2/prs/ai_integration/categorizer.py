"""AI categorization integration (AIR-01, AIR-02, FR-04, FR-05).

Categories are SUGGESTIONS only. Any failure yields an 'unavailable'
suggestion so visit-note saving is never blocked.
"""
import json
import os
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass

CATEGORIES = ("Respiratory", "Digestive", "Musculoskeletal", "General/Other")
CONFIDENCE_THRESHOLD = 0.60


@dataclass(frozen=True)
class Suggestion:
    """Immutable result of a categorization attempt."""
    category: str = None
    confidence: float = 0.0
    source: str = "none"
    message: str = ""

    @property
    def usable(self):
        return self.category in CATEGORIES and self.confidence >= CONFIDENCE_THRESHOLD

    @classmethod
    def unavailable(cls, reason):
        return cls(message=f"AI unavailable: {reason}")


class Categorizer(ABC):
    """Common interface for every categorization engine."""
    name = "abstract"

    def available(self):
        """Whether this engine can currently be used."""
        return True

    @abstractmethod
    def categorize(self, text):
        """Return (category, confidence). May raise on failure."""


class ClaudeCategorizer(Categorizer):
    """Real AI model via Anthropic API. Requires ANTHROPIC_API_KEY."""
    name = "Claude API (AI model)"

    def __init__(self, timeout=10):
        self._api_key = os.environ.get("ANTHROPIC_API_KEY")
        self._timeout = timeout

    def available(self):
        return bool(self._api_key)

    def categorize(self, text):
        prompt = (
            "Classify this clinic visit note into exactly one category: "
            "Respiratory, Digestive, Musculoskeletal, or General/Other. This is an "
            "organizational label, not a diagnosis. Reply ONLY with JSON: "
            '{"category": "...", "confidence": 0.0-1.0}\n\nNote: ' + text)
        body = json.dumps({
            "model": "claude-sonnet-4-6", "max_tokens": 100,
            "messages": [{"role": "user", "content": prompt}]}).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=body,
            headers={"content-type": "application/json", "x-api-key": self._api_key,
                     "anthropic-version": "2023-06-01"})
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            data = json.loads(resp.read())
        parsed = json.loads(data["content"][0]["text"])
        return parsed["category"], float(parsed["confidence"])


class KeywordFallbackCategorizer(Categorizer):
    """TEMPORARY keyword fallback / test substitute. NOT an AI model."""
    name = "Keyword fallback (NOT an AI model)"
    KEYWORDS = {
        "Respiratory": ["cough", "congestion", "breath", "wheez", "asthma", "sore throat"],
        "Digestive": ["nausea", "vomit", "stomach", "diarrhea", "abdominal", "constipation"],
        "Musculoskeletal": ["back pain", "joint", "muscle", "sprain", "knee", "shoulder",
                            "fracture"],
    }

    def categorize(self, text):
        lowered = text.lower()
        scores = {cat: sum(k in lowered for k in kws) for cat, kws in self.KEYWORDS.items()}
        best = max(scores, key=scores.get)
        if scores[best] == 0:
            return "General/Other", 0.5
        return best, min(0.6 + 0.15 * scores[best], 0.9)


class CategorizationService:
    """Tries the primary engine first, then the fallback.

    Works with any ``Categorizer`` through the shared interface, so engines can
    be swapped without changing ``suggest`` (no isinstance checks).
    """

    def __init__(self, primary=None, fallback=None):
        self._engines = [primary or ClaudeCategorizer(),
                         fallback or KeywordFallbackCategorizer()]

    def suggest(self, text):
        last_error = "no categorization engine is available"
        for engine in self._engines:
            if not engine.available():
                continue
            try:
                category, confidence = engine.categorize(text)
            except Exception as exc:  # AI failure must never block saving
                last_error = str(exc)
                continue
            suggestion = Suggestion(category, confidence, engine.name)
            if not suggestion.usable:
                suggestion = Suggestion(category, confidence, engine.name,
                                        "AI uncertain; note stays uncategorized.")
            return suggestion
        return Suggestion.unavailable(last_error)
