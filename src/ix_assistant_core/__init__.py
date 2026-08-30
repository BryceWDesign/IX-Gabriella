"""IX-Gabriella governed virtual assistant core."""

from ix_assistant_core.assistant.engine import GabriellaAssistant
from ix_assistant_core.identity import ASSISTANT_NAME, PROJECT_NAME, WAKE_PHRASE

__all__ = ["ASSISTANT_NAME", "PROJECT_NAME", "WAKE_PHRASE", "GabriellaAssistant"]
