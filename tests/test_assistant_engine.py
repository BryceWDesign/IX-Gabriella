from ix_assistant_core.assistant import GabriellaAssistant
from ix_assistant_core.models import ActionStatus


def test_timer_turn_completes_with_receipts() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("Hey Gabriella set a timer for 5 minutes")
    assert turn.status == ActionStatus.COMPLETED
    assert "Timer set locally" in turn.response_text
    assert len(assistant.local_store.list_records(kind="timer")) == 1
    assert len(turn.receipt_ids) >= 5
    assert assistant.receipts.verify_intent_chain(turn.intent.intent_id)


def test_smart_home_command_requires_visible_confirmation() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("turn off the kitchen lights")
    assert turn.status == ActionStatus.WAITING_FOR_CONFIRMATION
    assert "I heard:" in turn.response_text
    assert "Confirm before I act" in turn.response_text


def test_confirmed_email_still_only_drafts() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("email Sam that I will be late")
    assert turn.status == ActionStatus.WAITING_FOR_CONFIRMATION
    confirmed = assistant.confirm(turn, "yes confirm")
    assert confirmed.status == ActionStatus.COMPLETED
    assert "will not send" in confirmed.response_text


def test_memory_is_saved_only_after_confirmation() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("remember that I prefer quiet mode")
    assert turn.status == ActionStatus.WAITING_FOR_CONFIRMATION
    confirmed = assistant.confirm(turn, "approve")
    assert confirmed.status == ActionStatus.COMPLETED
    assert len(assistant.memory.list()) == 1


def test_rejected_action_does_not_execute() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("turn off the kitchen lights")
    rejected = assistant.confirm(turn, "no cancel")
    assert rejected.status == ActionStatus.BLOCKED
    assert "Canceled" in rejected.response_text
