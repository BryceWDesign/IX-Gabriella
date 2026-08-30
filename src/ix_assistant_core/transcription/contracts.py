from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TranscriptionResult:
    """Provider-neutral speech-to-text output contract.

    This is intentionally not bound to any cloud vendor. Mobile implementations
    can adapt Apple Speech, on-device recognizers, Whisper-family models, or a
    paid provider to this shape.
    """

    text: str
    confidence: float
    alternatives: tuple[str, ...] = ()
    provider: str = "manual-or-local"

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("transcription text must not be empty")
        object.__setattr__(self, "confidence", max(0.0, min(1.0, float(self.confidence))))
