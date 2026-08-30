from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Pattern

from .models import IntentCandidate, RiskLevel
from .text import clip01, lower_ascii, token_overlap

_DURATION_RE = re.compile(r"(?P<amount>\d+(?:\.\d+)?)\s*(?P<unit>seconds?|secs?|minutes?|mins?|hours?|hrs?|days?)")
_TIME_HINT_RE = re.compile(r"\b(today|tomorrow|tonight|morning|afternoon|evening|\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b")
_LIST_RE = re.compile(r"\badd\s+(?P<item>.+?)\s+to\s+(?:my\s+)?(?P<list>[a-z0-9 '\-]+?)\s+list\b")
_NOTE_RE = re.compile(r"\b(?:take|make|save)\s+(?:a\s+)?note(?:\s+that|\s*:)?\s+(?P<note>.+)")
_MEMORY_RE = re.compile(r"\b(?:remember|memorize)\s+(?:that\s+)?(?P<memory>.+)")
_REMIND_RE = re.compile(r"\bremind\s+me\s+(?:to\s+)?(?P<task>.+)")
_EMAIL_RE = re.compile(r"\b(?:draft|write|compose|email)\s+(?:an\s+)?(?:email\s+)?(?:(?:to|for)\s+(?P<recipient>[a-z0-9@._ '\-]+)\s*)?(?P<body>.+)?")
_CALENDAR_RE = re.compile(r"\b(?:schedule|calendar|book|put)\s+(?P<event>.+)")
_SMART_HOME_RE = re.compile(r"\b(?:turn|switch)\s+(?P<state>on|off)\s+(?P<device>.+)")
_SEARCH_RE = re.compile(r"\b(?:search|look\s+up|find\s+out|research)\s+(?P<query>.+)")
_CORRECT_RE = re.compile(r"\b(?:no|correct|correction|change\s+that|i\s+meant)\b(?P<correction>.*)")


@dataclass(frozen=True)
class FastIntentDefinition:
    name: str
    examples: tuple[str, ...]
    risk: RiskLevel
    requires_approval: bool
    required_slots: tuple[str, ...]
    patterns: tuple[Pattern[str], ...]
    local_execution_allowed: bool = False


class FastIntentRegistry:
    def __init__(self, definitions: tuple[FastIntentDefinition, ...] | None = None) -> None:
        self.definitions = definitions or default_fast_intents()

    def match(self, text: str) -> IntentCandidate | None:
        cleaned = lower_ascii(text)
        best: IntentCandidate | None = None
        for definition in self.definitions:
            slots, evidence, regex_score = self._extract(definition, cleaned)
            example_score = max((token_overlap(cleaned, ex) for ex in definition.examples), default=0.0)
            name_signal = 0.18 if definition.name.replace("_", " ") in cleaned else 0.0
            score = clip01(max(regex_score, example_score + name_signal))
            if score <= 0.20:
                continue
            missing = tuple(slot for slot in definition.required_slots if not slots.get(slot))
            confidence = clip01(score - 0.10 * len(missing))
            candidate = IntentCandidate(
                name=definition.name,
                confidence=confidence,
                risk=definition.risk,
                requires_approval=definition.requires_approval,
                missing_slots=missing,
                slots=slots,
                evidence=evidence,
            )
            if best is None or candidate.confidence > best.confidence:
                best = candidate
        return best

    def get_definition(self, name: str) -> FastIntentDefinition | None:
        for definition in self.definitions:
            if definition.name == name:
                return definition
        return None

    def _extract(self, definition: FastIntentDefinition, text: str) -> tuple[dict[str, Any], tuple[str, ...], float]:
        slots: dict[str, Any] = {}
        evidence: list[str] = []
        regex_score = 0.0
        for pattern in definition.patterns:
            match = pattern.search(text)
            if not match:
                continue
            regex_score = max(regex_score, 0.90)
            evidence.append(f"matched:{pattern.pattern}")
            slots.update({key: value.strip() for key, value in match.groupdict().items() if value and value.strip()})
        if definition.name == "set_timer":
            duration = _DURATION_RE.search(text)
            if duration:
                amount = float(duration.group("amount"))
                unit = duration.group("unit")
                slots["duration"] = {"amount": amount, "unit": unit}
                evidence.append("duration_extracted")
                regex_score = max(regex_score, 0.95)
        if definition.name == "create_reminder":
            time_hint = _TIME_HINT_RE.search(text)
            if time_hint:
                slots["time_hint"] = time_hint.group(0)
                evidence.append("time_hint_extracted")
            if slots.get("task"):
                regex_score = max(regex_score, 0.86)
        if definition.name == "email_draft" and slots.get("recipient") and not slots.get("body"):
            recipient_text = str(slots["recipient"])
            for separator in (" saying ", " that "):
                if separator in recipient_text:
                    recipient, body = recipient_text.split(separator, 1)
                    slots["recipient"] = recipient.strip()
                    slots["body"] = body.strip()
                    evidence.append("email_body_split_from_recipient_phrase")
                    regex_score = max(regex_score, 0.92)
                    break
        if definition.name == "approve_pending" and text in {"yes", "approve", "approved", "confirm", "do it", "go ahead"}:
            slots["approval"] = True
            regex_score = max(regex_score, 0.98)
        if definition.name == "reject_pending" and text in {"no", "reject", "cancel", "do not", "stop"}:
            slots["approval"] = False
            regex_score = max(regex_score, 0.98)
        return slots, tuple(evidence), regex_score


def default_fast_intents() -> tuple[FastIntentDefinition, ...]:
    return (
        FastIntentDefinition(
            name="set_timer",
            examples=("set a timer for 10 minutes", "start a five minute timer", "timer 20 minutes"),
            risk=RiskLevel.LOW,
            requires_approval=False,
            required_slots=("duration",),
            patterns=(re.compile(r"\b(?:set|start|create)?\s*(?:a\s+)?timer\b"),),
            local_execution_allowed=True,
        ),
        FastIntentDefinition(
            name="create_reminder",
            examples=("remind me tomorrow to call", "remind me to take medicine at 8", "set a reminder"),
            risk=RiskLevel.LOW,
            requires_approval=False,
            required_slots=("task", "time_hint"),
            patterns=(_REMIND_RE,),
            local_execution_allowed=True,
        ),
        FastIntentDefinition(
            name="take_note",
            examples=("take a note", "save a note that", "make note of this"),
            risk=RiskLevel.LOW,
            requires_approval=False,
            required_slots=("note",),
            patterns=(_NOTE_RE,),
            local_execution_allowed=True,
        ),
        FastIntentDefinition(
            name="add_list_item",
            examples=("add milk to my grocery list", "add batteries to shopping list"),
            risk=RiskLevel.LOW,
            requires_approval=False,
            required_slots=("item", "list"),
            patterns=(_LIST_RE,),
            local_execution_allowed=True,
        ),
        FastIntentDefinition(
            name="memory_proposal",
            examples=("remember that I prefer", "memorize that my default", "remember this"),
            risk=RiskLevel.MEDIUM,
            requires_approval=True,
            required_slots=("memory",),
            patterns=(_MEMORY_RE,),
            local_execution_allowed=False,
        ),
        FastIntentDefinition(
            name="email_draft",
            examples=("draft an email to John", "write email saying I am late", "email Sarah that"),
            risk=RiskLevel.HIGH,
            requires_approval=True,
            required_slots=("body",),
            patterns=(_EMAIL_RE,),
            local_execution_allowed=False,
        ),
        FastIntentDefinition(
            name="calendar_draft",
            examples=("schedule a meeting", "put lunch on my calendar", "book a call tomorrow"),
            risk=RiskLevel.MEDIUM,
            requires_approval=True,
            required_slots=("event",),
            patterns=(_CALENDAR_RE,),
            local_execution_allowed=False,
        ),
        FastIntentDefinition(
            name="search_request",
            examples=("search for", "look up", "research this"),
            risk=RiskLevel.MEDIUM,
            requires_approval=True,
            required_slots=("query",),
            patterns=(_SEARCH_RE,),
            local_execution_allowed=False,
        ),
        FastIntentDefinition(
            name="smart_home_stage",
            examples=("turn off the lights", "switch on bedroom fan", "turn on kitchen lamp"),
            risk=RiskLevel.MEDIUM,
            requires_approval=True,
            required_slots=("state", "device"),
            patterns=(_SMART_HOME_RE,),
            local_execution_allowed=False,
        ),
        FastIntentDefinition(
            name="approve_pending",
            examples=("yes", "approve", "confirm", "go ahead", "do it"),
            risk=RiskLevel.LOW,
            requires_approval=False,
            required_slots=("approval",),
            patterns=(re.compile(r"\b(?:yes|approve|confirm|go\s+ahead|do\s+it)\b"),),
            local_execution_allowed=True,
        ),
        FastIntentDefinition(
            name="reject_pending",
            examples=("no", "reject", "cancel that", "do not", "stop"),
            risk=RiskLevel.LOW,
            requires_approval=False,
            required_slots=("approval",),
            patterns=(re.compile(r"\b(?:no|reject|cancel|do\s+not|stop)\b"),),
            local_execution_allowed=True,
        ),
        FastIntentDefinition(
            name="correct_pending",
            examples=("no I meant", "correct that", "change that to"),
            risk=RiskLevel.LOW,
            requires_approval=False,
            required_slots=(),
            patterns=(_CORRECT_RE,),
            local_execution_allowed=True,
        ),
    )
