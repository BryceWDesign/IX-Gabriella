from __future__ import annotations

from .models import BrainDecision, DecisionStatus, IntentCandidate, PlanStep


class ResponseComposer:
    def compose_fast_success(self, intent: IntentCandidate, action: dict[str, object]) -> str:
        if intent.name == "set_timer":
            duration = intent.slots.get("duration", {})
            return f"Timer staged locally for {duration.get('amount')} {duration.get('unit')}."
        if intent.name == "create_reminder":
            return f"Reminder saved locally: {intent.slots.get('task')} ({intent.slots.get('time_hint')})."
        if intent.name == "take_note":
            return "Note saved locally."
        if intent.name == "add_list_item":
            return f"Added {intent.slots.get('item')} to your {intent.slots.get('list')} list."
        return "Local low-risk task completed."

    def compose_clarification(self, intent: IntentCandidate | None) -> str:
        if intent and intent.missing_slots:
            readable = ", ".join(intent.missing_slots)
            return f"I recognized the task, but I need: {readable}."
        return "I need one more detail before I can handle that correctly."

    def compose_approval(self, intent: IntentCandidate, action: dict[str, object]) -> str:
        return f"I can stage this as {intent.name}. Please approve before I treat it as authorized."

    def compose_plan(self, steps: tuple[PlanStep, ...]) -> str:
        titles = "; ".join(f"{index}. {step.title}" for index, step in enumerate(steps, start=1))
        return f"I routed this to IX-Gabriella-Brain and produced a reviewable plan: {titles}."

    def compose_decision(self, decision: BrainDecision) -> str:
        if decision.status == DecisionStatus.NEEDS_APPROVAL and decision.approval_question:
            return decision.approval_question
        return decision.user_message
