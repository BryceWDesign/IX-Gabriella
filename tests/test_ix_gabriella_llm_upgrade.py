from __future__ import annotations

from pathlib import Path

from ix_assistant_core.assistant import GabriellaAssistant
from ix_gabriella_brain import GabriellaBrain
from ix_gabriella_llm import GabriellaLLMEngine, LLMProviderMode, LLMRequest, LLMResponse
from ix_gabriella_llm.correction_learning import CorrectionStore
from ix_gabriella_llm.memory_retrieval import lexical_memory_hits
from ix_gabriella_llm.providers import FallbackLLMProvider, LocalGabriellaProvider, LLMProviderError, OllamaLLMProvider
from ix_gabriella_llm.structured import deterministic_repair, validate_structured_output
from ix_gabriella_llm.tool_schemas import allowed_tool_names


class BadProvider:
    mode = LLMProviderMode.OPENAI_COMPATIBLE

    def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            mode=self.mode,
            content='{"assistant_response":"sent it","confidence":0.9,"risk":"high","requested_tool":"send_email","requires_user_approval":false,"memory_write_requested":false}',
            confidence=0.9,
            proposed_tools=("send_email",),
        )


class ErrorProvider:
    mode = LLMProviderMode.OPENAI_COMPATIBLE

    def generate(self, request: LLMRequest) -> LLMResponse:
        raise LLMProviderError("network down")


def _request(text: str = "help me prepare for a meeting") -> LLMRequest:
    brain = GabriellaBrain(execute_fast_locally=False)
    packet = brain.think(text, user_id="u", channel="test", session_id="s")
    return LLMRequest(
        user_text=text,
        system_prompt="system",
        brain_packet=packet.to_dict(),
        allowed_tools=allowed_tool_names(),
        blocked_effects=("send_email",),
    )


def test_structured_output_contract_accepts_valid_packet() -> None:
    text = '{"assistant_response":"I can plan that.","confidence":0.81,"risk":"medium","requested_tool":"propose_plan","requires_user_approval":false,"memory_write_requested":false}'
    result = validate_structured_output(text, allowed_tools=allowed_tool_names())
    assert result.valid
    assert result.packet["assistant_response"] == "I can plan that."


def test_structured_output_repair_is_deterministic() -> None:
    result = deterministic_repair("I can help with that.", allowed_tools=allowed_tool_names())
    assert result.valid
    assert result.repaired
    assert result.packet["requires_user_approval"] is True


def test_llm_rejects_unapproved_tool_attempt() -> None:
    result = GabriellaLLMEngine(provider=BadProvider()).deliberate(
        user_text="send email to Sam",
        brain_packet=_request("send email to Sam").brain_packet,
    )
    assert result.response_text is None
    assert result.blocked_tool_attempts == ("send_email",)
    assert "blocked_llm_tool_attempt" in result.safety_flags


def test_fallback_provider_uses_local_when_primary_errors() -> None:
    provider = FallbackLLMProvider(ErrorProvider(), LocalGabriellaProvider())
    response = provider.generate(_request())
    assert response.mode == LLMProviderMode.FALLBACK
    assert "primary_provider_fallback_used" in response.safety_flags


def test_correction_store_persists_and_retrieves(tmp_path: Path) -> None:
    store = CorrectionStore(tmp_path / "corrections.json")
    store.add(original="set timer for tree minutes", corrected="set timer for three minutes")
    again = CorrectionStore(tmp_path / "corrections.json")
    assert again.examples_for("timer three")[0].corrected == "set timer for three minutes"


def test_memory_retrieval_returns_relevant_hits() -> None:
    hits = lexical_memory_hits("meeting with alex tomorrow", ("Alex prefers morning meetings", "Buy milk"))
    assert hits
    assert "Alex" in hits[0].text


def test_assistant_persistent_llm_records_correction(tmp_path: Path) -> None:
    assistant = GabriellaAssistant.default(state_dir=tmp_path, persist=True)
    turn = assistant.handle_text("email bryce that I will be late")
    assistant.correct(turn, "draft an email saying I will be late")
    assert (tmp_path / "llm_corrections.json").exists()


def test_ollama_provider_defaults_to_local_endpoint(monkeypatch) -> None:
    monkeypatch.setenv("IX_GABRIELLA_OLLAMA_MODEL", "test-model")
    provider = OllamaLLMProvider()
    assert provider.mode == LLMProviderMode.OLLAMA
