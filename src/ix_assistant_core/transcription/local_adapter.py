from __future__ import annotations

from ix_assistant_core.transcription.contracts import TranscriptionResult


class LocalTranscriptAdapter:
    """Deterministic adapter for tests and non-audio CLI usage.

    The adapter does not pretend to perform speech recognition. It turns supplied
    text into the same contract a speech recognizer would return so the rest of
    the assistant pipeline can be tested without cloud keys or microphones.
    """

    def transcribe_text(self, text: str, *, confidence: float = 1.0) -> TranscriptionResult:
        return TranscriptionResult(text=text, confidence=confidence)
