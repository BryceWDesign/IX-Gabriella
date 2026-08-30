from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import DeliberationResult, LLMProviderMode, LLMRequest
from .prompt_contracts import GABRIELLA_SYSTEM_PROMPT, LLM_OUTPUT_CONTRACT
from .providers import LLMProvider, LLMProviderError, build_provider_from_env
from .tool_schemas import BLOCKED_LLM_EFFECTS, allowed_tool_names

_FAST_SKIP_ROUTES = {"fast_lane"}
_SAFE_PROVIDER_TOOLS = set(allowed_tool_names())


@dataclass(slots=True)
class GabriellaLLMEngine:
    """Policy-bound language layer. It proposes wording and plans, never direct side effects."""

    provider: LLMProvider = field(default_factory=build_provider_from_env)
    enabled: bool = True

    def deliberate(self, *, user_text: str, brain_packet: dict[str, Any]) -> DeliberationResult:
        route = str(brain_packet.get("route", {}).get("route", "brain_lane"))
        status = str(brain_packet.get("decision", {}).get("status", ""))
        if not self.enabled or self.provider.mode == LLMProviderMode.DISABLED:
            return DeliberationResult(
                consulted=False,
                reason="llm_disabled",
                response_text=None,
                provider_mode=LLMProviderMode.DISABLED,
                confidence=0.0,
                safety_flags=("llm_disabled",),
            )
        if route in _FAST_SKIP_ROUTES and status not in {"needs_clarification", "needs_approval"}:
            return DeliberationResult(
                consulted=False,
                reason="fast_lane_downshift_preserved",
                response_text=None,
                provider_mode=self.provider.mode,
                confidence=0.0,
                critique=("simple task stayed out of the expensive language path",),
            )
        request = LLMRequest(
            user_text=user_text,
            system_prompt=f"{GABRIELLA_SYSTEM_PROMPT}\n\n{LLM_OUTPUT_CONTRACT}",
            brain_packet=brain_packet,
            allowed_tools=allowed_tool_names(),
            blocked_effects=BLOCKED_LLM_EFFECTS,
        )
        try:
            response = self.provider.generate(request)
        except LLMProviderError as exc:
            return DeliberationResult(
                consulted=True,
                reason=f"provider_failed_safe:{exc}",
                response_text=None,
                provider_mode=self.provider.mode,
                confidence=0.0,
                safety_flags=("provider_failed_safe",),
                critique=("fallback_to_deterministic_core",),
            )
        blocked = tuple(tool for tool in response.proposed_tools if tool not in _SAFE_PROVIDER_TOOLS)
        flags = (*response.safety_flags, *("blocked_llm_tool_attempt" for _ in blocked))
        text = None if blocked else response.content
        reason = "llm_deliberation_accepted" if not blocked else "llm_deliberation_rejected_for_tool_boundary"
        return DeliberationResult(
            consulted=True,
            reason=reason,
            response_text=text,
            provider_mode=response.mode,
            confidence=response.confidence,
            safety_flags=flags,
            blocked_tool_attempts=blocked,
            critique=_critique(brain_packet, response.confidence),
        )


def _critique(packet: dict[str, Any], confidence: float) -> tuple[str, ...]:
    route = str(packet.get("route", {}).get("route", "brain_lane"))
    notes = [f"route={route}"]
    if confidence < 0.60:
        notes.append("low_language_confidence_use_core_response")
    if route == "approval_lane":
        notes.append("approval_boundary_must_remain_active")
    if route == "brain_lane":
        notes.append("plan_only_until_core_policy_authorizes_tools")
    return tuple(notes)
