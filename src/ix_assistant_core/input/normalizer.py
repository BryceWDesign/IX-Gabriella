from __future__ import annotations

import re

from ix_assistant_core.identity import ASSISTANT_NAME, WAKE_PHRASE
from ix_assistant_core.models import InputMode, Transcript

_SPACE_RE = re.compile(r"\s+")
_WAKE_RE = re.compile(r"^(hey|hi|ok|okay)\s+(gabriella|gabriela|gabby|gabi)[,\s]+", re.I)


class InputNormalizer:
    """Normalize user text and voice transcripts without hiding uncertainty."""

    def normalize_text(
        self,
        text: str,
        *,
        mode: InputMode = InputMode.TEXT,
        acoustic_confidence: float | None = None,
        alternatives: tuple[str, ...] = (),
    ) -> Transcript:
        cleaned = _SPACE_RE.sub(" ", text.strip())
        cleaned = _WAKE_RE.sub("", cleaned).strip()
        if not cleaned:
            cleaned = text.strip()
        if not cleaned:
            raise ValueError("input text must not be empty")
        return Transcript(
            text=cleaned,
            mode=mode,
            acoustic_confidence=acoustic_confidence,
            alternatives=alternatives,
        )

    def explain_wake_name(self) -> str:
        return f"{WAKE_PHRASE} activates {ASSISTANT_NAME} in voice surfaces that support it."
