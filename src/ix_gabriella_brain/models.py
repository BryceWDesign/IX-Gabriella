from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RouteKind(StrEnum):
    FAST_LANE = "fast_lane"
    CLARIFY_LANE = "clarify_lane"
    APPROVAL_LANE = "approval_lane"
    BRAIN_LANE = "brain_lane"
    REFUSAL_LANE = "refusal_lane"


class DecisionStatus(StrEnum):
    EXECUTED_LOCAL = "executed_local"
    STAGED = "staged"
    NEEDS_APPROVAL = "needs_approval"
    NEEDS_CLARIFICATION = "needs_clarification"
    REFUSED = "refused"
    PROPOSED_PLAN = "proposed_plan"


class MemoryState(StrEnum):
    QUARANTINED = "quarantined"
    APPROVED = "approved"
    REJECTED = "rejected"


class BeliefStatus(StrEnum):
    OBSERVED = "observed"
    INFERRED = "inferred"
    USER_CONFIRMED = "user_confirmed"
    CONTRADICTED = "contradicted"
    STALE = "stale"
    QUARANTINED = "quarantined"


@dataclass(frozen=True)
class BrainRequest:
    text: str
    user_id: str = "local-user"
    channel: str = "text"
    session_id: str = "local-session"
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IntentCandidate:
    name: str
    confidence: float
    risk: RiskLevel
    requires_approval: bool
    missing_slots: tuple[str, ...] = ()
    slots: dict[str, Any] = field(default_factory=dict)
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["risk"] = self.risk.value
        return data


@dataclass(frozen=True)
class RouteDecision:
    route: RouteKind
    reason: str
    confidence: float
    complexity_score: float
    intent: IntentCandidate | None = None
    required_approval: bool = False
    risk: RiskLevel = RiskLevel.LOW

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["route"] = self.route.value
        data["risk"] = self.risk.value
        data["intent"] = self.intent.to_dict() if self.intent else None
        return data


@dataclass(frozen=True)
class PlanStep:
    step_id: str
    title: str
    action_type: str
    rationale: str
    risk: RiskLevel = RiskLevel.LOW
    requires_approval: bool = False
    evidence_needed: tuple[str, ...] = ()
    expected_result: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["risk"] = self.risk.value
        return data


@dataclass(frozen=True)
class MemoryCandidate:
    memory_id: str
    text: str
    reason: str
    state: MemoryState = MemoryState.QUARANTINED
    source_request_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["state"] = self.state.value
        return data


@dataclass(frozen=True)
class BeliefRecord:
    belief_id: str
    subject: str
    predicate: str
    object_value: str
    status: BeliefStatus
    confidence: float
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass(frozen=True)
class BrainDecision:
    status: DecisionStatus
    user_message: str
    action: dict[str, Any] = field(default_factory=dict)
    plan: tuple[PlanStep, ...] = ()
    memory_candidate: MemoryCandidate | None = None
    needs_user_input: bool = False
    approval_question: str | None = None
    safety_notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["plan"] = [step.to_dict() for step in self.plan]
        data["memory_candidate"] = self.memory_candidate.to_dict() if self.memory_candidate else None
        return data


@dataclass(frozen=True)
class WorldTwinResult:
    verdict: str
    predicted_outcome: str
    risk_score: float
    uncertainty: float
    blocked_reasons: tuple[str, ...] = ()
    branch_notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AssuranceResult:
    readiness_score: float
    passed: bool
    claims_allowed: tuple[str, ...]
    claims_blocked: tuple[str, ...]
    evidence_coverage: dict[str, bool]
    findings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CognitivePacket:
    packet_id: str
    request: BrainRequest
    route: RouteDecision
    decision: BrainDecision
    worldtwin: WorldTwinResult
    assurance: AssuranceResult
    receipt_hash: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "request": self.request.to_dict(),
            "route": self.route.to_dict(),
            "decision": self.decision.to_dict(),
            "worldtwin": self.worldtwin.to_dict(),
            "assurance": self.assurance.to_dict(),
            "receipt_hash": self.receipt_hash,
            "created_at": self.created_at,
        }
