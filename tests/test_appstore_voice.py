from ix_assistant_core.ads import AdPolicy
from ix_assistant_core.appstore import AppStoreReadinessCheck
from ix_assistant_core.privacy import PrivacyControls
from ix_assistant_core.voice import score_wake_phrase


def test_appstore_readiness_passes_when_required_disclosures_exist() -> None:
    check = AppStoreReadinessCheck(
        privacy_policy_present=True,
        account_deletion_path_present=True,
        microphone_usage_copy_present=True,
        ad_disclosure_present=True,
        privacy_controls=PrivacyControls(),
        ad_policy=AdPolicy(),
    )
    assert check.passed()


def test_appstore_readiness_detects_missing_privacy_policy() -> None:
    check = AppStoreReadinessCheck(
        privacy_policy_present=False,
        account_deletion_path_present=True,
        microphone_usage_copy_present=True,
        ad_disclosure_present=True,
        privacy_controls=PrivacyControls(),
        ad_policy=AdPolicy(),
    )
    assert "privacy-policy-missing" in check.issues()


def test_hey_gabriella_scores_as_voice_friendly() -> None:
    score = score_wake_phrase("Hey Gabriella")
    assert score.score >= 8.0
    assert "strong-consonant-anchors" in score.rationale
