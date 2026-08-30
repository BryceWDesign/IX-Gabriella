from __future__ import annotations

from dataclasses import dataclass

from .fast_intents import FastIntentRegistry
from .models import DecisionStatus, IntentCandidate, RiskLevel, RouteKind


@dataclass(frozen=True)
class PolicyDecision:
    allowed_local_execution: bool
    requires_approval: bool
    refused: bool
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "allowed_local_execution": self.allowed_local_execution,
            "requires_approval": self.requires_approval,
            "refused": self.refused,
            "notes": list(self.notes),
        }


class BrainPolicy:
    def __init__(self, registry: FastIntentRegistry | None = None) -> None:
        self.registry = registry or FastIntentRegistry()

    def decide(self, route: RouteKind, intent: IntentCandidate | None) -> PolicyDecision:
        notes: list[str] = []
        if intent is None:
            return PolicyDecision(False, route == RouteKind.APPROVAL_LANE, False, ("open_request_requires_cognitive_review",))
        definition = self.registry.get_definition(intent.name)
        local_allowed = bool(definition and definition.local_execution_allowed and intent.risk == RiskLevel.LOW and not intent.requires_approval)
        if intent.missing_slots:
            return PolicyDecision(False, False, False, ("missing_slots_block_execution:" + ",".join(intent.missing_slots),))
        if intent.risk in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
            notes.append("consequential_intent_requires_explicit_user_approval")
        if intent.name in {"email_draft", "calendar_draft", "search_request", "smart_home_stage", "memory_proposal"}:
            notes.append("stage_only_until_user_approval")
        requires_approval = intent.requires_approval or intent.risk != RiskLevel.LOW or route == RouteKind.APPROVAL_LANE
        return PolicyDecision(local_allowed, requires_approval, False, tuple(notes or ("policy_allows_bounded_processing",)))

    def status_for(self, policy: PolicyDecision) -> DecisionStatus:
        if policy.refused:
            return DecisionStatus.REFUSED
        if policy.allowed_local_execution:
            return DecisionStatus.EXECUTED_LOCAL
        if policy.requires_approval:
            return DecisionStatus.NEEDS_APPROVAL
        return DecisionStatus.STAGED
