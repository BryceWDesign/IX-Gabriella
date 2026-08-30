from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from ix_assistant_core.models import DecodedIntent, IntentKind, Transcript, new_id

_WORD_RE = re.compile(r"[a-z0-9']+")
_TIME_RE = re.compile(r"\b(?:in\s+)?(\d+)\s*(second|seconds|minute|minutes|hour|hours|day|days)\b", re.I)
_WAKE_WORDS_RE = re.compile(r"\b(?:hey|hi|okay|ok)\s+(?:gabriella|gabriela|gabby|gabi)\b[,\s]*", re.I)


@dataclass(frozen=True, slots=True)
class IntentRule:
    kind: IntentKind
    keywords: tuple[str, ...]
    confidence: float
    target: str | None = None
    requires_object: bool = False


class RuleBasedIntentParser:
    """Deterministic first-pass intent decoder for governed assistant actions."""

    def __init__(self, rules: Iterable[IntentRule] | None = None) -> None:
        self.rules = tuple(rules or _default_rules())

    def parse(self, transcript: Transcript) -> DecodedIntent:
        normalized = _normalize(transcript.text)
        tokens = set(_WORD_RE.findall(normalized))
        best_rule: IntentRule | None = None
        best_hits: list[str] = []

        for rule in self.rules:
            hits = [keyword for keyword in rule.keywords if keyword in normalized or keyword in tokens]
            if not hits:
                continue
            if best_rule is None or len(hits) > len(best_hits) or rule.confidence > best_rule.confidence:
                best_rule = rule
                best_hits = hits

        if best_rule is None:
            confidence = _with_acoustic(transcript, 0.20)
            return DecodedIntent(
                intent_id=new_id("intent"),
                kind=IntentKind.UNKNOWN,
                raw_text=transcript.text,
                normalized_text=normalized,
                confidence=round(confidence, 6),
                uncertainty=round(1.0 - confidence, 6),
                slots={"original_text": transcript.text},
                reasons=("no-rule-match",),
            )

        object_penalty = 0.0
        slots = _extract_slots(best_rule.kind, normalized, transcript.text)
        if best_rule.requires_object and _looks_objectless(normalized, best_hits, slots):
            object_penalty = 0.18
        alternative_penalty = min(0.12, 0.04 * len(transcript.alternatives))
        confidence = _with_acoustic(
            transcript,
            max(0.0, best_rule.confidence - object_penalty - alternative_penalty),
        )
        if transcript.alternatives:
            slots["transcript_alternatives"] = list(transcript.alternatives)
        reasons = ["rule-match", *[f"hit:{hit}" for hit in best_hits]]
        if object_penalty:
            reasons.append("missing-specific-object")
        if transcript.acoustic_confidence is not None:
            reasons.append("acoustic-confidence-applied")
        return DecodedIntent(
            intent_id=new_id("intent"),
            kind=best_rule.kind,
            raw_text=transcript.text,
            normalized_text=normalized,
            confidence=round(confidence, 6),
            uncertainty=round(max(0.0, 1.0 - confidence), 6),
            target=best_rule.target,
            slots=slots,
            reasons=tuple(reasons),
        )


def _default_rules() -> tuple[IntentRule, ...]:
    return (
        IntentRule(IntentKind.SAFETY_STOP, ("stop", "cancel", "never mind", "abort"), 0.95),
        IntentRule(
            IntentKind.SHOW_HELP,
            ("help", "what can you do", "capabilities", "commands"),
            0.90,
            "help",
        ),
        IntentRule(
            IntentKind.SMALL_TALK,
            ("hello", "hi", "good morning", "good afternoon", "good evening", "who are you", "your name"),
            0.86,
            "conversation",
        ),
        IntentRule(IntentKind.SET_TIMER, ("timer", "countdown"), 0.88, "timer"),
        IntentRule(IntentKind.SET_REMINDER, ("remind", "reminder"), 0.86, "reminder", True),
        IntentRule(
            IntentKind.CREATE_NOTE,
            ("note", "write down", "take a note", "remember this note"),
            0.82,
            "note",
            True,
        ),
        IntentRule(IntentKind.ADD_TO_LIST, ("list", "add", "shopping"), 0.76, "list", True),
        IntentRule(
            IntentKind.CALENDAR_DRAFT,
            ("calendar", "meeting", "schedule", "appointment"),
            0.78,
            "calendar",
            True,
        ),
        IntentRule(IntentKind.EMAIL_DRAFT, ("email", "mail", "message"), 0.77, "email", True),
        IntentRule(
            IntentKind.SMART_HOME_CONTROL,
            ("light", "lights", "thermostat", "door", "lock", "unlock", "garage", "oven", "stove"),
            0.74,
            "smart-home",
            True,
        ),
        IntentRule(IntentKind.MEMORY_WRITE, ("remember that", "save this", "memorize"), 0.80, "memory", True),
        IntentRule(IntentKind.MEMORY_READ, ("what do you remember", "recall", "memory"), 0.79, "memory"),
        IntentRule(
            IntentKind.PRIVACY_CONTROL,
            ("delete history", "privacy", "forget", "erase", "data"),
            0.84,
            "privacy",
        ),
        IntentRule(IntentKind.AD_PREFERENCE, ("ads", "advertising", "hide ad", "ad preference"), 0.82, "ads"),
        IntentRule(IntentKind.APP_SETTINGS, ("settings", "voice", "tone", "verbosity"), 0.72, "settings"),
        IntentRule(IntentKind.WEB_SEARCH, ("search", "look up", "find", "google"), 0.73, "search", True),
        IntentRule(
            IntentKind.ANSWER_QUESTION,
            ("what", "why", "how", "who", "when", "where"),
            0.68,
            "answer",
        ),
    )


def _normalize(text: str) -> str:
    text = _WAKE_WORDS_RE.sub("", text)
    return " ".join(text.lower().strip().replace("’", "'").split())


def _with_acoustic(transcript: Transcript, semantic_confidence: float) -> float:
    if transcript.acoustic_confidence is None:
        return semantic_confidence
    return max(0.0, min(1.0, 0.65 * semantic_confidence + 0.35 * transcript.acoustic_confidence))


def _looks_objectless(text: str, hits: list[str], slots: dict[str, object]) -> bool:
    if any(
        key in slots
        for key in ("content", "item", "recipient_hint", "device", "query", "memory_text", "reminder_text")
    ):
        return False
    remainder = text
    for hit in hits:
        remainder = remainder.replace(hit, " ")
    remainder = remainder.replace("please", " ").replace("can you", " ").strip()
    return len(_WORD_RE.findall(remainder)) < 2


def _extract_slots(kind: IntentKind, normalized: str, raw_text: str) -> dict[str, object]:
    slots: dict[str, object] = {"original_text": raw_text}
    if match := _TIME_RE.search(normalized):
        slots["duration_value"] = int(match.group(1))
        slots["duration_unit"] = match.group(2).lower()
    if kind == IntentKind.SMART_HOME_CONTROL:
        for state in ("on", "off", "lock", "unlock", "open", "close", "raise", "lower"):
            if re.search(rf"\b{state}\b", normalized):
                slots["requested_state"] = state
                break
        device = _device_from_smart_home(normalized)
        if device:
            slots["device"] = device
    elif kind == IntentKind.CREATE_NOTE:
        slots["content"] = _strip_prefix(normalized, ("take a note", "write down", "note"))
    elif kind == IntentKind.ADD_TO_LIST:
        list_slots = _list_slots(normalized)
        slots.update(list_slots)
    elif kind == IntentKind.SET_REMINDER:
        slots["reminder_text"] = _strip_prefix(
            normalized,
            ("remind me to", "remind me", "reminder to", "reminder"),
        )
    elif kind == IntentKind.EMAIL_DRAFT:
        slots["draft_only"] = True
        slots.update(_email_slots(normalized))
    elif kind == IntentKind.CALENDAR_DRAFT:
        slots["draft_only"] = True
        slots["event_text"] = _strip_prefix(normalized, ("schedule", "calendar", "meeting", "appointment"))
    elif kind == IntentKind.WEB_SEARCH:
        slots["query"] = _strip_prefix(normalized, ("search for", "search", "look up", "find", "google"))
    elif kind == IntentKind.MEMORY_WRITE:
        slots["memory_text"] = _strip_prefix(normalized, ("remember that", "save this", "memorize"))
    return slots


def _strip_prefix(text: str, prefixes: tuple[str, ...]) -> str:
    clean = text.strip()
    for prefix in prefixes:
        if clean.startswith(prefix):
            clean = clean[len(prefix):].strip(" ,.:;")
            break
    return clean


def _list_slots(text: str) -> dict[str, object]:
    match = re.search(r"\badd\s+(.+?)\s+to\s+(?:my\s+)?(.+?)\s+list\b", text)
    if match:
        return {"item": match.group(1).strip(), "list_name": match.group(2).strip()}
    if "shopping" in text:
        item = _strip_prefix(text, ("add", "shopping list", "list"))
        item = item.replace("to my shopping list", "").replace("to shopping list", "").strip(" ,.:;")
        return {"item": item, "list_name": "shopping"}
    return {"item": _strip_prefix(text, ("add", "list")), "list_name": "default"}


def _email_slots(text: str) -> dict[str, object]:
    match = re.search(r"\b(?:email|mail|message)\s+(.+?)\s+that\s+(.+)$", text)
    if match:
        return {"recipient_hint": match.group(1).strip(), "draft_body": match.group(2).strip()}
    return {"draft_body": _strip_prefix(text, ("email", "mail", "message"))}


def _device_from_smart_home(text: str) -> str:
    clean = re.sub(
        r"\b(turn|switch|set|please|the|my|to|on|off|lock|unlock|open|close|raise|lower)\b",
        " ",
        text,
    )
    clean = " ".join(clean.split())
    return clean.strip(" ,.:;")
