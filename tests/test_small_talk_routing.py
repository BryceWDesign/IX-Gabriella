from ix_assistant_core.assistant import GabriellaAssistant
from ix_assistant_core.models import ActionStatus, IntentKind


def test_name_question_uses_small_talk_not_brain_plan() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("tell me what your name is")
    assert turn.status == ActionStatus.COMPLETED
    assert turn.intent.kind == IntentKind.SMALL_TALK
    assert "Gabriella" in turn.response_text
    assert "prep plan" not in turn.response_text.lower()
    assert "reviewable" not in turn.response_text.lower()


def test_greeting_uses_small_talk_not_brain_plan() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("hello")
    assert turn.status == ActionStatus.COMPLETED
    assert turn.intent.kind == IntentKind.SMALL_TALK
    assert "Gabriella" in turn.response_text
    assert "prep plan" not in turn.response_text.lower()


def test_how_are_you_uses_small_talk_not_brain_plan() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("how are you")
    assert turn.status == ActionStatus.COMPLETED
    assert turn.intent.kind == IntentKind.SMALL_TALK
    assert "Gabriella" in turn.response_text


def test_small_talk_responses_are_context_specific() -> None:
    assistant = GabriellaAssistant.default()

    greeting = assistant.handle_text("hello")
    assert greeting.intent.kind == IntentKind.SMALL_TALK
    assert "What would you like me to help with" in greeting.response_text

    name = assistant.handle_text("what is your name?")
    assert name.intent.kind == IntentKind.SMALL_TALK
    assert "assistant persona" in name.response_text

    status = assistant.handle_text("how are you?")
    assert status.intent.kind == IntentKind.SMALL_TALK
    assert "running locally" in status.response_text
    assert "assistant persona" not in status.response_text
