from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class LLMProviderMode(StrEnum):
    LOCAL_GABRIELLA = "local_gabriella"
    OPENAI_COMPATIBLE = "openai_compatible"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class LLMRequest:
    user_text: str
    system_prompt: str
    brain_packet: dict[str, Any]
    allowed_tools: tuple[str, ...] = ()
    blocked_effects: tuple[str, ...] = ()
    max_output_chars: int = 2400
    temperature: float = 0.15

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["allowed_tools"] = list(self.allowed_tools)
        data["blocked_effects"] = list(self.blocked_effects)
        return data


@dataclass(frozen=True, slots=True)
class LLMResponse:
    mode: LLMProviderMode
    content: str
    confidence: float
    proposed_tools: tuple[str, ...] = ()
    safety_flags: tuple[str, ...] = ()
    raw: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "confidence", max(0.0, min(1.0, float(self.confidence))))
        object.__setattr__(self, "content", " ".join(self.content.strip().split()))
        object.__setattr__(self, "proposed_tools", tuple(tool.strip() for tool in self.proposed_tools if tool.strip()))
        object.__setattr__(self, "safety_flags", tuple(flag.strip() for flag in self.safety_flags if flag.strip()))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["mode"] = self.mode.value
        data["proposed_tools"] = list(self.proposed_tools)
        data["safety_flags"] = list(self.safety_flags)
        return data


@dataclass(frozen=True, slots=True)
class DeliberationResult:
    consulted: bool
    reason: str
    response_text: str | None
    provider_mode: LLMProviderMode
    confidence: float
    safety_flags: tuple[str, ...] = ()
    blocked_tool_attempts: tuple[str, ...] = ()
    critique: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "confidence", max(0.0, min(1.0, float(self.confidence))))
        object.__setattr__(self, "safety_flags", tuple(flag.strip() for flag in self.safety_flags if flag.strip()))
        object.__setattr__(self, "blocked_tool_attempts", tuple(tool.strip() for tool in self.blocked_tool_attempts if tool.strip()))
        object.__setattr__(self, "critique", tuple(item.strip() for item in self.critique if item.strip()))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["provider_mode"] = self.provider_mode.value
        data["safety_flags"] = list(self.safety_flags)
        data["blocked_tool_attempts"] = list(self.blocked_tool_attempts)
        data["critique"] = list(self.critique)
        return data
