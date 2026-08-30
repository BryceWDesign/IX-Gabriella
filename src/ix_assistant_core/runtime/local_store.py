from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any

from ix_assistant_core.models import new_id, utc_now


@dataclass(frozen=True, slots=True)
class LocalActionRecord:
    record_id: str
    kind: str
    title: str
    payload: dict[str, Any]
    created_at: str = field(default_factory=lambda: utc_now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "kind": self.kind,
            "title": self.title,
            "payload": self.payload,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LocalActionRecord":
        return cls(
            record_id=str(payload["record_id"]),
            kind=str(payload["kind"]),
            title=str(payload["title"]),
            payload=dict(payload.get("payload", {})),
            created_at=str(payload["created_at"]),
        )


class LocalActionStore:
    """Small durable local store for actions Gabriella can safely perform today."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self._records: list[LocalActionRecord] = []
        if path is not None and path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            self._records = [LocalActionRecord.from_dict(item) for item in raw]

    @classmethod
    def default_user_store(cls) -> "LocalActionStore":
        return cls(Path.home() / ".ix-gabriella" / "local_actions.json")

    def create_timer(
        self,
        *,
        duration_value: int,
        duration_unit: str,
        original_text: str,
    ) -> LocalActionRecord:
        seconds = _duration_to_seconds(duration_value, duration_unit)
        due_at = utc_now() + timedelta(seconds=seconds)
        return self._append(
            kind="timer",
            title=f"{duration_value} {duration_unit} timer",
            payload={"duration_seconds": seconds, "due_at": due_at.isoformat(), "source_text": original_text},
        )

    def create_reminder(self, *, text: str, original_text: str) -> LocalActionRecord:
        clean = _clean_text(text) or _clean_text(original_text)
        return self._append(
            kind="reminder",
            title=clean[:80],
            payload={"reminder_text": clean, "source_text": original_text},
        )

    def create_note(self, *, text: str, original_text: str) -> LocalActionRecord:
        clean = _clean_text(text) or _clean_text(original_text)
        return self._append(
            kind="note",
            title=clean[:80],
            payload={"note_text": clean, "source_text": original_text},
        )

    def add_list_item(
        self,
        *,
        item: str,
        list_name: str = "default",
        original_text: str = "",
    ) -> LocalActionRecord:
        clean_item = _clean_text(item)
        clean_list = _clean_text(list_name).lower() or "default"
        if not clean_item:
            clean_item = _clean_text(original_text)
        return self._append(
            kind="list_item",
            title=f"{clean_list}: {clean_item[:60]}",
            payload={"list_name": clean_list, "item": clean_item, "source_text": original_text},
        )

    def save_draft(
        self,
        *,
        kind: str,
        title: str,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> LocalActionRecord:
        if kind not in {"email_draft", "calendar_draft", "smart_home_stage", "search_request"}:
            raise ValueError("unsupported draft kind")
        return self._append(
            kind=kind,
            title=_clean_text(title)[:80] or kind.replace("_", " "),
            payload={"body": _clean_text(body), "metadata": dict(metadata or {})},
        )

    def list_records(self, *, kind: str | None = None) -> tuple[LocalActionRecord, ...]:
        if kind is None:
            return tuple(self._records)
        return tuple(record for record in self._records if record.kind == kind)

    def clear(self) -> None:
        self._records.clear()
        self._save()

    def _append(self, *, kind: str, title: str, payload: dict[str, Any]) -> LocalActionRecord:
        record = LocalActionRecord(
            record_id=new_id(kind),
            kind=kind,
            title=_clean_text(title),
            payload=payload,
        )
        self._records.append(record)
        self._save()
        return record

    def _save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        payload = json.dumps(
            [record.to_dict() for record in self._records],
            indent=2,
            sort_keys=True,
        )
        temp.write_text(payload, encoding="utf-8")
        temp.replace(self.path)


def _duration_to_seconds(value: int, unit: str) -> int:
    clean_unit = unit.lower().rstrip("s")
    multipliers = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}
    if clean_unit not in multipliers:
        raise ValueError("unsupported duration unit")
    if value <= 0:
        raise ValueError("duration must be positive")
    return value * multipliers[clean_unit]


def _clean_text(value: str) -> str:
    return " ".join(value.strip().split())
