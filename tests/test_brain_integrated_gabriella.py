from ix_assistant_core.assistant import GabriellaAssistant
from ix_assistant_core.models import ActionStatus, IntentKind


def test_main_assistant_uses_brain_packet_for_fast_timer() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("Hey Gabriella set a timer for 7 minutes")
    assert turn.status == ActionStatus.COMPLETED
    assert turn.intent.kind == IntentKind.SET_TIMER
    assert turn.brain_packet is not None
    assert turn.brain_packet["route"]["route"] == "fast_lane"
    assert len(assistant.local_store.list_records(kind="timer")) == 1


def test_main_assistant_routes_complex_goal_to_brain_plan() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("Help me prepare for tomorrow's meeting with a plan and questions")
    assert turn.status == ActionStatus.COMPLETED
    assert turn.intent.kind == IntentKind.BRAIN_PLAN
    assert turn.brain_packet is not None
    assert turn.brain_packet["route"]["route"] == "brain_lane"
    assert "IX-Gabriella-Brain" in turn.response_text
    assert "No external action" in turn.plan.preview


def test_brain_clarification_does_not_execute_missing_timer() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("set a timer")
    assert turn.status == ActionStatus.WAITING_FOR_CLARIFICATION
    assert "duration" in turn.response_text
    assert not assistant.local_store.list_records(kind="timer")
