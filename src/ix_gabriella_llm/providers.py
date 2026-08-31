from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from .embedded import EmbeddedGabriellaMicroLM
from .models import LLMProviderMode, LLMRequest, LLMResponse
from .structured import deterministic_repair, validate_structured_output


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
        structured = {
            "assistant_response": content,
            "confidence": 0.74 if route_name == "brain_lane" else 0.68,
            "risk": "medium" if route_name in {"brain_lane", "approval_lane"} else "low",
            "requested_tool": "propose_plan" if route_name == "brain_lane" else "draft_response",
            "requires_user_approval": route_name == "approval_lane" or decision_status == "needs_approval",
            "memory_write_requested": False,
        }
        return LLMResponse(
            mode=self.mode,
            content=json.dumps(structured, sort_keys=True),
            confidence=float(structured["confidence"]),
            proposed_tools=(str(structured["requested_tool"]),),
            safety_flags=tuple(flags),
            raw={"local_reasoner": "ix_gabriella_deterministic"},
            structured=structured,
        )



@dataclass(slots=True)
class EmbeddedGabriellaMicroProvider:
    """Packaged IX-Gabriella-LLM-Micro provider with actual local model weights."""

    model: EmbeddedGabriellaMicroLM | None = None
    mode: LLMProviderMode = LLMProviderMode.EMBEDDED_TINY

    def generate(self, request: LLMRequest) -> LLMResponse:
        model = self.model or EmbeddedGabriellaMicroLM.load()
        packet = request.brain_packet
        route = packet.get("route", {}) if isinstance(packet.get("route"), dict) else {}
        decision = packet.get("decision", {}) if isinstance(packet.get("decision"), dict) else {}
        route_name = str(route.get("route", "brain_lane"))
        status = str(decision.get("status", "proposed_plan"))
        missing = decision.get("missing_slots") or decision.get("missing") or []
        missing_slots = tuple(str(item) for item in missing) if isinstance(missing, (list, tuple)) else ()
        selected = model.select_response(
            user_text=request.user_text,
            route=route_name,
            status=status,
            missing_slots=missing_slots,
        )
        requires_approval = selected.requires_user_approval or route_name == "approval_lane" or status == "needs_approval"
        structured = {
            "assistant_response": selected.response,
            "confidence": 0.78 if route_name == "brain_lane" else 0.72,
            "risk": selected.risk,
            "requested_tool": selected.requested_tool if selected.requested_tool in request.allowed_tools else "draft_response",
            "requires_user_approval": requires_approval,
            "memory_write_requested": selected.memory_write_requested,
        }
        content = json.dumps(structured, sort_keys=True)
        flags: list[str] = ["embedded_model_loaded"]
        if requires_approval:
            flags.append("approval_required_before_effect")
        if selected.memory_write_requested:
            flags.append("memory_write_requires_core_approval")
        return LLMResponse(
            mode=self.mode,
            content=content,
            confidence=float(structured["confidence"]),
            proposed_tools=(str(structured["requested_tool"]),),
            safety_flags=tuple(flags),
            raw={
                "embedded_model": model.model_id,
                "model_sha256": model.model_sha256,
                "vocabulary_size": model.vocabulary_size,
                "candidate_score": round(selected.score, 6),
                "candidate_tags": list(selected.tags),
            },
            structured=structured,
        )

@dataclass(slots=True)
class OpenAICompatibleLLMProvider:
    """OpenAI-compatible chat-completions client configured through environment variables."""

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
            "messages": _messages(request),
            "temperature": request.temperature,
        }
        decoded = _post_json(endpoint=endpoint, payload=payload, api_key=api_key, timeout_seconds=self.timeout_seconds)
        try:
            content = decoded["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("LLM provider returned an unsupported response shape") from exc
        return _response_from_content(str(content), decoded, self.mode, request)


@dataclass(slots=True)
class OllamaLLMProvider:
    """Ollama /api/chat adapter for local model use."""

    endpoint_env: str = "IX_GABRIELLA_OLLAMA_ENDPOINT"
    model_env: str = "IX_GABRIELLA_OLLAMA_MODEL"
    timeout_seconds: float = 80.0
    mode: LLMProviderMode = LLMProviderMode.OLLAMA

    def generate(self, request: LLMRequest) -> LLMResponse:
        endpoint = os.environ.get(self.endpoint_env, "http://127.0.0.1:11434/api/chat").strip()
        model = os.environ.get(self.model_env, "").strip()
        if not model:
            raise LLMProviderError("IX_GABRIELLA_OLLAMA_MODEL is required")
        payload = {
            "model": model,
            "messages": _messages(request),
            "stream": False,
            "options": {"temperature": request.temperature},
            "format": {
                "type": "object",
                "properties": {
                    "assistant_response": {"type": "string"},
                    "confidence": {"type": "number"},
                    "risk": {"type": "string"},
                    "requested_tool": {"type": ["string", "null"]},
                    "requires_user_approval": {"type": "boolean"},
                    "memory_write_requested": {"type": "boolean"},
                },
                "required": [
                    "assistant_response",
                    "confidence",
                    "risk",
                    "requested_tool",
                    "requires_user_approval",
                    "memory_write_requested",
                ],
            },
        }
        decoded = _post_json(endpoint=endpoint, payload=payload, api_key="", timeout_seconds=self.timeout_seconds)
        try:
            content = decoded["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise LLMProviderError("Ollama provider returned an unsupported response shape") from exc
        return _response_from_content(str(content), decoded, self.mode, request)


@dataclass(slots=True)
class FallbackLLMProvider:
    primary: LLMProvider
    fallback: LLMProvider
    mode: LLMProviderMode = LLMProviderMode.FALLBACK

    def generate(self, request: LLMRequest) -> LLMResponse:
        try:
            response = self.primary.generate(request)
            valid = validate_structured_output(response.content, allowed_tools=request.allowed_tools)
            if valid.valid:
                return response
        except LLMProviderError:
            pass
        fallback_response = self.fallback.generate(request)
        return LLMResponse(
            mode=self.mode,
            content=fallback_response.content,
            confidence=fallback_response.confidence,
            proposed_tools=fallback_response.proposed_tools,
            safety_flags=(*fallback_response.safety_flags, "primary_provider_fallback_used"),
            raw={"fallback_mode": fallback_response.mode.value},
            structured=fallback_response.structured,
        )


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
    mode = os.environ.get("IX_GABRIELLA_LLM_MODE", "embedded_tiny").strip().lower()
    if mode in {"embedded_tiny", "ix_gabriella_micro", "micro"}:
        return EmbeddedGabriellaMicroProvider()
    if mode == "openai_compatible":
        return OpenAICompatibleLLMProvider()
    if mode == "ollama":
        return OllamaLLMProvider()
    if mode == "fallback_openai":
        return FallbackLLMProvider(OpenAICompatibleLLMProvider(), LocalGabriellaProvider())
    if mode == "fallback_ollama":
        return FallbackLLMProvider(OllamaLLMProvider(), LocalGabriellaProvider())
    if mode == "disabled":
        return DisabledLLMProvider()
    return LocalGabriellaProvider()


def _messages(request: LLMRequest) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": request.system_prompt},
        {
            "role": "user",
            "content": json.dumps(
                {
                    "user_text": request.user_text,
                    "brain_packet": request.brain_packet,
                    "allowed_tools": list(request.allowed_tools),
                    "blocked_effects": list(request.blocked_effects),
                    "memory_context": list(request.memory_context),
                    "correction_context": list(request.correction_context),
                },
                sort_keys=True,
            ),
        },
    ]


def _post_json(*, endpoint: str, payload: dict[str, object], api_key: str, timeout_seconds: float) -> dict[str, object]:
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    http_request = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(http_request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise LLMProviderError(f"LLM provider request failed: {exc}") from exc
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LLMProviderError("LLM provider returned non-JSON response") from exc
    if not isinstance(decoded, dict):
        raise LLMProviderError("LLM provider returned a non-object response")
    return decoded


def _normalize_legacy_content(content: str) -> str:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return content
    if not isinstance(payload, dict) or "assistant_response" in payload:
        return content
    if "content" in payload:
        tool_list = payload.get("proposed_tools", [])
        tool = tool_list[0] if isinstance(tool_list, list) and tool_list else None
        translated = {
            "assistant_response": str(payload.get("content", "")),
            "confidence": float(payload.get("confidence", 0.65) or 0.65),
            "risk": str(payload.get("risk", "medium")),
            "requested_tool": tool,
            "requires_user_approval": bool(payload.get("requires_user_approval", False)),
            "memory_write_requested": bool(payload.get("memory_write_requested", False)),
        }
        return json.dumps(translated, sort_keys=True)
    return content


def _response_from_content(content: str, raw: dict[str, object], mode: LLMProviderMode, request: LLMRequest) -> LLMResponse:
    content = _normalize_legacy_content(content)
    validation = validate_structured_output(content, allowed_tools=request.allowed_tools)
    if not validation.valid:
        validation = deterministic_repair(content, allowed_tools=request.allowed_tools)
    packet = validation.packet
    tool = packet.get("requested_tool")
    flags: list[str] = []
    if validation.repaired:
        flags.append("structured_repair_used")
    if packet.get("requires_user_approval"):
        flags.append("approval_required_before_effect")
    if packet.get("memory_write_requested"):
        flags.append("memory_write_requires_core_approval")
    return LLMResponse(
        mode=mode,
        content=str(packet["assistant_response"]),
        confidence=float(packet["confidence"]),
        proposed_tools=tuple([str(tool)] if tool else []),
        safety_flags=tuple(flags),
        raw={"provider_raw": raw, "structured_valid": not validation.repaired},
        structured=packet,
    )


def _local_content(user_text: str, packet: dict[str, object]) -> str:
    route = packet.get("route", {}) if isinstance(packet.get("route"), dict) else {}
    decision = packet.get("decision", {}) if isinstance(packet.get("decision"), dict) else {}
    route_name = str(route.get("route", "brain_lane"))
    status = str(decision.get("status", "proposed_plan"))
    if status == "needs_clarification":
        route_intent = route.get("intent") if isinstance(route.get("intent"), dict) else {}
        missing = decision.get("missing_slots") or decision.get("missing") or route_intent.get("missing_slots") or []
        if isinstance(missing, (list, tuple)) and missing:
            return f"I need the {missing[0]} before I can handle that safely."
        return "I need one more detail before I can handle that safely."
    if route_name == "approval_lane" or status == "needs_approval":
        return "I can prepare that, but I need your approval before anything consequential happens."
    if route_name == "brain_lane":
        return "IX-Gabriella-Brain can break that into a reviewable plan and keep execution gated until you approve specific steps."
    return "I understand. I will keep this in the fast lane and avoid overcomplicating it."
