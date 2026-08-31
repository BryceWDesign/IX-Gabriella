from ix_assistant_core.assistant import GabriellaAssistant
from ix_assistant_core.models import ActionStatus, IntentKind


def test_plain_help_stays_show_help() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("help")
    assert turn.status == ActionStatus.COMPLETED
    assert turn.intent.kind == IntentKind.SHOW_HELP


def test_capabilities_question_stays_show_help() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("what can you do?")
    assert turn.status == ActionStatus.COMPLETED
    assert turn.intent.kind == IntentKind.SHOW_HELP


def test_help_me_prepare_routes_to_brain_plan() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("Help me prepare for tomorrow's meeting with a plan and questions")
    assert turn.status == ActionStatus.COMPLETED
    assert turn.intent.kind == IntentKind.BRAIN_PLAN
    assert "show help" not in turn.plan.summary.lower()


def test_help_me_compare_launch_paths_routes_to_completed_brain_plan() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("Help me compare launch paths for a privacy first virtual assistant and build a plan")
    assert turn.status == ActionStatus.COMPLETED
    assert turn.intent.kind == IntentKind.BRAIN_PLAN
    assert "reviewable" in turn.response_text.lower()
