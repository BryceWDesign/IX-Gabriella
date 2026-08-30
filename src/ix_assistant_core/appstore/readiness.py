from __future__ import annotations

from dataclasses import dataclass

from ix_assistant_core.ads import AdPolicy
from ix_assistant_core.privacy import PrivacyControls


@dataclass(frozen=True, slots=True)
class AppStoreReadinessCheck:
    """Static readiness checks for an eventual App Store app wrapper."""

    privacy_policy_present: bool
    account_deletion_path_present: bool
    microphone_usage_copy_present: bool
    ad_disclosure_present: bool
    privacy_controls: PrivacyControls
    ad_policy: AdPolicy

    def issues(self) -> tuple[str, ...]:
        issues: list[str] = []
        if not self.privacy_policy_present:
            issues.append("privacy-policy-missing")
        if not self.account_deletion_path_present:
            issues.append("account-deletion-path-missing")
        if not self.microphone_usage_copy_present:
            issues.append("microphone-usage-copy-missing")
        if not self.ad_disclosure_present:
            issues.append("ad-disclosure-missing")
        if self.privacy_controls.share_voice_content_for_ads:
            issues.append("voice-content-ad-targeting-enabled")
        if self.ad_policy.allow_voice_content_targeting:
            issues.append("ad-policy-allows-voice-content-targeting")
        return tuple(issues)

    def passed(self) -> bool:
        return not self.issues()
