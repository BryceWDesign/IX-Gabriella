from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import DeliberationResult, LLMProviderMode, LLMRequest
from .providers import LLMProvider, LLMProviderError, LocalGabriellaProvider, build_provider_from_env
from .structured import validate_structured_output
from .tool_schemas import BLOCKED_LLM_EFFECTS, allowed_tool_names

_FAST_SKIP_ROUTES = {"fast_lane"}
_SAFE_PROVIDER_TOOLS = set(allowed_tool_names())


@dataclass(slots=True)
class GabriellaLLMOrchestrator:
    provider: LLMProvider | None = None

    def run(
        self,
        *,
        request: LLMRequest,
        skip_fast_lane: bool,
        provider_mode_when_skipped: LLMProviderMode,
    ) -> DeliberationResult:
        route = str(request.brain_packet.get("route", {}).get("route", "brain_lane"))
        status = str(request.brain_packet.get("decision", {}).get("status", ""))
        provider = self.provider or build_provider_from_env()
        if skip_fast_lane and route in _FAST_SKIP_ROUTES and status not in {"needs_clarification", "needs_approval"}:
            return DeliberationResult(
                consulted=False,
                reason="fast_lane_downshift_preserved",
                response_text=None,
                provider_mode=provider_mode_when_skipped,
                confidence=0.0,
                critique=("simple task stayed out of the expensive language path",),
                intelligence_ceiling_note="fast deterministic lane",
            )
        try:
            response = provider.generate(request)
        except LLMProviderError as exc:
            local = LocalGabriellaProvider().generate(request)
            return DeliberationResult(
                consulted=True,
                reason=f"provider_failed_safe:{exc}",
                response_text=local.structured.get("assistant_response", local.content),
                provider_mode=provider.mode,
                confidence=local.confidence,
                safety_flags=("provider_failed_safe", *local.safety_flags),
                critique=("fallback_to_deterministic_core",),
                repair_used=True,
                structured_valid=True,
                intelligence_ceiling_note="fallback provider used",
            )
        validation = validate_structured_output(response.content, allowed_tools=request.allowed_tools)
        structured_valid = validation.valid or bool(response.structured)
        blocked = tuple(tool for tool in response.proposed_tools if tool not in _SAFE_PROVIDER_TOOLS)
        flags = (*response.safety_flags, *tuple("blocked_llm_tool_attempt" for _ in blocked))
        text = None if blocked else (response.structured.get("assistant_response") if response.structured else response.content)
        reason = "llm_deliberation_accepted" if not blocked else "llm_deliberation_rejected_for_tool_boundary"
        return DeliberationResult(
            consulted=True,
            reason=reason,
            response_text=str(text) if text else None,
            provider_mode=response.mode,
            confidence=response.confidence,
            safety_flags=flags,
            blocked_tool_attempts=blocked,
            critique=_critique(request.brain_packet, response.confidence, structured_valid),
            repair_used="structured_repair_used" in flags,
            structured_valid=structured_valid,
            intelligence_ceiling_note=_ceiling_note(response.mode),
        )


def _critique(packet: dict[str, Any], confidence: float, structured_valid: bool) -> tuple[str, ...]:
    route = str(packet.get("route", {}).get("route", "brain_lane"))
    notes = [f"route={route}"]
    if confidence < 0.60:
        notes.append("low_language_confidence_use_core_response")
    if route == "approval_lane":
        notes.append("approval_boundary_must_remain_active")
    if route == "brain_lane":
        notes.append("plan_only_until_core_policy_authorizes_tools")
    if not structured_valid:
        notes.append("structured_output_repaired_or_fallback")
    return tuple(notes)


def _ceiling_note(mode: LLMProviderMode) -> str:
    if mode == LLMProviderMode.EMBEDDED_TINY:
        return "embedded micro model improves standalone behavior; strong external model required for 8 plus behavior"
    if mode in {LLMProviderMode.OPENAI_COMPATIBLE, LLMProviderMode.OLLAMA, LLMProviderMode.FALLBACK}:
        return "connected model quality determines 8 plus behavior"
    return "deterministic local language layer"
