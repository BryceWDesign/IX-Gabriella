from __future__ import annotations

from pathlib import Path

from .assurance import AssuranceCase
from .belief import BeliefGraph
from .fast_intents import FastIntentRegistry
from .hashing import stable_hash, utc_now_iso
from .memory import MemoryQuarantine
from .mission import MissionEnvelopeBuilder
from .models import BrainDecision, BrainRequest, CognitivePacket, DecisionStatus, RouteKind
from .planner import GoalPlanner
from .policy import BrainPolicy
from .receipts import ReceiptLedger
from .response import ResponseComposer
from .routing import DownshiftRouter
from .storage import StateRepository
from .uncertainty import UncertaintyEngine
from .worldtwin import WorldTwinLite


class GabriellaBrain:
    def __init__(self, *, state_path: Path | str | None = None, receipt_path: Path | str | None = None, execute_fast_locally: bool = True) -> None:
        self.registry = FastIntentRegistry()
        self.router = DownshiftRouter(self.registry)
        self.policy = BrainPolicy(self.registry)
        self.planner = GoalPlanner()
        self.uncertainty = UncertaintyEngine()
        self.missions = MissionEnvelopeBuilder()
        self.worldtwin = WorldTwinLite()
        self.assurance = AssuranceCase()
        self.composer = ResponseComposer()
        self.beliefs = BeliefGraph()
        self.memory = MemoryQuarantine()
        self.state_repo = StateRepository(state_path)
        self.ledger = ReceiptLedger(Path(receipt_path) if receipt_path else None)
        self.execute_fast_locally = execute_fast_locally

    def think(self, text: str, *, user_id: str = "local-user", channel: str = "text", session_id: str = "local-session") -> CognitivePacket:
        request = BrainRequest(text=text, user_id=user_id, channel=channel, session_id=session_id)
        request_hash = stable_hash(request.to_dict())
        route = self.router.route(text)
        mission = self.missions.build(text, route.risk)
        uncertainty = self.uncertainty.assess(text, route.intent, route.risk)
        decision = self._decide(text, request_hash, route, uncertainty.should_ask)
        world = self.worldtwin.evaluate(decision, mission)
        assurance = self.assurance.evaluate(route, decision, mission, world)
        packet_payload = {
            "request": request.to_dict(),
            "route": route.to_dict(),
            "decision": decision.to_dict(),
            "mission": mission.to_dict(),
            "worldtwin": world.to_dict(),
            "assurance": assurance.to_dict(),
            "uncertainty": uncertainty.to_dict(),
        }
        packet_id = "brain-packet-" + stable_hash(packet_payload)[:16]
        receipt = self.ledger.append("cognitive_packet", {"packet_id": packet_id, **packet_payload})
        packet = CognitivePacket(
            packet_id=packet_id,
            request=request,
            route=route,
            decision=decision,
            worldtwin=world,
            assurance=assurance,
            receipt_hash=receipt["receipt_hash"],
            created_at=utc_now_iso(),
        )
        if decision.status == DecisionStatus.NEEDS_APPROVAL:
            self.state_repo.state.stage_pending(packet_id, decision.action)
        self.state_repo.save()
        return packet

    def approve(self, packet_id: str) -> dict[str, object]:
        action = self.state_repo.state.approve_pending(packet_id)
        receipt = self.ledger.append("approval", {"packet_id": packet_id, "action": action})
        self.state_repo.save()
        return {"packet_id": packet_id, "approved": True, "receipt_hash": receipt["receipt_hash"], "action": action}

    def reject(self, packet_id: str) -> dict[str, object]:
        action = self.state_repo.state.reject_pending(packet_id)
        receipt = self.ledger.append("rejection", {"packet_id": packet_id, "action": action})
        self.state_repo.save()
        return {"packet_id": packet_id, "approved": False, "receipt_hash": receipt["receipt_hash"], "action": action}

    def _decide(self, text: str, request_hash: str, route, should_ask: bool) -> BrainDecision:
        intent = route.intent
        if route.route == RouteKind.CLARIFY_LANE or route.route != RouteKind.BRAIN_LANE and should_ask and intent and intent.missing_slots:
            return BrainDecision(
                status=DecisionStatus.NEEDS_CLARIFICATION,
                user_message=self.composer.compose_clarification(intent),
                needs_user_input=True,
                safety_notes=("no_action_without_required_slots",),
            )
        if route.route == RouteKind.FAST_LANE and intent:
            policy = self.policy.decide(route.route, intent)
            if policy.allowed_local_execution:
                action = {"intent": intent.name, "slots": intent.slots}
                status = DecisionStatus.STAGED
                effects = ("delegate_low_risk_local_action_to_gabriella_core",)
                if self.execute_fast_locally:
                    action = self.state_repo.state.commit_local(intent.name, intent.slots)
                    status = DecisionStatus.EXECUTED_LOCAL
                    effects = ("execute_low_risk_local_action",)
                return BrainDecision(
                    status=status,
                    user_message=self.composer.compose_fast_success(intent, action),
                    action={"intent": intent.name, "slots": intent.slots, "local_result": action, "requested_effects": effects},
                    safety_notes=policy.notes,
                )
        if route.route == RouteKind.APPROVAL_LANE and intent:
            if intent.name == "memory_proposal":
                candidate = self.memory.propose(str(intent.slots.get("memory", "")), source_request_hash=request_hash)
                return BrainDecision(
                    status=DecisionStatus.NEEDS_APPROVAL,
                    user_message="I can remember that only if you approve it.",
                    action={"intent": intent.name, "slots": intent.slots, "memory_id": candidate.memory_id, "requested_effects": ("store_long_term_memory_without_approval",)},
                    memory_candidate=candidate,
                    needs_user_input=True,
                    approval_question=f"Approve saving this memory: {candidate.text}",
                    safety_notes=("memory_quarantine_active",),
                )
            action = {"intent": intent.name, "slots": intent.slots, "requested_effects": ("stage_action",)}
            return BrainDecision(
                status=DecisionStatus.NEEDS_APPROVAL,
                user_message=self.composer.compose_approval(intent, action),
                action=action,
                needs_user_input=True,
                approval_question=self.composer.compose_approval(intent, action),
                safety_notes=("approval_required_before_external_or_private_effect",),
            )
        steps = self.planner.plan(text)
        self.beliefs.add("current_user_goal", "requested", text, confidence=route.confidence, evidence=(request_hash,))
        return BrainDecision(
            status=DecisionStatus.PROPOSED_PLAN,
            user_message=self.composer.compose_plan(steps),
            plan=steps,
            action={"intent": "plan_goal", "requested_effects": ("decompose_goal", "create_reviewable_plan")},
            safety_notes=("brain_lane_plan_only_no_external_execution",),
        )
