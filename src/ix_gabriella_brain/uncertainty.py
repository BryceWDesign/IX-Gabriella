from __future__ import annotations

from dataclasses import dataclass

from .models import IntentCandidate, RiskLevel
from .text import lower_ascii

_AMBIGUOUS = ("thing", "stuff", "whatever", "something", "maybe", "guess", "that one", "it")


@dataclass(frozen=True)
class UncertaintyAssessment:
    confidence: float
    should_ask: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {"confidence": self.confidence, "should_ask": self.should_ask, "reasons": list(self.reasons)}


class UncertaintyEngine:
    def assess(self, text: str, intent: IntentCandidate | None, risk: RiskLevel) -> UncertaintyAssessment:
        cleaned = lower_ascii(text)
        base = intent.confidence if intent else 0.58
        reasons: list[str] = []
        if intent and intent.missing_slots:
            base -= 0.15 * len(intent.missing_slots)
            reasons.append("missing_required_slots:" + ",".join(intent.missing_slots))
        if any(marker in cleaned for marker in _AMBIGUOUS):
            base -= 0.12
            reasons.append("ambiguous_reference")
        if risk in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
            base -= 0.10
            reasons.append("consequential_action_requires_extra_caution")
        confidence = max(0.0, min(1.0, base))
        should_ask = confidence < 0.62 or bool(intent and intent.missing_slots)
        if not reasons:
            reasons.append("sufficient_operational_clarity")
        return UncertaintyAssessment(confidence=confidence, should_ask=should_ask, reasons=tuple(reasons))
