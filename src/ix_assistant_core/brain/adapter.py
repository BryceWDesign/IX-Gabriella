from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ix_assistant_core.models import DecodedIntent, IntentKind, Transcript, new_id
from ix_gabriella_brain.models import CognitivePacket, DecisionStatus


@dataclass(frozen=True, slots=True)
class BrainBridgeResult:
    """Normalized bridge from IX-Gabriella-Brain into the main assistant core."""

    intent: DecodedIntent | None
    response_override: str | None = None
    status_override: str | None = None
    receipt_summary: str = "IX-Gabriella-Brain cognitive packet created."
    brain_packet: CognitivePacket | None = None

    @property
    def packet_dict(self) -> dict[str, Any] | None:
        return None if self.brain_packet is None else self.brain_packet.to_dict()


class BrainBridge:
    """Maps brain packets into existing Gabriella action, policy, and receipt contracts."""

    def to_core_intent(self, packet: CognitivePacket, transcript: Transcript) -> BrainBridgeResult:
        route = packet.route
        decision = packet.decision
        brain_intent = route.intent
        packet_dict = packet.to_dict()

        if decision.status == DecisionStatus.NEEDS_CLARIFICATION:
            return BrainBridgeResult(
                intent=_decoded_from_brain(
                    transcript,
                    kind=_kind_from_name(brain_intent.name if brain_intent else "unknown"),
                    confidence=max(0.25, route.confidence),
                    slots=_slots_from_brain(brain_intent.name if brain_intent else "unknown", brain_intent.slots if brain_intent else {}, transcript.text),
                    reasons=("brain-needs-clarification", route.reason),
                    brain_packet=packet_dict,
                ),
                response_override=decision.user_message,
                status_override="waiting_for_clarification",
                brain_packet=packet,
            )

        if decision.status == DecisionStatus.PROPOSED_PLAN:
            slots = {
                "brain_packet_id": packet.packet_id,
                "brain_route": route.route.value,
                "brain_status": decision.status.value,
                "plan_steps": [step.to_dict() for step in decision.plan],
                "worldtwin": packet.worldtwin.to_dict(),
                "assurance": packet.assurance.to_dict(),
                "original_text": transcript.text,
            }
            return BrainBridgeResult(
                intent=_decoded_from_brain(
                    transcript,
                    kind=IntentKind.BRAIN_PLAN,
                    confidence=route.confidence,
                    slots=slots,
                    reasons=("brain-lane", route.reason),
                    brain_packet=packet_dict,
                ),
                response_override=decision.user_message,
                status_override="completed",
                brain_packet=packet,
            )

        if brain_intent is None:
            return BrainBridgeResult(
                intent=_decoded_from_brain(
                    transcript,
                    kind=IntentKind.UNKNOWN,
                    confidence=route.confidence,
                    slots={"original_text": transcript.text, "brain_packet_id": packet.packet_id},
                    reasons=("brain-no-fast-intent", route.reason),
                    brain_packet=packet_dict,
                ),
                response_override=decision.user_message if decision.user_message else None,
                brain_packet=packet,
            )

        name = brain_intent.name
        return BrainBridgeResult(
            intent=_decoded_from_brain(
                transcript,
                kind=_kind_from_name(name),
                confidence=brain_intent.confidence,
                slots=_slots_from_brain(name, brain_intent.slots, transcript.text, packet),
                reasons=("brain-intent", route.reason, *brain_intent.evidence),
                brain_packet=packet_dict,
            ),
            brain_packet=packet,
        )


def _decoded_from_brain(
    transcript: Transcript,
    *,
    kind: IntentKind,
    confidence: float,
    slots: dict[str, Any],
    reasons: tuple[str, ...],
    brain_packet: dict[str, Any] | None,
) -> DecodedIntent:
    clean_confidence = max(0.0, min(1.0, confidence))
    merged_slots: dict[str, Any] = dict(slots)
    if brain_packet is not None:
        merged_slots["brain"] = {
            "packet_id": brain_packet["packet_id"],
            "route": brain_packet["route"]["route"],
            "decision_status": brain_packet["decision"]["status"],
            "receipt_hash": brain_packet["receipt_hash"],
        }
    return DecodedIntent(
        intent_id=new_id("intent"),
        kind=kind,
        raw_text=transcript.text,
        normalized_text=transcript.text.lower().strip(),
        confidence=round(clean_confidence, 6),
        uncertainty=round(max(0.0, 1.0 - clean_confidence), 6),
        target="ix-gabriella-brain",
        slots=merged_slots,
        reasons=tuple(reason for reason in reasons if reason),
    )


def _kind_from_name(name: str) -> IntentKind:
    return {
        "set_timer": IntentKind.SET_TIMER,
        "create_reminder": IntentKind.SET_REMINDER,
        "take_note": IntentKind.CREATE_NOTE,
        "add_list_item": IntentKind.ADD_TO_LIST,
        "memory_proposal": IntentKind.MEMORY_WRITE,
        "email_draft": IntentKind.EMAIL_DRAFT,
        "calendar_draft": IntentKind.CALENDAR_DRAFT,
        "search_request": IntentKind.WEB_SEARCH,
        "smart_home_stage": IntentKind.SMART_HOME_CONTROL,
        "approve_pending": IntentKind.SAFETY_STOP,
        "reject_pending": IntentKind.SAFETY_STOP,
        "correct_pending": IntentKind.SAFETY_STOP,
    }.get(name, IntentKind.UNKNOWN)


def _slots_from_brain(
    name: str,
    brain_slots: dict[str, Any],
    raw_text: str,
    packet: CognitivePacket | None = None,
) -> dict[str, Any]:
    slots: dict[str, Any] = {"original_text": raw_text}
    if name == "set_timer":
        duration = brain_slots.get("duration", {})
        if isinstance(duration, dict):
            amount = duration.get("amount", 5)
            unit = duration.get("unit", "minutes")
            slots["duration_value"] = int(float(amount))
            slots["duration_unit"] = str(unit)
    elif name == "create_reminder":
        slots["reminder_text"] = str(brain_slots.get("task") or raw_text)
        if brain_slots.get("time_hint"):
            slots["time_hint"] = str(brain_slots["time_hint"])
    elif name == "take_note":
        slots["content"] = str(brain_slots.get("note") or raw_text)
    elif name == "add_list_item":
        slots["item"] = str(brain_slots.get("item") or raw_text)
        slots["list_name"] = str(brain_slots.get("list") or "default")
    elif name == "memory_proposal":
        slots["memory_text"] = str(brain_slots.get("memory") or raw_text)
        if packet and packet.decision.memory_candidate:
            slots["quarantined_memory_id"] = packet.decision.memory_candidate.memory_id
    elif name == "email_draft":
        slots["recipient_hint"] = str(brain_slots.get("recipient") or "unresolved recipient")
        slots["draft_body"] = str(brain_slots.get("body") or raw_text)
        slots["draft_only"] = True
    elif name == "calendar_draft":
        slots["event_text"] = str(brain_slots.get("event") or raw_text)
        slots["draft_only"] = True
    elif name == "search_request":
        slots["query"] = str(brain_slots.get("query") or raw_text)
    elif name == "smart_home_stage":
        slots["requested_state"] = str(brain_slots.get("state") or "unresolved state")
        slots["device"] = str(brain_slots.get("device") or "unresolved device")
    else:
        slots.update(brain_slots)
    return slots
