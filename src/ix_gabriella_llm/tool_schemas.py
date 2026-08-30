from __future__ import annotations

from typing import Any

SAFE_TOOL_SCHEMAS: tuple[dict[str, Any], ...] = (
    {
        "name": "draft_response",
        "description": "Draft user-facing language only. No external side effects.",
        "risk": "low",
        "approval_required": False,
    },
    {
        "name": "request_clarification",
        "description": "Ask the user for one missing detail.",
        "risk": "low",
        "approval_required": False,
    },
    {
        "name": "propose_plan",
        "description": "Create a reviewable plan. No external side effects.",
        "risk": "low_to_medium",
        "approval_required": False,
    },
    {
        "name": "stage_action_preview",
        "description": "Describe a possible action for later approval by the core assistant.",
        "risk": "medium",
        "approval_required": True,
    },
)

BLOCKED_LLM_EFFECTS: tuple[str, ...] = (
    "send_email",
    "send_message",
    "modify_calendar",
    "purchase_item",
    "transfer_money",
    "unlock_door",
    "delete_account",
    "write_long_term_memory_without_approval",
    "control_smart_home_device_directly",
)


def allowed_tool_names() -> tuple[str, ...]:
    return tuple(schema["name"] for schema in SAFE_TOOL_SCHEMAS)
