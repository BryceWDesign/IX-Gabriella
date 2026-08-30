from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum, auto
from threading import RLock
from typing import Any

from ix_assistant_core.models import new_id, utc_now


class ReceiptEventType(StrEnum):
    TRANSCRIPT_RECEIVED = auto()
    INTENT_DECODED = auto()
    ACTION_PLANNED = auto()
    POLICY_ALLOWED = auto()
    POLICY_REVIEW_REQUIRED = auto()
    POLICY_BLOCKED = auto()
    APPROVAL_RECORDED = auto()
    APPROVAL_REJECTED = auto()
    ACTION_COMPLETED = auto()
    ACTION_BLOCKED = auto()
    CORRECTION_RECORDED = auto()
    MEMORY_WRITTEN = auto()
    MEMORY_REJECTED = auto()
    PRIVACY_EVENT = auto()
    AD_POLICY_EVENT = auto()
    BRAIN_PACKET_CREATED = auto()
    LLM_DELIBERATION_COMPLETED = auto()


@dataclass(frozen=True, slots=True)
class ReceiptRecord:
    receipt_id: str
    intent_id: str
    event_type: ReceiptEventType
    summary: str
    previous_receipt_id: str | None
    previous_chain_digest: str | None
    chain_digest: str
    created_at: datetime
    actor: str = "ix-gabriella"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "intent_id": self.intent_id,
            "event_type": self.event_type.value,
            "summary": self.summary,
            "previous_receipt_id": self.previous_receipt_id,
            "previous_chain_digest": self.previous_chain_digest,
            "chain_digest": self.chain_digest,
            "created_at": self.created_at.isoformat(),
            "actor": self.actor,
            "metadata": self.metadata,
        }


class ReceiptLedger:
    """Thread-safe tamper-evident receipt chain per assistant intent."""

    def __init__(self) -> None:
        self._records: list[ReceiptRecord] = []
        self._lock = RLock()

    def append(
        self,
        *,
        intent_id: str,
        event_type: ReceiptEventType,
        summary: str,
        metadata: dict[str, Any] | None = None,
        actor: str = "ix-gabriella",
    ) -> ReceiptRecord:
        clean_intent_id = _normalize_id(intent_id)
        clean_summary = summary.strip()
        if not clean_summary:
            raise ValueError("summary must not be empty")
        metadata = dict(metadata or {})
        with self._lock:
            previous = self.latest_for_intent(clean_intent_id)
            previous_receipt_id = None if previous is None else previous.receipt_id
            previous_chain_digest = None if previous is None else previous.chain_digest
            receipt_id = new_id("receipt")
            created_at = utc_now()
            digest = _digest(
                receipt_id=receipt_id,
                intent_id=clean_intent_id,
                event_type=event_type.value,
                summary=clean_summary,
                previous_chain_digest=previous_chain_digest,
                actor=actor,
                metadata=metadata,
            )
            record = ReceiptRecord(
                receipt_id=receipt_id,
                intent_id=clean_intent_id,
                event_type=event_type,
                summary=clean_summary,
                previous_receipt_id=previous_receipt_id,
                previous_chain_digest=previous_chain_digest,
                chain_digest=digest,
                created_at=created_at,
                actor=actor,
                metadata=metadata,
            )
            self._records.append(record)
            return record

    def records(self) -> tuple[ReceiptRecord, ...]:
        with self._lock:
            return tuple(self._records)

    def latest_for_intent(self, intent_id: str) -> ReceiptRecord | None:
        clean_intent_id = _normalize_id(intent_id)
        for record in reversed(self._records):
            if record.intent_id == clean_intent_id:
                return record
        return None

    def filter_by_intent(self, intent_id: str) -> tuple[ReceiptRecord, ...]:
        clean_intent_id = _normalize_id(intent_id)
        return tuple(record for record in self.records() if record.intent_id == clean_intent_id)

    def verify_intent_chain(self, intent_id: str) -> bool:
        previous: ReceiptRecord | None = None
        for record in self.filter_by_intent(intent_id):
            expected_previous_id = None if previous is None else previous.receipt_id
            expected_previous_digest = None if previous is None else previous.chain_digest
            if record.previous_receipt_id != expected_previous_id:
                return False
            if record.previous_chain_digest != expected_previous_digest:
                return False
            expected_digest = _digest(
                receipt_id=record.receipt_id,
                intent_id=record.intent_id,
                event_type=record.event_type.value,
                summary=record.summary,
                previous_chain_digest=record.previous_chain_digest,
                actor=record.actor,
                metadata=record.metadata,
            )
            if record.chain_digest != expected_digest:
                return False
            previous = record
        return True

    def export_json(self) -> str:
        payload = [record.to_dict() for record in self.records()]
        return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)


def _normalize_id(value: str) -> str:
    cleaned = value.strip().lower().replace("_", "-").replace(" ", "-")
    if not cleaned:
        raise ValueError("identifier must not be empty")
    return cleaned


def _digest(
    *,
    receipt_id: str,
    intent_id: str,
    event_type: str,
    summary: str,
    previous_chain_digest: str | None,
    actor: str,
    metadata: dict[str, Any],
) -> str:
    payload = {
        "receipt_id": receipt_id,
        "intent_id": intent_id,
        "event_type": event_type,
        "summary": summary,
        "previous_chain_digest": previous_chain_digest,
        "actor": actor,
        "metadata": metadata,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
