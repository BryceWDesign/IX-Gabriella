from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum, auto

from ix_assistant_core.models import ActionPlan, PolicyDecision, utc_now


class ApprovalStatus(StrEnum):
    APPROVED = auto()
    REJECTED = auto()


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    intent_id: str
    status: ApprovalStatus
    approved_text: str
    decided_by: str = "user"
    decided_at: str = field(default_factory=lambda: utc_now().isoformat())
    note: str = ""

    @property
    def approved(self) -> bool:
        return self.status == ApprovalStatus.APPROVED


class ApprovalGate:
    """Explicit human confirmation gate.

    IX-Gabriella treats decoded intent as a proposal, not permission. The gate
    only approves when the user explicitly confirms the visible action preview.
    """

    APPROVE_TOKENS = {"yes", "approve", "confirmed", "confirm", "do it", "that's right"}
    REJECT_TOKENS = {"no", "reject", "cancel", "stop", "wrong", "do not"}

    def decide(self, *, plan: ActionPlan, policy: PolicyDecision, user_reply: str) -> ApprovalDecision:
        normalized = " ".join(user_reply.lower().strip().split())
        if any(token in normalized for token in self.REJECT_TOKENS):
            return ApprovalDecision(
                intent_id=plan.intent.intent_id,
                status=ApprovalStatus.REJECTED,
                approved_text=plan.preview,
                note="User rejected or corrected the proposed action.",
            )
        if policy.needs_confirmation and any(token in normalized for token in self.APPROVE_TOKENS):
            return ApprovalDecision(
                intent_id=plan.intent.intent_id,
                status=ApprovalStatus.APPROVED,
                approved_text=plan.preview,
                note="User explicitly approved the proposed action.",
            )
        if policy.allowed:
            return ApprovalDecision(
                intent_id=plan.intent.intent_id,
                status=ApprovalStatus.APPROVED,
                approved_text=plan.preview,
                note="Policy allowed the low-risk action without extra confirmation.",
            )
        return ApprovalDecision(
            intent_id=plan.intent.intent_id,
            status=ApprovalStatus.REJECTED,
            approved_text=plan.preview,
            note="No explicit approval token was present.",
        )
