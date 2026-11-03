"""AI categorization integration (AIR-01, AIR-02, FR-04, FR-05).

Categories are SUGGESTIONS only. Any failure returns an 'unavailable' suggestion
so visit-note saving is never blocked.
"""
import json
import os
import urllib.request
from abc import ABC, abstractmethod

CATEGORIES = ("Respiratory", "Digestive", "Musculoskeletal", "General/Other")
CONFIDENCE_THRESHOLD = 0.60


class Suggestion:
    def __init__(self, category=None, confidence=0.0, source="none", message=""):
        self.category = category
        self.confidence = confidence
        self.source = source
        self.message = message

    @property
    def usable(self):
        return self.category in CATEGORIES and self.confidence >= CONFIDENCE_THRESHOLD


class Categorizer(ABC):
    name = "abstract"

    @abstractmethod
    def categorize(self, text):
        """Return (category, confidence). May raise on failure."""


class ClaudeCategorizer(Categorizer):
    """Real AI model via Anthropic API. Requires ANTHROPIC_API_KEY."""
    name = "Claude API (AI model)"

    def __init__(self, timeout=10):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.timeout = timeout

    def available(self):
        return bool(self.api_key)

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
            headers={"content-type": "application/json", "x-api-key": self.api_key,
                     "anthropic-version": "2023-06-01"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read())
        parsed = json.loads(data["content"][0]["text"])
        return parsed["category"], float(parsed["confidence"])


class KeywordFallbackCategorizer(Categorizer):
    """TEMPORARY keyword fallback / test substitute. NOT an AI model."""
    name = "Keyword fallback (NOT an AI model)"
    KEYWORDS = {
        "Respiratory": ["cough", "congestion", "breath", "wheez", "asthma", "sore throat"],
        "Digestive": ["nausea", "vomit", "stomach", "diarrhea", "abdominal", "constipation"],
        "Musculoskeletal": ["back pain", "joint", "muscle", "sprain", "knee", "shoulder", "fracture"],
    }

    def categorize(self, text):
        lowered = text.lower()
        scores = {cat: sum(k in lowered for k in kws) for cat, kws in self.KEYWORDS.items()}
        best = max(scores, key=scores.get)
        if scores[best] == 0:
            return "General/Other", 0.5
        return best, min(0.6 + 0.15 * scores[best], 0.9)


class CategorizationService:
    def __init__(self, primary=None, fallback=None):
        self.primary = primary or ClaudeCategorizer()
        self.fallback = fallback or KeywordFallbackCategorizer()

    def suggest(self, text):
        engines = []
        if isinstance(self.primary, ClaudeCategorizer):
            if self.primary.available():
                engines.append(self.primary)
        else:
            engines.append(self.primary)
        engines.append(self.fallback)
        for engine in engines:
            try:
                category, confidence = engine.categorize(text)
                suggestion = Suggestion(category, confidence, engine.name)
                if not suggestion.usable:
                    suggestion.message = "AI uncertain; note stays uncategorized."
                return suggestion
            except Exception as exc:  # AI failure must never block saving
                last_error = str(exc)
        return Suggestion(source="none", message=f"AI unavailable: {last_error}")
