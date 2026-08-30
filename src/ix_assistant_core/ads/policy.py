from __future__ import annotations

from dataclasses import dataclass


SENSITIVE_TERMS = {
    "medical",
    "doctor",
    "diagnosis",
    "debt",
    "bank",
    "password",
    "religion",
    "politics",
    "divorce",
    "legal",
    "lawsuit",
    "child",
    "location",
}


@dataclass(frozen=True, slots=True)
class AdDecision:
    show_bottom_ad: bool
    allowed_context: str
    reason: str


@dataclass(frozen=True, slots=True)
class AdPolicy:
    """Ad policy for a free tier that protects assistant trust."""

    allow_bottom_banner: bool = True
    allow_voice_content_targeting: bool = False
    allow_sensitive_context_ads: bool = False

    def decide(self, *, screen_name: str, transcript_text: str | None = None) -> AdDecision:
        if not self.allow_bottom_banner:
            return AdDecision(False, "none", "bottom banner ads are disabled")
        transcript_text = transcript_text or ""
        if self.allow_voice_content_targeting:
            raise ValueError("voice content targeting is not allowed")
        if _contains_sensitive_context(transcript_text) and not self.allow_sensitive_context_ads:
            return AdDecision(False, "none", "sensitive context suppresses ads on this screen")
        return AdDecision(True, screen_name, "generic screen-level ad only")


def _contains_sensitive_context(text: str) -> bool:
    normalized = text.lower()
    return any(term in normalized for term in SENSITIVE_TERMS)
