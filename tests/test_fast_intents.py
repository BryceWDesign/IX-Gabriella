from ix_gabriella_brain.fast_intents import FastIntentRegistry
from ix_gabriella_brain.models import RiskLevel


def test_timer_intent_extracts_duration() -> None:
    intent = FastIntentRegistry().match("set a timer for 10 minutes")
    assert intent is not None
    assert intent.name == "set_timer"
    assert intent.slots["duration"]["amount"] == 10.0
    assert intent.risk == RiskLevel.LOW
    assert not intent.missing_slots


def test_reminder_intent_missing_time_when_absent() -> None:
    intent = FastIntentRegistry().match("remind me to call John")
    assert intent is not None
    assert intent.name == "create_reminder"
    assert "time_hint" in intent.missing_slots


def test_reminder_intent_extracts_time_hint() -> None:
    intent = FastIntentRegistry().match("remind me to call John tomorrow")
    assert intent is not None
    assert intent.name == "create_reminder"
    assert intent.slots["time_hint"] == "tomorrow"


def test_list_intent_extracts_item_and_list() -> None:
    intent = FastIntentRegistry().match("add milk to my grocery list")
    assert intent is not None
    assert intent.name == "add_list_item"
    assert intent.slots["item"] == "milk"
    assert intent.slots["list"] == "grocery"


def test_note_intent_extracts_note() -> None:
    intent = FastIntentRegistry().match("take a note that verify receipts after tests")
    assert intent is not None
    assert intent.name == "take_note"
    assert "verify receipts" in intent.slots["note"]


def test_memory_intent_requires_approval() -> None:
    intent = FastIntentRegistry().match("remember that I prefer direct answers")
    assert intent is not None
    assert intent.name == "memory_proposal"
    assert intent.requires_approval


def test_email_intent_is_high_risk() -> None:
    intent = FastIntentRegistry().match("draft an email to Sarah saying I am late")
    assert intent is not None
    assert intent.name == "email_draft"
    assert intent.risk == RiskLevel.HIGH


def test_smart_home_stage_intent() -> None:
    intent = FastIntentRegistry().match("turn off the kitchen lights")
    assert intent is not None
    assert intent.name == "smart_home_stage"
    assert intent.slots["state"] == "off"
    assert intent.slots["device"] == "the kitchen lights"
