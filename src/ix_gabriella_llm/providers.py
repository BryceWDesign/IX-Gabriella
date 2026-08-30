from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from .models import LLMProviderMode, LLMRequest, LLMResponse


class LLMProviderError(RuntimeError):
    pass


class LLMProvider(Protocol):
    mode: LLMProviderMode

    def generate(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError


@dataclass(slots=True)
class LocalGabriellaProvider:
    """Deterministic no-key language layer for offline IX-Gabriella operation."""

    mode: LLMProviderMode = LLMProviderMode.LOCAL_GABRIELLA

    def generate(self, request: LLMRequest) -> LLMResponse:
        packet = request.brain_packet
        route = packet.get("route", {})
        decision = packet.get("decision", {})
        route_name = str(route.get("route", "brain_lane"))
        decision_status = str(decision.get("status", "proposed_plan"))
        content = _local_content(request.user_text, packet)
        flags: list[str] = []
        if route_name == "approval_lane" or decision_status == "needs_approval":
            flags.append("approval_required_before_effect")
        if route_name == "brain_lane":
            flags.append("plan_only_no_external_execution")
        return LLMResponse(
            mode=self.mode,
            content=content,
            confidence=0.74 if route_name == "brain_lane" else 0.68,
            proposed_tools=("draft_response", "propose_plan") if route_name == "brain_lane" else ("draft_response",),
            safety_flags=tuple(flags),
            raw={"local_reasoner": "ix_gabriella_deterministic"},
        )


@dataclass(slots=True)
class OpenAICompatibleLLMProvider:
    """OpenAI-compatible chat-completions client configured only through environment variables."""

    endpoint_env: str = "IX_GABRIELLA_LLM_ENDPOINT"
    api_key_env: str = "IX_GABRIELLA_LLM_API_KEY"
    model_env: str = "IX_GABRIELLA_LLM_MODEL"
    timeout_seconds: float = 40.0
    mode: LLMProviderMode = LLMProviderMode.OPENAI_COMPATIBLE

    def generate(self, request: LLMRequest) -> LLMResponse:
        endpoint = os.environ.get(self.endpoint_env, "").strip()
        model = os.environ.get(self.model_env, "").strip()
        api_key = os.environ.get(self.api_key_env, "").strip()
        if not endpoint or not model:
            raise LLMProviderError("IX_GABRIELLA_LLM_ENDPOINT and IX_GABRIELLA_LLM_MODEL are required")
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "user_text": request.user_text,
                            "brain_packet": request.brain_packet,
                            "allowed_tools": list(request.allowed_tools),
                            "blocked_effects": list(request.blocked_effects),
                        },
                        sort_keys=True,
                    ),
                },
            ],
            "temperature": request.temperature,
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        http_request = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(http_request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise LLMProviderError(f"LLM provider request failed: {exc}") from exc
        try:
            decoded = json.loads(raw)
            content = decoded["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise LLMProviderError("LLM provider returned an unsupported response shape") from exc
        return _response_from_content(content, decoded)


@dataclass(slots=True)
class DisabledLLMProvider:
    mode: LLMProviderMode = LLMProviderMode.DISABLED

    def generate(self, request: LLMRequest) -> LLMResponse:
        del request
        return LLMResponse(
            mode=self.mode,
            content="",
            confidence=0.0,
            safety_flags=("llm_disabled",),
        )


def build_provider_from_env() -> LLMProvider:
    mode = os.environ.get("IX_GABRIELLA_LLM_MODE", "local_gabriella").strip().lower()
    if mode == "openai_compatible":
        return OpenAICompatibleLLMProvider()
    if mode == "disabled":
        return DisabledLLMProvider()
    return LocalGabriellaProvider()


def _response_from_content(content: object, raw: dict[str, object]) -> LLMResponse:
    text = " ".join(str(content).strip().split())
    proposed_tools: tuple[str, ...] = ()
    safety_flags: tuple[str, ...] = ()
    confidence = 0.70
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            text = " ".join(str(parsed.get("content", text)).strip().split())
            proposed_raw = parsed.get("proposed_tools", ())
            if isinstance(proposed_raw, list):
                proposed_tools = tuple(str(item) for item in proposed_raw)
            flags_raw = parsed.get("safety_flags", ())
            if isinstance(flags_raw, list):
                safety_flags = tuple(str(item) for item in flags_raw)
            if isinstance(parsed.get("confidence"), int | float):
                confidence = float(parsed["confidence"])
    except json.JSONDecodeError:
        pass
    if not text:
        raise LLMProviderError("LLM provider returned empty content")
    return LLMResponse(
        mode=LLMProviderMode.OPENAI_COMPATIBLE,
        content=text,
        confidence=confidence,
        proposed_tools=proposed_tools,
        safety_flags=safety_flags,
        raw={"provider_response": raw},
    )


def _local_content(user_text: str, packet: dict[str, object]) -> str:
    decision = packet.get("decision", {}) if isinstance(packet.get("decision"), dict) else {}
    route = packet.get("route", {}) if isinstance(packet.get("route"), dict) else {}
    route_name = str(route.get("route", "brain_lane"))
    if decision.get("status") == "needs_clarification":
        return str(decision.get("user_message") or "I need one more detail before I handle that correctly.")
    if route_name == "approval_lane" or decision.get("status") == "needs_approval":
        message = str(decision.get("approval_question") or decision.get("user_message") or "Please approve before I act.")
        return f"I heard the request. {message}"
    plan = decision.get("plan") if isinstance(decision.get("plan"), list) else []
    if plan:
        titles = [str(step.get("title", "Review step")) for step in plan if isinstance(step, dict)]
        joined = "; ".join(f"{i}. {title}" for i, title in enumerate(titles, start=1))
        return (
            "IX-Gabriella-Brain treated this as a complex request and built a reviewable plan. "
            f"{joined}. I have not executed external actions."
        )
    return (
        "I can help with that, but I will keep it inside the governed assistant path: "
        "interpret, check uncertainty, ask if needed, and record a receipt."
    )
