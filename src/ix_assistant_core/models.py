from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum, auto
from typing import Any
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def new_id(prefix: str) -> str:
    cleaned = prefix.strip().lower().replace("_", "-") or "id"
    return f"{cleaned}-{uuid4().hex}"


class InputMode(StrEnum):
    TEXT = auto()
    VOICE = auto()
    SYSTEM = auto()


class IntentKind(StrEnum):
    UNKNOWN = auto()
    SMALL_TALK = auto()
    SHOW_HELP = auto()
    ANSWER_QUESTION = auto()
    WEB_SEARCH = auto()
    SET_TIMER = auto()
    SET_REMINDER = auto()
    CREATE_NOTE = auto()
    ADD_TO_LIST = auto()
    CALENDAR_DRAFT = auto()
    EMAIL_DRAFT = auto()
    SMART_HOME_CONTROL = auto()
    MEMORY_WRITE = auto()
    MEMORY_READ = auto()
    PRIVACY_CONTROL = auto()
    AD_PREFERENCE = auto()
    APP_SETTINGS = auto()
    SAFETY_STOP = auto()
    BRAIN_PLAN = auto()


class ActionRisk(StrEnum):
    LOW = auto()
    MODERATE = auto()
    HIGH = auto()
    CRITICAL = auto()


class PolicyOutcome(StrEnum):
    ALLOW = auto()
    REQUIRE_CONFIRMATION = auto()
    BLOCK = auto()


class ActionStatus(StrEnum):
    PLANNED = auto()
    WAITING_FOR_CONFIRMATION = auto()
    COMPLETED = auto()
    BLOCKED = auto()
    CORRECTED = auto()
    FAILED = auto()
    WAITING_FOR_CLARIFICATION = auto()


@dataclass(frozen=True, slots=True)
class Transcript:
    text: str
    mode: InputMode = InputMode.TEXT
    acoustic_confidence: float | None = None
    alternatives: tuple[str, ...] = ()
    created_at: datetime = field(default_factory=utc_now)
    transcript_id: str = field(default_factory=lambda: new_id("transcript"))

    def __post_init__(self) -> None:
        cleaned = " ".join(self.text.strip().split())
        if not cleaned:
            raise ValueError("transcript text must not be empty")
        object.__setattr__(self, "text", cleaned)
        if self.acoustic_confidence is not None:
            bounded = max(0.0, min(1.0, float(self.acoustic_confidence)))
            object.__setattr__(self, "acoustic_confidence", bounded)
        object.__setattr__(
            self,
            "alternatives",
            tuple(" ".join(item.strip().split()) for item in self.alternatives if item.strip()),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["mode"] = self.mode.value
        payload["created_at"] = self.created_at.isoformat()
        payload["alternatives"] = list(self.alternatives)
        return payload


@dataclass(frozen=True, slots=True)
class DecodedIntent:
    intent_id: str
    kind: IntentKind
    raw_text: str
    normalized_text: str
    confidence: float
    uncertainty: float
    target: str | None = None
    slots: dict[str, Any] = field(default_factory=dict)
    reasons: tuple[str, ...] = ()
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.intent_id.strip():
            raise ValueError("intent_id must not be empty")
        if not self.raw_text.strip():
            raise ValueError("raw_text must not be empty")
        object.__setattr__(self, "confidence", max(0.0, min(1.0, float(self.confidence))))
        object.__setattr__(self, "uncertainty", max(0.0, min(1.0, float(self.uncertainty))))
        object.__setattr__(
            self,
            "reasons",
            tuple(reason.strip().lower().replace(" ", "-") for reason in self.reasons if reason.strip()),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "kind": self.kind.value,
            "raw_text": self.raw_text,
            "normalized_text": self.normalized_text,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "target": self.target,
            "slots": self.slots,
            "reasons": list(self.reasons),
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class ActionPlan:
    intent: DecodedIntent
    risk: ActionRisk
    summary: str
    preview: str
    requires_confirmation: bool
    allowed_tools: tuple[str, ...] = ()
    irreversible: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent.to_dict(),
            "risk": self.risk.value,
            "summary": self.summary,
            "preview": self.preview,
            "requires_confirmation": self.requires_confirmation,
            "allowed_tools": list(self.allowed_tools),
            "irreversible": self.irreversible,
        }


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    intent_id: str
    outcome: PolicyOutcome
    reason_codes: tuple[str, ...]
    rationale: str
    fallback_action: str = "ask_clarifying_question"
    decided_at: datetime = field(default_factory=utc_now)

    @property
    def allowed(self) -> bool:
        return self.outcome == PolicyOutcome.ALLOW

    @property
    def needs_confirmation(self) -> bool:
        return self.outcome == PolicyOutcome.REQUIRE_CONFIRMATION

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "outcome": self.outcome.value,
            "reason_codes": list(self.reason_codes),
            "rationale": self.rationale,
            "fallback_action": self.fallback_action,
            "decided_at": self.decided_at.isoformat(),
            "allowed": self.allowed,
            "needs_confirmation": self.needs_confirmation,
        }


@dataclass(frozen=True, slots=True)
class AssistantTurn:
    transcript: Transcript
    intent: DecodedIntent
    plan: ActionPlan
    policy: PolicyDecision
    status: ActionStatus
    response_text: str
    receipt_ids: tuple[str, ...]
    confirmation_prompt: str | None = None
    brain_packet: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "transcript": self.transcript.to_dict(),
            "intent": self.intent.to_dict(),
            "plan": self.plan.to_dict(),
            "policy": self.policy.to_dict(),
            "status": self.status.value,
            "response_text": self.response_text,
            "receipt_ids": list(self.receipt_ids),
            "confirmation_prompt": self.confirmation_prompt,
            "brain_packet": self.brain_packet,
        }
