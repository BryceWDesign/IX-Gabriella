from __future__ import annotations

from .fast_intents import FastIntentRegistry
from .models import RiskLevel, RouteDecision, RouteKind
from .text import lower_ascii, tokens

_COMPLEX_SIGNALS = {
    "plan", "prepare", "strategy", "compare", "analyze", "research", "organize", "project",
    "roadmap", "architecture", "workflow", "upgrade", "design", "investigate", "summarize",
    "recommend", "diagnose", "decide", "evaluate", "build", "create", "launch", "monetize",
}
_HIGH_RISK_SIGNALS = {
    "delete", "erase", "send", "buy", "purchase", "pay", "wire", "transfer", "post", "publish",
    "share", "upload", "unsubscribe", "remove", "shutdown", "unlock", "password", "private",
}
_AMBIGUITY_SIGNALS = {"maybe", "whatever", "something", "thing", "stuff", "somehow", "guess", "probably"}


class DownshiftRouter:
    def __init__(self, registry: FastIntentRegistry | None = None) -> None:
        self.registry = registry or FastIntentRegistry()

    def route(self, text: str) -> RouteDecision:
        cleaned = lower_ascii(text)
        words = tokens(cleaned)
        intent = self.registry.match(cleaned)
        complexity = self._complexity_score(cleaned, words)
        risk = self._risk_from_text(cleaned, intent.risk if intent else RiskLevel.LOW)
        if intent and intent.confidence >= 0.78 and intent.missing_slots:
            return RouteDecision(
                route=RouteKind.CLARIFY_LANE,
                reason="recognized simple task but required details are missing",
                confidence=intent.confidence,
                complexity_score=complexity,
                intent=intent,
                required_approval=False,
                risk=risk,
            )
        if intent and intent.confidence >= 0.78 and complexity < 0.55:
            route = RouteKind.APPROVAL_LANE if intent.requires_approval or risk in {RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL} else RouteKind.FAST_LANE
            return RouteDecision(
                route=route,
                reason="recognized fast-lane assistant task",
                confidence=intent.confidence,
                complexity_score=complexity,
                intent=intent,
                required_approval=route == RouteKind.APPROVAL_LANE,
                risk=risk,
            )
        if intent and intent.confidence >= 0.55 and intent.missing_slots:
            return RouteDecision(
                route=RouteKind.CLARIFY_LANE,
                reason="partial intent match needs clarification",
                confidence=intent.confidence,
                complexity_score=complexity,
                intent=intent,
                required_approval=False,
                risk=risk,
            )
        if any(signal in cleaned for signal in _HIGH_RISK_SIGNALS) and not intent:
            return RouteDecision(
                route=RouteKind.APPROVAL_LANE,
                reason="request includes consequential action language without enough structure",
                confidence=0.50,
                complexity_score=complexity,
                intent=intent,
                required_approval=True,
                risk=RiskLevel.HIGH,
            )
        return RouteDecision(
            route=RouteKind.BRAIN_LANE,
            reason="request needs cognitive planning or open interpretation",
            confidence=max(intent.confidence if intent else 0.0, 0.62),
            complexity_score=complexity,
            intent=intent,
            required_approval=risk != RiskLevel.LOW,
            risk=risk,
        )

    def _complexity_score(self, cleaned: str, words: tuple[str, ...]) -> float:
        score = 0.0
        if len(words) > 18:
            score += 0.20
        if len(words) > 32:
            score += 0.20
        score += min(0.35, 0.08 * sum(1 for word in words if word in _COMPLEX_SIGNALS))
        score += min(0.20, 0.07 * sum(1 for word in words if word in _AMBIGUITY_SIGNALS))
        if " and " in cleaned or ";" in cleaned:
            score += 0.10
        if any(cleaned.startswith(prefix) for prefix in ("why", "how", "what if", "can you help")):
            score += 0.12
        return min(1.0, score)

    def _risk_from_text(self, cleaned: str, baseline: RiskLevel) -> RiskLevel:
        if any(word in cleaned for word in ("wire", "transfer money", "password", "delete account")):
            return RiskLevel.CRITICAL
        if any(word in cleaned for word in _HIGH_RISK_SIGNALS):
            return RiskLevel.HIGH
        if baseline in {RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL}:
            return baseline
        if any(word in cleaned for word in ("email", "calendar", "search", "device", "lights")):
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
