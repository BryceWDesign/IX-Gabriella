from ix_assistant_core.input import InputNormalizer
from ix_assistant_core.intent import RuleBasedIntentParser
from ix_assistant_core.models import InputMode, IntentKind


def test_wake_phrase_is_removed_without_losing_request() -> None:
    transcript = InputNormalizer().normalize_text("Hey Gabriella, remind me to call Mom")
    assert transcript.text == "remind me to call Mom"


def test_low_acoustic_confidence_reduces_intent_confidence() -> None:
    transcript = InputNormalizer().normalize_text(
        "turn on the kitchen lights", mode=InputMode.VOICE, acoustic_confidence=0.40
    )
    intent = RuleBasedIntentParser().parse(transcript)
    assert intent.kind == IntentKind.SMART_HOME_CONTROL
    assert intent.confidence < 0.74
    assert "acoustic-confidence-applied" in intent.reasons


def test_unknown_intent_fails_closed() -> None:
    transcript = InputNormalizer().normalize_text("blorple the glass triangle")
    intent = RuleBasedIntentParser().parse(transcript)
    assert intent.kind == IntentKind.UNKNOWN
    assert intent.confidence <= 0.20
