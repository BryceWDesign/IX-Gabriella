from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from ix_assistant_core.assistant import GabriellaAssistant
from ix_assistant_core.models import ActionStatus, IntentKind
from ix_gabriella_llm import GabriellaLLMEngine
from ix_gabriella_llm.deliberation import GabriellaLLMEngine as Engine
from ix_gabriella_llm.models import LLMProviderMode, LLMRequest, LLMResponse
from ix_gabriella_llm.providers import OpenAICompatibleLLMProvider


class UnsafeProvider:
    mode = LLMProviderMode.LOCAL_GABRIELLA

    def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            mode=self.mode,
            content="I sent it.",
            confidence=0.95,
            proposed_tools=("send_email",),
        )


class _LLMHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length).decode("utf-8"))
        assert body["model"] == "gabriella-test-model"
        assert "Brain proposes" in body["messages"][0]["content"]
        data = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "content": "Provider deliberation accepted.",
                                    "confidence": 0.83,
                                    "proposed_tools": ["draft_response"],
                                }
                            )
                        }
                    }
                ]
            }
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def test_fast_lane_does_not_invoke_language_model() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("Hey Gabriella set a timer for 4 minutes")
    assert turn.status == ActionStatus.COMPLETED
    assert turn.intent.kind == IntentKind.SET_TIMER
    assert turn.brain_packet is not None
    assert turn.brain_packet["llm"]["consulted"] is False
    assert turn.brain_packet["llm"]["reason"] == "fast_lane_downshift_preserved"


def test_complex_request_uses_local_gabriella_llm_layer() -> None:
    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text("Help me prepare for tomorrow's meeting with a plan and questions")
    assert turn.status == ActionStatus.COMPLETED
    assert turn.intent.kind == IntentKind.BRAIN_PLAN
    assert turn.brain_packet is not None
    assert turn.brain_packet["llm"]["consulted"] is True
    assert turn.brain_packet["llm"]["provider_mode"] == "local_gabriella"
    assert "reviewable plan" in turn.response_text


def test_llm_tool_boundary_blocks_direct_side_effects() -> None:
    assistant = GabriellaAssistant.default()
    assistant.llm = GabriellaLLMEngine(provider=UnsafeProvider())
    turn = assistant.handle_text("Analyze the safest way to prepare an email workflow for John tomorrow")
    assert turn.intent.kind == IntentKind.EMAIL_DRAFT
    assert turn.status == ActionStatus.WAITING_FOR_CONFIRMATION
    assert turn.brain_packet is not None
    assert turn.brain_packet["llm"]["reason"] == "llm_deliberation_rejected_for_tool_boundary"
    assert turn.brain_packet["llm"]["blocked_tool_attempts"] == ["send_email"]
    assert "I sent it" not in turn.response_text


def test_openai_compatible_llm_provider_accepts_json_contract(monkeypatch) -> None:
    server = HTTPServer(("127.0.0.1", 0), _LLMHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        monkeypatch.setenv("IX_GABRIELLA_LLM_ENDPOINT", f"http://{host}:{port}/v1/chat/completions")
        monkeypatch.setenv("IX_GABRIELLA_LLM_MODEL", "gabriella-test-model")
        provider = OpenAICompatibleLLMProvider(timeout_seconds=5)
        response = provider.generate(
            LLMRequest(
                user_text="hello",
                system_prompt="Brain proposes. Policy decides.",
                brain_packet={"route": {"route": "brain_lane"}, "decision": {"status": "proposed_plan"}},
                allowed_tools=("draft_response",),
                blocked_effects=("send_email",),
            )
        )
        assert response.content == "Provider deliberation accepted."
        assert response.confidence == 0.83
        assert response.proposed_tools == ("draft_response",)
    finally:
        server.shutdown()
        server.server_close()
