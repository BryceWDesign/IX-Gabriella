from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

REQUIRED_KEYS = {
    "assistant_response": str,
    "confidence": (int, float),
    "risk": str,
    "requested_tool": (str, type(None)),
    "requires_user_approval": bool,
    "memory_write_requested": bool,
}
ALLOWED_RISKS = {"low", "medium", "high"}


@dataclass(frozen=True, slots=True)
class StructuredValidation:
    valid: bool
    packet: dict[str, Any]
    errors: tuple[str, ...]
    repaired: bool = False


def extract_json_object(text: str) -> dict[str, Any] | None:
    clean = text.strip()
    if clean.startswith("{") and clean.endswith("}"):
        try:
            value = json.loads(clean)
            return value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            return None
    start = clean.find("{")
    end = clean.rfind("}")
    if start >= 0 and end > start:
        try:
            value = json.loads(clean[start : end + 1])
            return value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def validate_structured_output(text: str, *, allowed_tools: tuple[str, ...]) -> StructuredValidation:
    packet = extract_json_object(text)
    if packet is None:
        return StructuredValidation(False, {}, ("not_json_object",))
    errors: list[str] = []
    for key, expected in REQUIRED_KEYS.items():
        if key not in packet:
            errors.append(f"missing:{key}")
            continue
        if not isinstance(packet[key], expected):
            errors.append(f"wrong_type:{key}")
    risk = str(packet.get("risk", "")).lower()
    if risk not in ALLOWED_RISKS:
        errors.append("invalid:risk")
    requested_tool = packet.get("requested_tool")
    if requested_tool is not None and requested_tool not in allowed_tools:
        errors.append("invalid:requested_tool")
    confidence = packet.get("confidence", 0.0)
    try:
        conf = float(confidence)
        if not 0.0 <= conf <= 1.0:
            errors.append("invalid:confidence_range")
        else:
            packet["confidence"] = conf
    except (TypeError, ValueError):
        errors.append("invalid:confidence_number")
    if errors:
        return StructuredValidation(False, packet, tuple(errors))
    packet["risk"] = risk
    packet["assistant_response"] = " ".join(str(packet["assistant_response"]).strip().split())
    return StructuredValidation(True, packet, ())


def deterministic_repair(text: str, *, allowed_tools: tuple[str, ...]) -> StructuredValidation:
    packet = extract_json_object(text) or {}
    response = str(packet.get("assistant_response") or text or "I need one more detail before I can proceed.")
    requested_tool = packet.get("requested_tool") if packet.get("requested_tool") in allowed_tools else None
    repaired = {
        "assistant_response": " ".join(response.strip().split())[:2400],
        "confidence": max(0.0, min(1.0, float(packet.get("confidence", 0.55) or 0.55))),
        "risk": str(packet.get("risk") or "medium").lower() if str(packet.get("risk") or "medium").lower() in ALLOWED_RISKS else "medium",
        "requested_tool": requested_tool,
        "requires_user_approval": bool(packet.get("requires_user_approval", True)),
        "memory_write_requested": bool(packet.get("memory_write_requested", False)),
    }
    return StructuredValidation(True, repaired, (), repaired=True)
