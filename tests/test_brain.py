from pathlib import Path

from ix_gabriella_brain import GabriellaBrain
from ix_gabriella_brain.models import DecisionStatus, RouteKind


def test_brain_executes_low_risk_timer(tmp_path: Path) -> None:
    brain = GabriellaBrain(state_path=tmp_path / "state.json", receipt_path=tmp_path / "receipts.jsonl")
    packet = brain.think("set a timer for 10 minutes")
    assert packet.route.route == RouteKind.FAST_LANE
    assert packet.decision.status == DecisionStatus.EXECUTED_LOCAL
    assert brain.state_repo.state.timers
    assert packet.assurance.passed


def test_brain_saves_local_note(tmp_path: Path) -> None:
    brain = GabriellaBrain(state_path=tmp_path / "state.json")
    packet = brain.think("take a note that receipts must be checked")
    assert packet.decision.status == DecisionStatus.EXECUTED_LOCAL
    assert brain.state_repo.state.notes[0]["slots"]["note"] == "receipts must be checked"


def test_brain_adds_list_item(tmp_path: Path) -> None:
    brain = GabriellaBrain(state_path=tmp_path / "state.json")
    packet = brain.think("add milk to my grocery list")
    assert packet.decision.status == DecisionStatus.EXECUTED_LOCAL
    assert brain.state_repo.state.lists["grocery"] == ["milk"]


def test_brain_clarifies_missing_reminder_time(tmp_path: Path) -> None:
    brain = GabriellaBrain(state_path=tmp_path / "state.json")
    packet = brain.think("remind me to check the build")
    assert packet.decision.status == DecisionStatus.NEEDS_CLARIFICATION
    assert packet.decision.needs_user_input


def test_brain_stages_memory_for_approval(tmp_path: Path) -> None:
    brain = GabriellaBrain(state_path=tmp_path / "state.json")
    packet = brain.think("remember that I prefer short replies")
    assert packet.decision.status == DecisionStatus.NEEDS_APPROVAL
    assert packet.decision.memory_candidate is not None
    assert packet.packet_id in brain.state_repo.state.pending


def test_brain_plans_complex_goal(tmp_path: Path) -> None:
    brain = GabriellaBrain(state_path=tmp_path / "state.json")
    packet = brain.think("help me prepare for tomorrow's meeting with a reviewable plan")
    assert packet.route.route == RouteKind.BRAIN_LANE
    assert packet.decision.status == DecisionStatus.PROPOSED_PLAN
    assert len(packet.decision.plan) >= 5
    assert packet.worldtwin.verdict == "reviewable"


def test_approval_flow_records_receipt(tmp_path: Path) -> None:
    brain = GabriellaBrain(state_path=tmp_path / "state.json")
    packet = brain.think("draft an email to Sarah saying I am late")
    result = brain.approve(packet.packet_id)
    assert result["approved"] is True
    assert "receipt_hash" in result


def test_rejection_flow_records_receipt(tmp_path: Path) -> None:
    brain = GabriellaBrain(state_path=tmp_path / "state.json")
    packet = brain.think("turn off the kitchen lights")
    result = brain.reject(packet.packet_id)
    assert result["approved"] is False
    assert "receipt_hash" in result
