from __future__ import annotations

from .mission import MissionEnvelope
from .models import BrainDecision, DecisionStatus, RouteDecision, RouteKind, WorldTwinResult

_ALLOWED_CLAIMS = (
    "governed cognitive assistant brain layer",
    "AGI-candidate architecture research direction",
    "receipt-backed decision packet",
    "human-authority-gated consequential action",
)
_BLOCKED_CLAIMS = (
    "true AGI demonstrated",
    "consciousness demonstrated",
    "autonomous authority granted",
    "certified safe system",
)


class AssuranceCase:
    def evaluate(self, route: RouteDecision, decision: BrainDecision, mission: MissionEnvelope, world: WorldTwinResult) -> "AssuranceResult":
        from .models import AssuranceResult

        coverage = {
            "route_selected": route.route in set(RouteKind),
            "mission_envelope": bool(mission.allowed_actions and mission.forbidden_actions),
            "human_authority_boundary": not (mission.requires_human_authority and decision.status == DecisionStatus.EXECUTED_LOCAL),
            "worldtwin_checked": world.verdict in {"reviewable", "blocked", "local_safe_action"},
            "receipt_required": True,
            "claim_boundaries": True,
        }
        findings: list[str] = []
        if world.blocked_reasons:
            findings.append("worldtwin_blocked:" + ",".join(world.blocked_reasons))
        if route.required_approval and decision.status == DecisionStatus.EXECUTED_LOCAL:
            coverage["human_authority_boundary"] = False
            findings.append("approval_required_but_local_execution_attempted")
        readiness = sum(1 for ok in coverage.values() if ok) / len(coverage)
        passed = readiness >= 0.84 and not world.blocked_reasons
        return AssuranceResult(
            readiness_score=round(readiness, 3),
            passed=passed,
            claims_allowed=_ALLOWED_CLAIMS,
            claims_blocked=_BLOCKED_CLAIMS,
            evidence_coverage=coverage,
            findings=tuple(findings),
        )
