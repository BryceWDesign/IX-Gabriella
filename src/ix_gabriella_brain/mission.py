from __future__ import annotations

from dataclasses import dataclass, field

from .models import RiskLevel
from .text import lower_ascii


@dataclass(frozen=True)
class MissionEnvelope:
    goal: str
    allowed_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    constraints: tuple[str, ...]
    risk: RiskLevel
    requires_human_authority: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "goal": self.goal,
            "allowed_actions": list(self.allowed_actions),
            "forbidden_actions": list(self.forbidden_actions),
            "constraints": list(self.constraints),
            "risk": self.risk.value,
            "requires_human_authority": self.requires_human_authority,
        }


@dataclass(frozen=True)
class MissionEnvelopeBuilder:
    default_forbidden: tuple[str, ...] = field(default=(
        "spend_money",
        "send_external_message_without_approval",
        "delete_user_data_without_approval",
        "change_device_state_without_approval",
        "store_long_term_memory_without_approval",
        "claim_true_agi_or_consciousness",
    ))

    def build(self, text: str, risk: RiskLevel) -> MissionEnvelope:
        cleaned = lower_ascii(text)
        constraints = self._constraints(cleaned)
        allowed = ["answer", "clarify", "stage_action", "write_receipt"]
        if risk == RiskLevel.LOW:
            allowed.append("execute_low_risk_local_action")
        if "plan" in cleaned or "prepare" in cleaned or "build" in cleaned:
            allowed.extend(["decompose_goal", "create_reviewable_plan"])
        forbidden = list(self.default_forbidden)
        if "do not" in cleaned or "don't" in cleaned or "never" in cleaned:
            forbidden.append("violate_user_negative_constraint")
        return MissionEnvelope(
            goal=text.strip(),
            allowed_actions=tuple(dict.fromkeys(allowed)),
            forbidden_actions=tuple(dict.fromkeys(forbidden)),
            constraints=constraints,
            risk=risk,
            requires_human_authority=risk != RiskLevel.LOW,
        )

    def _constraints(self, cleaned: str) -> tuple[str, ...]:
        constraints: list[str] = []
        markers = ("do not", "don't", "never", "without", "must", "only", "no ")
        for marker in markers:
            if marker in cleaned:
                constraints.append(f"user_constraint_contains:{marker}")
        return tuple(dict.fromkeys(constraints))
