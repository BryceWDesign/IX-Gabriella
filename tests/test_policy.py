from ix_assistant_core.actions import ActionPlanner
from ix_assistant_core.governance import GovernancePolicy
from ix_assistant_core.input import InputNormalizer
from ix_assistant_core.intent import RuleBasedIntentParser
from ix_assistant_core.models import PolicyOutcome


def _plan(text: str):
    transcript = InputNormalizer().normalize_text(text)
    intent = RuleBasedIntentParser().parse(transcript)
    return ActionPlanner().plan(intent)


def test_low_risk_timer_can_pass_policy() -> None:
    decision = GovernancePolicy().evaluate(_plan("set a timer for 5 minutes"))
    assert decision.outcome == PolicyOutcome.ALLOW


def test_smart_home_requires_confirmation() -> None:
    decision = GovernancePolicy().evaluate(_plan("turn off the bedroom lights"))
    assert decision.outcome == PolicyOutcome.REQUIRE_CONFIRMATION
    assert "approval-required" in decision.reason_codes


def test_financial_purchase_pattern_is_blocked() -> None:
    decision = GovernancePolicy().evaluate(_plan("buy a new television"))
    assert decision.outcome == PolicyOutcome.BLOCK
    assert "denied-pattern" in decision.reason_codes


def test_unknown_requires_confirmation_not_execution() -> None:
    decision = GovernancePolicy().evaluate(_plan("florm the cabinet"))
    assert decision.outcome == PolicyOutcome.REQUIRE_CONFIRMATION
    assert "confidence-below-policy" in decision.reason_codes
