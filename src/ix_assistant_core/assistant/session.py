from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ix_assistant_core.assistant.engine import GabriellaAssistant
from ix_assistant_core.models import ActionStatus, AssistantTurn, InputMode

_APPROVAL_WORDS = {"yes", "yeah", "yep", "approve", "confirm", "confirmed", "do it", "that's right"}
_REJECTION_WORDS = {"no", "nope", "cancel", "reject", "wrong", "stop", "do not"}
_CORRECTION_PREFIXES = ("no i meant", "no, i meant", "i meant", "correction", "correct that to")


@dataclass(slots=True)
class AssistantSession:
    """Stateful conversation wrapper for GUI and terminal chat."""

    assistant: GabriellaAssistant = field(default_factory=GabriellaAssistant.default)
    pending_turn: AssistantTurn | None = None
    history: list[dict[str, Any]] = field(default_factory=list)

    def submit(
        self,
        text: str,
        *,
        mode: InputMode = InputMode.TEXT,
        acoustic_confidence: float | None = None,
        alternatives: tuple[str, ...] = (),
    ) -> AssistantTurn:
        clean = " ".join(text.strip().split())
        if not clean:
            raise ValueError("message text must not be empty")

        if self.pending_turn is not None:
            normalized = clean.lower()
            correction = _extract_correction(normalized)
            if correction:
                turn = self.assistant.correct(self.pending_turn, correction)
                self.pending_turn = turn if turn.status == ActionStatus.WAITING_FOR_CONFIRMATION else None
                self._record(clean, turn)
                return turn
            if _contains_any(normalized, _APPROVAL_WORDS | _REJECTION_WORDS):
                turn = self.assistant.confirm(self.pending_turn, clean)
                self.pending_turn = None
                self._record(clean, turn)
                return turn

        turn = self.assistant.handle_text(
            clean,
            mode=mode,
            acoustic_confidence=acoustic_confidence,
            alternatives=alternatives,
        )
        self.pending_turn = turn if turn.status == ActionStatus.WAITING_FOR_CONFIRMATION else None
        self._record(clean, turn)
        return turn

    def confirm_pending(self, approved: bool) -> AssistantTurn | None:
        if self.pending_turn is None:
            return None
        reply = "yes confirm" if approved else "no cancel"
        turn = self.assistant.confirm(self.pending_turn, reply)
        self.pending_turn = None
        self._record(reply, turn)
        return turn

    def correct_pending(self, corrected_text: str) -> AssistantTurn | None:
        if self.pending_turn is None:
            return None
        turn = self.assistant.correct(self.pending_turn, corrected_text)
        self.pending_turn = turn if turn.status == ActionStatus.WAITING_FOR_CONFIRMATION else None
        self._record(corrected_text, turn)
        return turn

    def snapshot(self) -> dict[str, Any]:
        return {
            "pending": None if self.pending_turn is None else self.pending_turn.to_dict(),
            "history": self.history[-50:],
            "receipt_count": len(self.assistant.receipts.records()),
            "memory_count": len(self.assistant.memory.list()),
            "local_action_count": len(self.assistant.local_store.list_records()),
            "brain_enabled": True,
            "llm_layer": self.assistant.llm.provider.mode.value,
        }

    def _record(self, user_text: str, turn: AssistantTurn) -> None:
        self.history.append(
            {
                "user_text": user_text,
                "assistant_text": turn.response_text,
                "status": turn.status.value,
                "intent": turn.intent.kind.value,
                "receipt_ids": list(turn.receipt_ids),
                "brain_route": None if turn.brain_packet is None else turn.brain_packet["route"]["route"],
                "brain_status": None if turn.brain_packet is None else turn.brain_packet["decision"]["status"],
                "llm_reason": None if turn.brain_packet is None else turn.brain_packet.get("llm", {}).get("reason"),
            }
        )


def _extract_correction(normalized: str) -> str | None:
    for prefix in _CORRECTION_PREFIXES:
        if normalized.startswith(prefix):
            return normalized[len(prefix):].strip(" ,.:;") or None
    return None


def _contains_any(text: str, tokens: set[str]) -> bool:
    return any(token in text for token in tokens)
