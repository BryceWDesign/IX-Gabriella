from datetime import date

from ix_assistant_core.assistant import GabriellaAssistant
from ix_assistant_core.models import ActionStatus, IntentKind


def test_this_does_not_trigger_hi_small_talk() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("do you know what day this is?")
    assert turn.status == ActionStatus.COMPLETED
    assert turn.intent.kind == IntentKind.ANSWER_QUESTION
    assert date.today().strftime("%A") in turn.response_text
    assert "prep plan" not in turn.response_text.lower()


def test_broad_factual_question_does_not_become_brain_plan() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("How many cities are in Arizona?")
    assert turn.status == ActionStatus.COMPLETED
    assert turn.intent.kind == IntentKind.ANSWER_QUESTION
    assert "verified knowledge connector" in turn.response_text
    assert "prep plan" not in turn.response_text.lower()
    assert "reviewable" not in turn.response_text.lower()


def test_complex_how_question_can_still_use_brain_lane() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("How should I plan and launch a virtual assistant product?")
    assert turn.status == ActionStatus.COMPLETED
    assert turn.intent.kind == IntentKind.BRAIN_PLAN
