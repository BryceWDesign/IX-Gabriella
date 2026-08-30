import json
from pathlib import Path

from ix_gabriella_brain.brain import GabriellaBrain
from ix_gabriella_brain.cli import main
from ix_gabriella_brain.storage import BrainState, StateRepository


def test_state_repository_persists(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    repo = StateRepository(path)
    repo.state.commit_local("take_note", {"note": "persist me"})
    repo.save()
    loaded = StateRepository(path)
    assert loaded.state.notes[0]["slots"]["note"] == "persist me"


def test_brain_state_stage_and_approve() -> None:
    state = BrainState()
    state.stage_pending("p1", {"intent": "email_draft"})
    approved = state.approve_pending("p1")
    assert approved["approved"] is True
    assert not state.pending


def test_brain_state_stage_and_reject() -> None:
    state = BrainState()
    state.stage_pending("p1", {"intent": "email_draft"})
    rejected = state.reject_pending("p1")
    assert rejected["approved"] is False
    assert not state.pending


def test_cli_plain_text(tmp_path: Path, capsys) -> None:
    code = main(["--state", str(tmp_path / "state.json"), "set", "a", "timer", "for", "1", "minute"])
    out = capsys.readouterr().out
    assert code == 0
    assert "route=fast_lane" in out


def test_cli_json_output(tmp_path: Path, capsys) -> None:
    code = main(["--state", str(tmp_path / "state.json"), "--json", "help", "me", "prepare", "for", "a", "meeting"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert code == 0
    assert data["decision"]["status"] == "proposed_plan"


def test_packet_contains_receipt_hash(tmp_path: Path) -> None:
    brain = GabriellaBrain(state_path=tmp_path / "state.json")
    packet = brain.think("add water to my grocery list")
    assert len(packet.receipt_hash) == 64
