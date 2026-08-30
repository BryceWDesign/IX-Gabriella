from __future__ import annotations

from .mission import MissionEnvelope
from .models import BrainDecision, DecisionStatus, RiskLevel, WorldTwinResult

_RISK_NUM = {
    RiskLevel.LOW: 0.18,
    RiskLevel.MEDIUM: 0.45,
    RiskLevel.HIGH: 0.72,
    RiskLevel.CRITICAL: 0.95,
}


class WorldTwinLite:
    def evaluate(self, decision: BrainDecision, mission: MissionEnvelope) -> WorldTwinResult:
        blocked: list[str] = []
        notes: list[str] = []
        risk_score = _RISK_NUM[mission.risk]
        if decision.status == DecisionStatus.REFUSED:
            return WorldTwinResult(
                verdict="blocked",
                predicted_outcome="No action proceeds because the request was refused.",
                risk_score=risk_score,
                uncertainty=0.20,
                blocked_reasons=("decision_refused",),
                branch_notes=("safe_no_action_branch",),
            )
        for action in decision.action.get("requested_effects", ()):  # type: ignore[union-attr]
            if action in mission.forbidden_actions:
                blocked.append(f"forbidden_effect:{action}")
        if decision.status == DecisionStatus.EXECUTED_LOCAL and mission.risk != RiskLevel.LOW:
            blocked.append("non_low_risk_local_execution_blocked")
        if decision.status == DecisionStatus.NEEDS_APPROVAL:
            notes.append("approval_branch_holds_action_before_execution")
        if decision.plan:
            plan_risk = max((_RISK_NUM[step.risk] for step in decision.plan), default=risk_score)
            risk_score = max(risk_score, plan_risk)
            notes.append(f"plan_steps:{len(decision.plan)}")
        verdict = "blocked" if blocked else "reviewable"
        if decision.status == DecisionStatus.EXECUTED_LOCAL and not blocked:
            verdict = "local_safe_action"
        uncertainty = 0.15 if verdict == "local_safe_action" else min(0.75, risk_score + 0.08 * len(decision.plan))
        return WorldTwinResult(
            verdict=verdict,
            predicted_outcome=self._outcome(decision, verdict),
            risk_score=round(risk_score, 3),
            uncertainty=round(uncertainty, 3),
            blocked_reasons=tuple(blocked),
            branch_notes=tuple(notes),
        )

    def _outcome(self, decision: BrainDecision, verdict: str) -> str:
        if verdict == "blocked":
            return "The safest predicted outcome is holding the request and asking the user or refusing."
        if decision.status == DecisionStatus.EXECUTED_LOCAL:
            return "A low-risk local assistant state update is expected with receipt coverage."
        if decision.status == DecisionStatus.PROPOSED_PLAN:
            return "A reviewable plan is produced without executing external effects."
        if decision.status == DecisionStatus.NEEDS_APPROVAL:
            return "Action remains staged until the user explicitly approves."
        if decision.status == DecisionStatus.NEEDS_CLARIFICATION:
            return "No action proceeds until missing information is supplied."
        return "A bounded response is returned with evidence and receipt linkage."
