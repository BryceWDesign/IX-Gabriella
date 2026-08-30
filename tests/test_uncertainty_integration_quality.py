from pathlib import Path

from ix_gabriella_brain import GabriellaBrain
from ix_gabriella_brain.fast_intents import FastIntentRegistry
from ix_gabriella_brain.integrations.gabriella_core import GabriellaBrainAdapter
from ix_gabriella_brain.models import RiskLevel
from ix_gabriella_brain.quality import run_quality_gate, scan_forbidden_markers
from ix_gabriella_brain.uncertainty import UncertaintyEngine


def test_uncertainty_asks_for_missing_slots() -> None:
    intent = FastIntentRegistry().match("set a timer")
    result = UncertaintyEngine().assess("set a timer", intent, RiskLevel.LOW)
    assert result.should_ask
    assert any("missing_required_slots" in reason for reason in result.reasons)


def test_uncertainty_penalizes_high_risk() -> None:
    result = UncertaintyEngine().assess("send private data", None, RiskLevel.HIGH)
    assert result.confidence < 0.58
    assert result.should_ask


def test_adapter_returns_packet_dict(tmp_path: Path) -> None:
    adapter = GabriellaBrainAdapter(GabriellaBrain(state_path=tmp_path / "state.json"))
    result = adapter.handle_user_text("set a timer for 2 minutes")
    assert result["route"] == "fast_lane"
    assert result["status"] == "executed_local"
    assert "brain_packet" in result


def test_quality_gate_runs(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = run_quality_gate(repo)
    assert result["compile_passed"]
    assert result["overall_passed"]


def test_forbidden_marker_scan_empty() -> None:
    repo = Path(__file__).resolve().parents[1]
    assert scan_forbidden_markers(repo) == ()
