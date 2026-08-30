from ix_gabriella_brain.assurance import AssuranceCase
from ix_gabriella_brain.fast_intents import FastIntentRegistry
from ix_gabriella_brain.mission import MissionEnvelopeBuilder
from ix_gabriella_brain.models import BrainDecision, DecisionStatus, RiskLevel, RouteKind
from ix_gabriella_brain.planner import GoalPlanner
from ix_gabriella_brain.policy import BrainPolicy
from ix_gabriella_brain.routing import DownshiftRouter
from ix_gabriella_brain.worldtwin import WorldTwinLite


def test_meeting_planner_creates_context_steps() -> None:
    steps = GoalPlanner().plan("prepare for tomorrow's meeting")
    assert any(step.action_type == "retrieve_context" for step in steps)
    assert any(step.requires_approval for step in steps)


def test_comparison_planner_includes_criteria() -> None:
    steps = GoalPlanner().plan("compare two options and recommend one")
    assert steps[0].action_type == "criteria"


def test_build_planner_includes_quality_gate() -> None:
    steps = GoalPlanner().plan("build the strongest brain repo")
    assert any(step.action_type == "verify" for step in steps)


def test_research_planner_includes_source_review() -> None:
    steps = GoalPlanner().plan("research the top complaints")
    assert any(step.action_type == "source_review" for step in steps)


def test_mission_envelope_forbids_self_authorized_memory() -> None:
    mission = MissionEnvelopeBuilder().build("remember this", RiskLevel.MEDIUM)
    assert "store_long_term_memory_without_approval" in mission.forbidden_actions
    assert mission.requires_human_authority


def test_policy_allows_local_timer() -> None:
    intent = FastIntentRegistry().match("set a timer for 3 minutes")
    decision = BrainPolicy().decide(RouteKind.FAST_LANE, intent)
    assert decision.allowed_local_execution
    assert not decision.requires_approval


def test_policy_requires_memory_approval() -> None:
    intent = FastIntentRegistry().match("remember that I like receipts")
    decision = BrainPolicy().decide(RouteKind.APPROVAL_LANE, intent)
    assert decision.requires_approval
    assert not decision.allowed_local_execution


def test_worldtwin_blocks_forbidden_effect() -> None:
    mission = MissionEnvelopeBuilder().build("remember that x", RiskLevel.MEDIUM)
    decision = BrainDecision(
        status=DecisionStatus.NEEDS_APPROVAL,
        user_message="approval needed",
        action={"requested_effects": ("store_long_term_memory_without_approval",)},
    )
    result = WorldTwinLite().evaluate(decision, mission)
    assert result.verdict == "blocked"


def test_worldtwin_allows_local_safe_action() -> None:
    mission = MissionEnvelopeBuilder().build("set a timer for 1 minute", RiskLevel.LOW)
    decision = BrainDecision(status=DecisionStatus.EXECUTED_LOCAL, user_message="done", action={"requested_effects": ("execute_low_risk_local_action",)})
    result = WorldTwinLite().evaluate(decision, mission)
    assert result.verdict == "local_safe_action"


def test_assurance_passes_reviewable_plan() -> None:
    route = DownshiftRouter().route("help me prepare for a meeting")
    mission = MissionEnvelopeBuilder().build("help me prepare for a meeting", route.risk)
    decision = BrainDecision(status=DecisionStatus.PROPOSED_PLAN, user_message="plan", plan=GoalPlanner().plan("meeting"))
    world = WorldTwinLite().evaluate(decision, mission)
    result = AssuranceCase().evaluate(route, decision, mission, world)
    assert result.readiness_score >= 0.84
    assert "true AGI demonstrated" in result.claims_blocked
