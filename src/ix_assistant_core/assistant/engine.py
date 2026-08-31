from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ix_assistant_core.actions import ActionPlanner
from ix_assistant_core.ads import AdPolicy
from ix_assistant_core.brain import BrainBridge
from ix_assistant_core.governance import ApprovalGate, GovernancePolicy
from ix_assistant_core.input import InputNormalizer
from ix_assistant_core.intent import RuleBasedIntentParser
from ix_assistant_core.memory import MemoryStore
from ix_assistant_core.models import (
    ActionStatus,
    AssistantTurn,
    InputMode,
    IntentKind,
    PolicyOutcome,
    Transcript,
)
from ix_assistant_core.privacy import PrivacyControls
from ix_assistant_core.receipts import ReceiptEventType, ReceiptLedger
from ix_assistant_core.response import ResponseComposer
from ix_assistant_core.runtime import LocalActionStore
from ix_gabriella_brain import GabriellaBrain
from ix_gabriella_llm import GabriellaLLMEngine


@dataclass(slots=True)
class GabriellaAssistant:
    """Brain-integrated governed assistant pipeline with safe local execution."""

    normalizer: InputNormalizer
    parser: RuleBasedIntentParser
    planner: ActionPlanner
    policy: GovernancePolicy
    approval_gate: ApprovalGate
    receipts: ReceiptLedger
    memory: MemoryStore
    privacy: PrivacyControls
    ad_policy: AdPolicy
    local_store: LocalActionStore
    responder: ResponseComposer
    brain: GabriellaBrain
    brain_bridge: BrainBridge
    llm: GabriellaLLMEngine

    @classmethod
    def default(cls, *, state_dir: Path | None = None, persist: bool = False) -> "GabriellaAssistant":
        privacy = PrivacyControls()
        privacy.validate()
        memory_path = None
        action_path = None
        brain_state_path = None
        brain_receipt_path = None
        if persist:
            root = state_dir or Path.home() / ".ix-gabriella"
            root.mkdir(parents=True, exist_ok=True)
            memory_path = root / "approved_memory.json"
            action_path = root / "local_actions.json"
            brain_state_path = root / "brain_state.json"
            brain_receipt_path = root / "brain_receipts.jsonl"
        return cls(
            normalizer=InputNormalizer(),
            parser=RuleBasedIntentParser(),
            planner=ActionPlanner(),
            policy=GovernancePolicy(),
            approval_gate=ApprovalGate(),
            receipts=ReceiptLedger(),
            memory=MemoryStore(memory_path),
            privacy=privacy,
            ad_policy=AdPolicy(),
            local_store=LocalActionStore(action_path),
            responder=ResponseComposer(),
            brain=GabriellaBrain(
                state_path=brain_state_path,
                receipt_path=brain_receipt_path,
                execute_fast_locally=False,
            ),
            brain_bridge=BrainBridge(),
            llm=GabriellaLLMEngine.persistent(state_dir=root) if persist else GabriellaLLMEngine(),
        )

    def handle_text(
        self,
        text: str,
        *,
        mode: InputMode = InputMode.TEXT,
        acoustic_confidence: float | None = None,
        alternatives: tuple[str, ...] = (),
    ) -> AssistantTurn:
        transcript = self.normalizer.normalize_text(
            text,
            mode=mode,
            acoustic_confidence=acoustic_confidence,
            alternatives=alternatives,
        )
        return self._handle_transcript(transcript)

    def _handle_transcript(self, transcript: Transcript) -> AssistantTurn:
        packet = self.brain.think(
            transcript.text,
            user_id="local-user",
            channel=transcript.mode.value,
            session_id="ix-gabriella-local-session",
        )
        bridge = self.brain_bridge.to_core_intent(packet, transcript)
        llm_result = self.llm.deliberate(
            user_text=transcript.text,
            brain_packet=packet.to_dict(),
            approved_memories=tuple(record.text for record in self.memory.list()),
        )
        local_intent = self.parser.parse(transcript)
        local_question_text = local_intent.normalized_text
        complex_question = any(
            signal in local_question_text
            for signal in (
                "plan",
                "prepare",
                "strategy",
                "compare",
                "analyze",
                "research",
                "organize",
                "project",
                "roadmap",
                "architecture",
                "workflow",
                "upgrade",
                "design",
                "investigate",
                "summarize",
                "recommend",
                "diagnose",
                "decide",
                "evaluate",
                "build",
                "create",
                "launch",
                "monetize",
            )
        )
        if local_intent.kind in {IntentKind.SMALL_TALK, IntentKind.SHOW_HELP} and local_intent.confidence >= 0.70:
            intent = local_intent
        elif local_intent.kind == IntentKind.ANSWER_QUESTION and local_intent.confidence >= 0.60 and not complex_question:
            intent = local_intent
        else:
            intent = bridge.intent or local_intent
        plan = self.planner.plan(intent)
        policy = self.policy.evaluate(plan)
        receipt_ids: list[str] = []
        receipt_ids.append(
            self.receipts.append(
                intent_id=intent.intent_id,
                event_type=ReceiptEventType.TRANSCRIPT_RECEIVED,
                summary="User transcript received.",
                metadata={"transcript": transcript.to_dict()},
            ).receipt_id
        )
        receipt_ids.append(
            self.receipts.append(
                intent_id=intent.intent_id,
                event_type=ReceiptEventType.BRAIN_PACKET_CREATED,
                summary=bridge.receipt_summary,
                metadata={"brain_packet": packet.to_dict()},
            ).receipt_id
        )
        receipt_ids.append(
            self.receipts.append(
                intent_id=intent.intent_id,
                event_type=ReceiptEventType.LLM_DELIBERATION_COMPLETED,
                summary=llm_result.reason,
                metadata={"llm": llm_result.to_dict()},
            ).receipt_id
        )
        receipt_ids.append(
            self.receipts.append(
                intent_id=intent.intent_id,
                event_type=ReceiptEventType.INTENT_DECODED,
                summary=f"Intent decoded as {intent.kind.value}.",
                metadata={"intent": intent.to_dict()},
            ).receipt_id
        )
        receipt_ids.append(
            self.receipts.append(
                intent_id=intent.intent_id,
                event_type=ReceiptEventType.ACTION_PLANNED,
                summary=plan.summary,
                metadata={"plan": plan.to_dict()},
            ).receipt_id
        )

        event = {
            PolicyOutcome.ALLOW: ReceiptEventType.POLICY_ALLOWED,
            PolicyOutcome.REQUIRE_CONFIRMATION: ReceiptEventType.POLICY_REVIEW_REQUIRED,
            PolicyOutcome.BLOCK: ReceiptEventType.POLICY_BLOCKED,
        }[policy.outcome]
        receipt_ids.append(
            self.receipts.append(
                intent_id=intent.intent_id,
                event_type=event,
                summary=policy.rationale,
                metadata={"policy": policy.to_dict()},
            ).receipt_id
        )

        if bridge.status_override == "waiting_for_clarification":
            response = llm_result.response_text or bridge.response_override or "I need one more detail before I can handle that."
            status = ActionStatus.WAITING_FOR_CLARIFICATION
            confirmation_prompt = None
        elif intent.kind == IntentKind.BRAIN_PLAN:
            response = llm_result.response_text or bridge.response_override or "I produced a reviewable cognitive plan."
            status = ActionStatus.COMPLETED
            confirmation_prompt = None
            receipt_ids.append(
                self.receipts.append(
                    intent_id=intent.intent_id,
                    event_type=ReceiptEventType.ACTION_COMPLETED,
                    summary="Brain plan produced with no external execution.",
                    metadata={"response_text": response, "plan_only": True},
                ).receipt_id
            )
        elif policy.outcome == PolicyOutcome.BLOCK:
            response = "I cannot do that. I can help with a safer alternative or clarify the request."
            status = ActionStatus.BLOCKED
            confirmation_prompt = None
        elif policy.outcome == PolicyOutcome.REQUIRE_CONFIRMATION:
            response = self._confirmation_text(transcript=transcript, plan=plan, brain_route=packet.route.route.value)
            status = ActionStatus.WAITING_FOR_CONFIRMATION
            confirmation_prompt = response
        else:
            response = self._execute_allowed_low_risk(plan.intent.kind, turn_plan=plan, llm_result=llm_result)
            status = ActionStatus.COMPLETED
            confirmation_prompt = None
            receipt_ids.append(
                self.receipts.append(
                    intent_id=intent.intent_id,
                    event_type=ReceiptEventType.ACTION_COMPLETED,
                    summary="Low-risk local action completed or prepared by Gabriella core.",
                    metadata={"response_text": response},
                ).receipt_id
            )

        return AssistantTurn(
            transcript=transcript,
            intent=intent,
            plan=plan,
            policy=policy,
            status=status,
            response_text=response,
            receipt_ids=tuple(receipt_ids),
            confirmation_prompt=confirmation_prompt,
            brain_packet={**packet.to_dict(), "llm": llm_result.to_dict()},
        )

    def confirm(self, turn: AssistantTurn, user_reply: str) -> AssistantTurn:
        decision = self.approval_gate.decide(plan=turn.plan, policy=turn.policy, user_reply=user_reply)
        if decision.approved:
            event = ReceiptEventType.APPROVAL_RECORDED
            status = ActionStatus.COMPLETED
            response = self._execute_after_approval(turn)
        else:
            event = ReceiptEventType.APPROVAL_REJECTED
            status = ActionStatus.BLOCKED
            response = "Canceled. Tell me the correction and I will rebuild the action preview."
        receipt = self.receipts.append(
            intent_id=turn.intent.intent_id,
            event_type=event,
            summary=decision.note,
            metadata={"approval": {"status": decision.status.value, "approved_text": decision.approved_text}},
        )
        receipt_ids = (*turn.receipt_ids, receipt.receipt_id)
        if decision.approved:
            receipt2 = self.receipts.append(
                intent_id=turn.intent.intent_id,
                event_type=ReceiptEventType.ACTION_COMPLETED,
                summary="Approved action completed or staged according to safe execution rules.",
                metadata={"response_text": response},
            )
            receipt_ids = (*receipt_ids, receipt2.receipt_id)
        return AssistantTurn(
            transcript=turn.transcript,
            intent=turn.intent,
            plan=turn.plan,
            policy=turn.policy,
            status=status,
            response_text=response,
            receipt_ids=receipt_ids,
            confirmation_prompt=None,
            brain_packet=turn.brain_packet,
        )

    def correct(self, turn: AssistantTurn, corrected_text: str) -> AssistantTurn:
        self.llm.record_correction(original=turn.transcript.text, corrected=corrected_text)
        self.receipts.append(
            intent_id=turn.intent.intent_id,
            event_type=ReceiptEventType.CORRECTION_RECORDED,
            summary="User supplied corrected intent text.",
            metadata={"original": turn.transcript.text, "corrected": corrected_text},
        )
        corrected = self.handle_text(corrected_text, mode=turn.transcript.mode)
        return AssistantTurn(
            transcript=corrected.transcript,
            intent=corrected.intent,
            plan=corrected.plan,
            policy=corrected.policy,
            status=ActionStatus.CORRECTED if corrected.status != ActionStatus.BLOCKED else corrected.status,
            response_text=corrected.response_text,
            receipt_ids=corrected.receipt_ids,
            confirmation_prompt=corrected.confirmation_prompt,
            brain_packet=corrected.brain_packet,
        )

    def export_receipts(self) -> str:
        return self.receipts.export_json()

    def _confirmation_text(self, *, transcript: Transcript, plan, brain_route: str | None = None) -> str:
        heard = transcript.text
        route_text = f" Brain route: {brain_route}." if brain_route else ""
        return (
            f"I heard: '{heard}'. I think you want me to: {plan.summary}. "
            f"Preview: {plan.preview}{route_text} Confirm before I act?"
        )

    def _execute_allowed_low_risk(self, kind: IntentKind, *, turn_plan, llm_result=None) -> str:
        intent = turn_plan.intent
        slots = intent.slots
        if kind == IntentKind.BRAIN_PLAN:
            return "IX-Gabriella-Brain produced a plan only. No external action was executed."
        if kind == IntentKind.SET_TIMER:
            value = int(slots.get("duration_value", 5))
            unit = str(slots.get("duration_unit", "minutes"))
            record = self.local_store.create_timer(
                duration_value=value,
                duration_unit=unit,
                original_text=intent.raw_text,
            )
            return f"Timer set locally: {record.title}."
        if kind == IntentKind.CREATE_NOTE:
            content = str(slots.get("content") or intent.raw_text)
            record = self.local_store.create_note(text=content, original_text=intent.raw_text)
            return f"Note saved locally: {record.title}."
        if kind == IntentKind.ADD_TO_LIST:
            item = str(slots.get("item") or intent.raw_text)
            list_name = str(slots.get("list_name") or "default")
            record = self.local_store.add_list_item(
                item=item,
                list_name=list_name,
                original_text=intent.raw_text,
            )
            return f"Added to {record.payload['list_name']} list: {record.payload['item']}."
        if kind == IntentKind.SET_REMINDER:
            text = str(slots.get("reminder_text") or intent.raw_text)
            record = self.local_store.create_reminder(text=text, original_text=intent.raw_text)
            return f"Reminder saved locally: {record.title}."
        if kind == IntentKind.WEB_SEARCH:
            query = str(slots.get("query") or intent.raw_text)
            self.local_store.save_draft(kind="search_request", title=query, body=query)
            return f"Search request prepared for review: {query}."
        if kind in {IntentKind.SMALL_TALK, IntentKind.SHOW_HELP}:
            return self.responder.answer(intent)
        if kind == IntentKind.ANSWER_QUESTION:
            return self.responder.answer(intent)
        if kind == IntentKind.MEMORY_READ:
            count = len(self.memory.list())
            return f"You have {count} approved memory record(s)."
        if kind == IntentKind.AD_PREFERENCE:
            decision = self.ad_policy.decide(screen_name="settings")
            return f"Ad preference screen ready. Policy: {decision.reason}."
        if kind == IntentKind.APP_SETTINGS:
            return (
                "Settings screen ready. Voice output, receipts, and confirmation behavior "
                "can be adjusted in the GUI."
            )
        if kind == IntentKind.SAFETY_STOP:
            return "Stopped. No pending action will be executed."
        return "I can answer or prepare this low-risk request."

    def _execute_after_approval(self, turn: AssistantTurn) -> str:
        slots = turn.intent.slots
        if turn.intent.kind == IntentKind.MEMORY_WRITE:
            text = str(slots.get("memory_text") or turn.transcript.text)
            record = self.memory.add(text, approved_by_user=True, tags=("user-approved", "brain-reviewed"))
            self.receipts.append(
                intent_id=turn.intent.intent_id,
                event_type=ReceiptEventType.MEMORY_WRITTEN,
                summary="Approved memory was saved.",
                metadata={"memory_id": record.memory_id, "brain_packet": slots.get("brain")},
            )
            return f"Saved to approved memory: {record.text}."
        if turn.intent.kind == IntentKind.EMAIL_DRAFT:
            recipient = str(slots.get("recipient_hint") or "unresolved recipient")
            body = str(slots.get("draft_body") or turn.transcript.text)
            record = self.local_store.save_draft(
                kind="email_draft",
                title=f"Email draft to {recipient}",
                body=body,
                metadata={"recipient_hint": recipient, "send_blocked_without_second_approval": True},
            )
            return (
                f"Email draft saved locally as {record.record_id}. "
                "I will not send it without a separate explicit send approval."
            )
        if turn.intent.kind == IntentKind.CALENDAR_DRAFT:
            body = str(slots.get("event_text") or turn.transcript.text)
            record = self.local_store.save_draft(kind="calendar_draft", title="Calendar draft", body=body)
            return (
                f"Calendar draft saved locally as {record.record_id}. "
                "I will not invite anyone without explicit approval."
            )
        if turn.intent.kind == IntentKind.SMART_HOME_CONTROL:
            device = str(slots.get("device") or "unresolved device")
            state = str(slots.get("requested_state") or "unresolved state")
            record = self.local_store.save_draft(
                kind="smart_home_stage",
                title=f"{device} {state}",
                body=turn.transcript.text,
                metadata={"device": device, "requested_state": state, "integration_required": True},
            )
            return (
                f"Smart-home command staged as {record.record_id}: {device} → {state}. "
                "A real device connector must verify the target before execution."
            )
        if turn.intent.kind == IntentKind.PRIVACY_CONTROL:
            return "Privacy-control action prepared. Review the affected data in settings before applying it."
        return self._execute_allowed_low_risk(turn.intent.kind, turn_plan=turn.plan)
