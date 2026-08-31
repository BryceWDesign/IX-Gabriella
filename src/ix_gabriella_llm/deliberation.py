from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .correction_learning import CorrectionStore
from .memory_retrieval import lexical_memory_hits
from .models import DeliberationResult, LLMProviderMode, LLMRequest, LLMStackHealth
from .orchestrator import GabriellaLLMOrchestrator
from .prompt_contracts import GABRIELLA_SYSTEM_PROMPT, LLM_OUTPUT_CONTRACT
from .providers import LLMProvider, build_provider_from_env
from .tool_schemas import BLOCKED_LLM_EFFECTS, allowed_tool_names


@dataclass(slots=True)
class GabriellaLLMEngine:
    """Policy-bound language layer. It proposes wording and plans, never direct effects."""

    provider: LLMProvider = field(default_factory=build_provider_from_env)
    enabled: bool = True
    correction_store: CorrectionStore = field(default_factory=CorrectionStore)

    def deliberate(
        self,
        *,
        user_text: str,
        brain_packet: dict[str, Any],
        approved_memories: tuple[str, ...] = (),
    ) -> DeliberationResult:
        if not self.enabled or self.provider.mode == LLMProviderMode.DISABLED:
            return DeliberationResult(
                consulted=False,
                reason="llm_disabled",
                response_text=None,
                provider_mode=LLMProviderMode.DISABLED,
                confidence=0.0,
                safety_flags=("llm_disabled",),
                intelligence_ceiling_note="disabled",
            )
        memory_hits = tuple(hit.text for hit in lexical_memory_hits(user_text, approved_memories))
        correction_hits = tuple(
            f"original={item.original} corrected={item.corrected}"
            for item in self.correction_store.examples_for(user_text)
        )
        request = LLMRequest(
            user_text=user_text,
            system_prompt=f"{GABRIELLA_SYSTEM_PROMPT}\n\n{LLM_OUTPUT_CONTRACT}",
            brain_packet=brain_packet,
            allowed_tools=allowed_tool_names(),
            blocked_effects=BLOCKED_LLM_EFFECTS,
            memory_context=memory_hits,
            correction_context=correction_hits,
        )
        orchestrator = GabriellaLLMOrchestrator(provider=self.provider)
        return orchestrator.run(
            request=request,
            skip_fast_lane=True,
            provider_mode_when_skipped=self.provider.mode,
        )

    def record_correction(self, *, original: str, corrected: str) -> None:
        self.correction_store.add(original=original, corrected=corrected)

    def health(self) -> LLMStackHealth:
        external = self.provider.mode in {
            LLMProviderMode.OPENAI_COMPATIBLE,
            LLMProviderMode.OLLAMA,
            LLMProviderMode.FALLBACK,
        }
        return LLMStackHealth(
            configured_mode=self.provider.mode,
            has_external_provider=external,
            has_structured_contract=True,
            has_fallback=self.provider.mode == LLMProviderMode.FALLBACK,
            expected_standalone_score=6.4 if self.provider.mode == LLMProviderMode.EMBEDDED_TINY else (6.0 if self.provider.mode == LLMProviderMode.LOCAL_GABRIELLA else 5.5),
            expected_with_strong_model_score=8.2,
        )

    @classmethod
    def persistent(cls, *, state_dir: Path) -> "GabriellaLLMEngine":
        state_dir.mkdir(parents=True, exist_ok=True)
        return cls(correction_store=CorrectionStore(state_dir / "llm_corrections.json"))
