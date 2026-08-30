from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PrivacyControls:
    """Runtime privacy defaults for IX-Gabriella."""

    memory_opt_in: bool = False
    share_voice_content_for_ads: bool = False
    retain_raw_audio: bool = False
    retain_transcripts: bool = True
    allow_sensitive_action_without_confirmation: bool = False

    def validate(self) -> None:
        if self.share_voice_content_for_ads:
            raise ValueError("voice or transcript content must not be shared for ad targeting")
        if self.allow_sensitive_action_without_confirmation:
            raise ValueError("sensitive actions must require confirmation")

    def user_summary(self) -> str:
        memory = "off" if not self.memory_opt_in else "on with approval"
        audio = "not retained" if not self.retain_raw_audio else "retained by setting"
        ads = "not based on private voice content"
        return f"Memory is {memory}. Raw audio is {audio}. Ads are {ads}."
