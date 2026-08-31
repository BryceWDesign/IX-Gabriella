from ix_assistant_core.assistant import GabriellaAssistant
from ix_assistant_core.models import IntentKind


def test_answer_question_does_not_use_brain_plan_text() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("How many cities are in Arizona?")
    assert turn.intent.kind == IntentKind.ANSWER_QUESTION
    assert "verified knowledge connector" in turn.response_text
    assert "reviewable prep plan" not in turn.response_text.lower()
    assert "draft an agenda" not in turn.response_text.lower()


def test_time_question_gets_local_time_response() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("what time is it?")
    assert turn.intent.kind == IntentKind.ANSWER_QUESTION
    assert "local time" in turn.response_text.lower()
    assert "reviewable prep plan" not in turn.response_text.lower()


def test_day_question_gets_local_date_response() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("do you know what day this is?")
    assert turn.intent.kind == IntentKind.ANSWER_QUESTION
    assert "Today is" in turn.response_text
    assert "reviewable prep plan" not in turn.response_text.lower()
