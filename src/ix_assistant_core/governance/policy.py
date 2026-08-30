from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field

from ix_assistant_core.models import ActionPlan, ActionRisk, PolicyDecision, PolicyOutcome


@dataclass(frozen=True, slots=True)
class GovernancePolicy:
    """Fail-closed assistant policy inspired by BlackFox and SynapDrive patterns."""

    min_confidence: float = 0.64
    high_risk_min_confidence: float = 0.84
    max_uncertainty: float = 0.36
    safe_fallback_action: str = "ask_clarifying_question"
    denied_patterns: tuple[str, ...] = (
        "*send money*",
        "*wire transfer*",
        "*buy *",
        "*purchase *",
        "*delete account*",
        "*disable security*",
        "*bypass*",
        "*unlock door*",
    )
    always_confirm_patterns: tuple[str, ...] = (
        "*send*email*",
        "*message*",
        "*calendar*invite*",
        "*remember*",
        "*delete history*",
        "*privacy*",
        "*door*",
        "*garage*",
        "*thermostat*",
    )

    def __post_init__(self) -> None:
        for label, value in (
            ("min_confidence", self.min_confidence),
            ("high_risk_min_confidence", self.high_risk_min_confidence),
            ("max_uncertainty", self.max_uncertainty),
        ):
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{label} must be in [0, 1]")

    def evaluate(self, plan: ActionPlan) -> PolicyDecision:
        text = plan.intent.normalized_text
        reasons: list[str] = []

        if any(fnmatch.fnmatch(text, pattern) for pattern in self.denied_patterns):
            return PolicyDecision(
                intent_id=plan.intent.intent_id,
                outcome=PolicyOutcome.BLOCK,
                reason_codes=("denied-pattern",),
                rationale="The requested action matches a blocked safety or financial pattern.",
                fallback_action=self.safe_fallback_action,
            )

        if plan.risk == ActionRisk.CRITICAL:
            return PolicyDecision(
                intent_id=plan.intent.intent_id,
                outcome=PolicyOutcome.BLOCK,
                reason_codes=("critical-risk",),
                rationale="Critical-risk actions are blocked by default.",
                fallback_action=self.safe_fallback_action,
            )

        threshold = self.high_risk_min_confidence if plan.risk == ActionRisk.HIGH else self.min_confidence
        if plan.intent.confidence < threshold:
            reasons.append("confidence-below-policy")
        if plan.intent.uncertainty > self.max_uncertainty:
            reasons.append("uncertainty-above-policy")
        if plan.intent.kind.value == "unknown":
            reasons.append("unknown-intent")

        if reasons:
            return PolicyDecision(
                intent_id=plan.intent.intent_id,
                outcome=PolicyOutcome.REQUIRE_CONFIRMATION,
                reason_codes=tuple(dict.fromkeys(reasons)),
                rationale="The assistant is not confident enough to act without clarification.",
                fallback_action=self.safe_fallback_action,
            )

        if plan.requires_confirmation or any(
            fnmatch.fnmatch(text, pattern) for pattern in self.always_confirm_patterns
        ):
            return PolicyDecision(
                intent_id=plan.intent.intent_id,
                outcome=PolicyOutcome.REQUIRE_CONFIRMATION,
                reason_codes=("approval-required", plan.risk.value),
                rationale="This action requires visible user confirmation before execution.",
                fallback_action=self.safe_fallback_action,
            )

        return PolicyDecision(
            intent_id=plan.intent.intent_id,
            outcome=PolicyOutcome.ALLOW,
            reason_codes=("low-risk-local-action",),
            rationale="Low-risk local action passed policy.",
            fallback_action=self.safe_fallback_action,
        )
