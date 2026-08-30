import pytest

from ix_assistant_core.ads import AdPolicy
from ix_assistant_core.memory import MemoryStore
from ix_assistant_core.privacy import PrivacyControls


def test_memory_write_requires_user_approval() -> None:
    store = MemoryStore()
    with pytest.raises(PermissionError):
        store.add("likes concise answers", approved_by_user=False)
    record = store.add("likes concise answers", approved_by_user=True)
    assert record.approved_by_user is True
    assert len(store.list()) == 1


def test_privacy_rejects_voice_content_ad_targeting() -> None:
    controls = PrivacyControls(share_voice_content_for_ads=True)
    with pytest.raises(ValueError):
        controls.validate()


def test_sensitive_context_suppresses_bottom_ad() -> None:
    decision = AdPolicy().decide(screen_name="chat", transcript_text="my bank password issue")
    assert decision.show_bottom_ad is False


def test_generic_screen_ad_allowed_without_private_targeting() -> None:
    decision = AdPolicy().decide(screen_name="home", transcript_text="set a timer")
    assert decision.show_bottom_ad is True
    assert decision.allowed_context == "home"
