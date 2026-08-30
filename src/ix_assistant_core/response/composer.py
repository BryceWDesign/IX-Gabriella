from __future__ import annotations

from ix_assistant_core.identity import ASSISTANT_NAME, PRODUCT_PROMISE, PROJECT_NAME
from ix_assistant_core.models import DecodedIntent, IntentKind


class ResponseComposer:
    """Deterministic local response composer for no-key operation."""

    def answer(self, intent: DecodedIntent) -> str:
        text = intent.normalized_text
        if intent.kind == IntentKind.SHOW_HELP:
            return self.capabilities()
        if intent.kind == IntentKind.SMALL_TALK:
            return (
                f"I am {ASSISTANT_NAME}. I can listen, show what I heard, "
                "ask before risky actions, and keep receipts."
            )
        if "your name" in text or "who are you" in text:
            return f"I am {ASSISTANT_NAME}, the assistant persona for {PROJECT_NAME}."
        if "what can you do" in text or "help" in text:
            return self.capabilities()
        if "privacy" in text:
            return (
                "Memory is approval-based. You can review it, clear it, or keep it off. "
                "Private voice content should not be used for creepy ad targeting."
            )
        if "receipt" in text or "receipts" in text:
            return (
                "Every meaningful step can be recorded as a tamper-evident receipt: "
                "transcript, decoded intent, policy result, approval, and action result."
            )
        if "why" in text and "ask" in text and "act" in text:
            return f"Because {PRODUCT_PROMISE}. Decoded intent is a proposal, not permission."
        if text.endswith("?") or intent.kind == IntentKind.ANSWER_QUESTION:
            return (
                "I can answer simple local questions now. For broad web knowledge "
                "or ChatGPT-level reasoning, connect a reviewed model provider behind "
                "the same policy gate."
            )
        return self.capabilities()

    def capabilities(self) -> str:
        return (
            "I can handle typed or spoken input in the local GUI, set local timers, "
            "save notes, add list items, draft reminders, prepare email/calendar drafts, "
            "stage smart-home commands for later integration, manage approved memory, "
            "and show receipts before and after important actions."
        )
