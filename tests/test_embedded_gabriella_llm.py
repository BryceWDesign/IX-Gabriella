from __future__ import annotations

import json
from pathlib import Path

from ix_gabriella_brain import GabriellaBrain
from ix_gabriella_llm import EmbeddedGabriellaMicroLM, GabriellaLLMEngine, LLMProviderMode
from ix_gabriella_llm.models import LLMRequest
from ix_gabriella_llm.providers import EmbeddedGabriellaMicroProvider, build_provider_from_env
from ix_gabriella_llm.tool_schemas import allowed_tool_names


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "src" / "ix_gabriella_llm" / "data" / "ix_gabriella_micro_lm.json"


def test_embedded_model_artifact_exists_and_is_real() -> None:
    assert MODEL_PATH.exists()
    artifact = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    assert artifact["name"] == "IX-Gabriella-LLM-Micro"
    assert artifact["author"] == "Bryce Lovell"
    assert artifact["training_examples"] >= 20
    assert artifact["metadata"]["vocabulary_size"] > 50
    assert len(artifact["trigram_logprob"]) > 50
    assert artifact["artifact_sha256"]


def test_embedded_model_loads_and_scores_candidates() -> None:
    model = EmbeddedGabriellaMicroLM.load()
    selected = model.select_response(
        user_text="help me prepare for tomorrow's meeting",
        route="brain_lane",
        status="proposed_plan",
        missing_slots=(),
    )
    assert selected.score < 0
    assert "plan" in selected.tags
    assert "reviewable" in selected.response.lower() or "plan" in selected.response.lower()


def test_embedded_provider_returns_structured_output() -> None:
    brain = GabriellaBrain(execute_fast_locally=False)
    packet = brain.think(
        "remember that I prefer concise meeting prep",
        user_id="test-user",
        channel="test",
        session_id="embedded-test",
    ).to_dict()
    provider = EmbeddedGabriellaMicroProvider()
    response = provider.generate(
        LLMRequest(
            user_text="remember that I prefer concise meeting prep",
            system_prompt="Return structured JSON.",
            brain_packet=packet,
            allowed_tools=allowed_tool_names(),
        )
    )
    assert response.mode == LLMProviderMode.EMBEDDED_TINY
    assert response.raw["embedded_model"] == "ix-gabriella-llm-micro-v0.1.0"
    assert response.raw["vocabulary_size"] > 50
    assert response.structured["requires_user_approval"] is True
    assert "embedded_model_loaded" in response.safety_flags


def test_engine_can_use_embedded_model_without_external_service(monkeypatch) -> None:
    monkeypatch.setenv("IX_GABRIELLA_LLM_MODE", "embedded_tiny")
    provider = build_provider_from_env()
    assert provider.mode == LLMProviderMode.EMBEDDED_TINY
    brain = GabriellaBrain(execute_fast_locally=False)
    packet = brain.think(
        "help me compare two product ideas and recommend a path",
        user_id="test-user",
        channel="test",
        session_id="engine-embedded-test",
    ).to_dict()
    result = GabriellaLLMEngine(provider=provider).deliberate(
        user_text="help me compare two product ideas and recommend a path",
        brain_packet=packet,
    )
    assert result.consulted is True
    assert result.provider_mode == LLMProviderMode.EMBEDDED_TINY
    assert result.structured_valid is True
    assert result.response_text is not None
    assert "plan" in result.response_text.lower() or "compare" in result.response_text.lower()
