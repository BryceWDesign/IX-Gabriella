from __future__ import annotations

from .hashing import stable_hash
from .models import PlanStep, RiskLevel
from .text import lower_ascii


def _step_id(goal: str, title: str, index: int) -> str:
    return "step-" + stable_hash({"goal": goal, "title": title, "index": index})[:12]


class GoalPlanner:
    def plan(self, goal: str) -> tuple[PlanStep, ...]:
        cleaned = lower_ascii(goal)
        if "meeting" in cleaned or "call" in cleaned:
            titles = (
                ("Identify meeting objective", "extract_context", "Find the stated purpose, people, date, and expected outcome."),
                ("Gather known context", "retrieve_context", "Use approved memory or provided notes only."),
                ("Draft prep agenda", "compose", "Create a concise agenda and open questions."),
                ("Ask for missing details", "clarify", "Do not invent attendee goals or private facts."),
                ("Create review packet", "review_packet", "Package plan, assumptions, and unresolved items."),
            )
        elif "compare" in cleaned or "choose" in cleaned or "recommend" in cleaned:
            titles = (
                ("Extract decision criteria", "criteria", "List what matters before ranking options."),
                ("Separate facts from assumptions", "belief_check", "Mark unknowns instead of treating guesses as facts."),
                ("Score each option", "evaluate", "Use declared criteria and confidence levels."),
                ("Surface risks", "risk_review", "Call out weak evidence and tradeoffs."),
                ("Recommend reversible next step", "recommend", "Prefer a bounded next action over forced certainty."),
            )
        elif "build" in cleaned or "create" in cleaned or "upgrade" in cleaned or "launch" in cleaned:
            titles = (
                ("Define target capability", "scope", "Describe the output, boundary, and success gate."),
                ("Inventory available components", "inventory", "Use donor mechanisms and current repo features."),
                ("Design safe architecture", "architecture", "Route simple tasks fast and complex tasks through cognition."),
                ("Implement bounded capability", "implement", "Build real code with tests and claim boundaries."),
                ("Run quality gate", "verify", "Compile, test, scan markers, and generate receipts."),
                ("Prepare handoff", "handoff", "Export manifest, audit, and usage instructions."),
            )
        elif "research" in cleaned or "look up" in cleaned or "find out" in cleaned:
            titles = (
                ("Clarify research question", "clarify", "Narrow what must be verified."),
                ("Collect source evidence", "evidence", "Use current sources when freshness matters."),
                ("Compare source quality", "source_review", "Separate primary, secondary, and weak sources."),
                ("Summarize with uncertainty", "summarize", "Cite facts and mark unresolved points."),
            )
        else:
            titles = (
                ("Restate the user goal", "interpret", "Confirm the goal in operational terms."),
                ("Identify missing information", "clarify", "Ask only for details required to proceed."),
                ("Create bounded action plan", "plan", "Break the task into safe steps."),
                ("Check approval boundaries", "govern", "Separate proposals from user-authorized action."),
                ("Return next useful result", "respond", "Give the user a clear next step or answer."),
            )
        steps: list[PlanStep] = []
        for index, (title, action_type, rationale) in enumerate(titles, start=1):
            risk = RiskLevel.MEDIUM if action_type in {"implement", "retrieve_context", "evidence"} else RiskLevel.LOW
            requires_approval = action_type in {"retrieve_context", "implement", "handoff"}
            steps.append(PlanStep(
                step_id=_step_id(goal, title, index),
                title=title,
                action_type=action_type,
                rationale=rationale,
                risk=risk,
                requires_approval=requires_approval,
                evidence_needed=("user_goal", "policy_boundary") if requires_approval else ("user_goal",),
                expected_result=f"{title} completed or explicitly blocked.",
            ))
        return tuple(steps)
