from __future__ import annotations

from ix_assistant_core.models import ActionPlan, ActionRisk, DecodedIntent, IntentKind


class ActionPlanner:
    """Convert decoded intent into a previewable action plan."""

    def plan(self, intent: DecodedIntent) -> ActionPlan:
        risk = _risk_for(intent)
        requires_confirmation = risk in {ActionRisk.MODERATE, ActionRisk.HIGH, ActionRisk.CRITICAL}
        if intent.kind in {IntentKind.EMAIL_DRAFT, IntentKind.CALENDAR_DRAFT, IntentKind.MEMORY_WRITE}:
            requires_confirmation = True
        if intent.kind == IntentKind.SMART_HOME_CONTROL:
            requires_confirmation = True

        summary = _summary(intent)
        preview = _preview(intent, risk)
        return ActionPlan(
            intent=intent,
            risk=risk,
            summary=summary,
            preview=preview,
            requires_confirmation=requires_confirmation,
            allowed_tools=_allowed_tools(intent),
            irreversible=risk == ActionRisk.CRITICAL,
        )


def _risk_for(intent: DecodedIntent) -> ActionRisk:
    text = intent.normalized_text
    if intent.kind == IntentKind.UNKNOWN:
        return ActionRisk.HIGH
    if any(token in text for token in ("delete account", "send money", "buy ", "purchase")):
        return ActionRisk.CRITICAL
    if "unlock door" in text:
        return ActionRisk.CRITICAL
    if intent.kind in {
        IntentKind.EMAIL_DRAFT,
        IntentKind.CALENDAR_DRAFT,
        IntentKind.MEMORY_WRITE,
        IntentKind.PRIVACY_CONTROL,
    }:
        return ActionRisk.MODERATE
    if intent.kind == IntentKind.SMART_HOME_CONTROL:
        if any(token in text for token in ("lock", "unlock", "garage", "door", "oven", "stove")):
            return ActionRisk.HIGH
        return ActionRisk.MODERATE
    if intent.kind in {
        IntentKind.SET_TIMER,
        IntentKind.CREATE_NOTE,
        IntentKind.ADD_TO_LIST,
        IntentKind.ANSWER_QUESTION,
        IntentKind.SMALL_TALK,
        IntentKind.SHOW_HELP,
        IntentKind.MEMORY_READ,
        IntentKind.AD_PREFERENCE,
        IntentKind.APP_SETTINGS,
        IntentKind.SAFETY_STOP,
        IntentKind.BRAIN_PLAN,
    }:
        return ActionRisk.LOW
    return ActionRisk.MODERATE


def _summary(intent: DecodedIntent) -> str:
    labels = {
        IntentKind.UNKNOWN: "Clarify the user's request",
        IntentKind.SMALL_TALK: "Respond conversationally",
        IntentKind.SHOW_HELP: "Show assistant capabilities",
        IntentKind.ANSWER_QUESTION: "Answer a question",
        IntentKind.WEB_SEARCH: "Prepare a search request",
        IntentKind.SET_TIMER: "Set a timer",
        IntentKind.SET_REMINDER: "Create a reminder",
        IntentKind.CREATE_NOTE: "Create a local note",
        IntentKind.ADD_TO_LIST: "Add an item to a list",
        IntentKind.CALENDAR_DRAFT: "Draft a calendar event",
        IntentKind.EMAIL_DRAFT: "Draft an email or message",
        IntentKind.SMART_HOME_CONTROL: "Prepare a smart-home action",
        IntentKind.MEMORY_WRITE: "Save a memory with user approval",
        IntentKind.MEMORY_READ: "Read approved memory",
        IntentKind.PRIVACY_CONTROL: "Change privacy data controls",
        IntentKind.AD_PREFERENCE: "Change ad preference controls",
        IntentKind.APP_SETTINGS: "Change assistant settings",
        IntentKind.SAFETY_STOP: "Stop or cancel the active task",
        IntentKind.BRAIN_PLAN: "Produce a reviewable cognitive plan",
    }
    return labels[intent.kind]


def _preview(intent: DecodedIntent, risk: ActionRisk) -> str:
    if intent.kind == IntentKind.UNKNOWN:
        return "I am not confident enough to act. I should ask a clarifying question."
    if intent.kind == IntentKind.BRAIN_PLAN:
        return "IX-Gabriella-Brain will produce a plan only. No external action is executed."
    if intent.kind == IntentKind.EMAIL_DRAFT:
        return "I can draft the message, but I will not send it without explicit approval."
    if intent.kind == IntentKind.CALENDAR_DRAFT:
        return "I can draft the calendar event, but I will not invite anyone without approval."
    if intent.kind == IntentKind.SMART_HOME_CONTROL:
        return "I will repeat the device and requested state before any smart-home action."
    if intent.kind == IntentKind.MEMORY_WRITE:
        return "I can save this only after the user approves the exact memory text."
    if intent.kind == IntentKind.PRIVACY_CONTROL:
        return "I can prepare the data-control change and show what will be affected."
    if risk == ActionRisk.LOW:
        return "This is a low-risk local assistant action."
    return "This action has risk and needs review before execution."


def _allowed_tools(intent: DecodedIntent) -> tuple[str, ...]:
    mapping = {
        IntentKind.SMALL_TALK: ("local_responder",),
        IntentKind.SHOW_HELP: ("local_responder",),
        IntentKind.ANSWER_QUESTION: ("local_responder",),
        IntentKind.SET_TIMER: ("local_timer",),
        IntentKind.SET_REMINDER: ("local_reminders",),
        IntentKind.CREATE_NOTE: ("local_notes",),
        IntentKind.ADD_TO_LIST: ("local_lists",),
        IntentKind.EMAIL_DRAFT: ("email_draft",),
        IntentKind.CALENDAR_DRAFT: ("calendar_draft",),
        IntentKind.WEB_SEARCH: ("search_provider",),
        IntentKind.MEMORY_WRITE: ("approved_memory",),
        IntentKind.MEMORY_READ: ("approved_memory",),
        IntentKind.PRIVACY_CONTROL: ("privacy_controls",),
        IntentKind.AD_PREFERENCE: ("ad_controls",),
        IntentKind.APP_SETTINGS: ("assistant_settings",),
        IntentKind.BRAIN_PLAN: ("ix_gabriella_brain", "plan_only"),
    }
    return mapping.get(intent.kind, ())
