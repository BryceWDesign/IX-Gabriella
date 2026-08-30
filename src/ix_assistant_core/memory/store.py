from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ix_assistant_core.models import new_id, utc_now


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    memory_id: str
    text: str
    approved_by_user: bool
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "memory_id": self.memory_id,
            "text": self.text,
            "approved_by_user": self.approved_by_user,
            "created_at": self.created_at,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "MemoryRecord":
        return cls(
            memory_id=str(payload["memory_id"]),
            text=str(payload["text"]),
            approved_by_user=bool(payload["approved_by_user"]),
            created_at=str(payload["created_at"]),
            tags=tuple(str(item) for item in payload.get("tags", [])),
        )


class MemoryStore:
    """Opt-in memory store.

    The store rejects writes unless the caller marks them as approved by the
    user. This enforces the product promise that memory is visible, reversible,
    and never silently taken from private conversation.
    """

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self._records: list[MemoryRecord] = []
        if path is not None and path.exists():
            self._records = [MemoryRecord.from_dict(item) for item in json.loads(path.read_text())]

    def add(self, text: str, *, approved_by_user: bool, tags: tuple[str, ...] = ()) -> MemoryRecord:
        clean = " ".join(text.strip().split())
        if not clean:
            raise ValueError("memory text must not be empty")
        if not approved_by_user:
            raise PermissionError("memory writes require explicit user approval")
        record = MemoryRecord(
            memory_id=new_id("memory"),
            text=clean,
            approved_by_user=True,
            tags=tuple(tag.strip().lower() for tag in tags if tag.strip()),
        )
        self._records.append(record)
        self._save()
        return record

    def list(self) -> tuple[MemoryRecord, ...]:
        return tuple(self._records)

    def forget(self, memory_id: str) -> bool:
        before = len(self._records)
        self._records = [record for record in self._records if record.memory_id != memory_id]
        changed = len(self._records) != before
        if changed:
            self._save()
        return changed

    def clear(self) -> None:
        self._records.clear()
        self._save()

    def _save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps([record.to_dict() for record in self._records], indent=2)
        self.path.write_text(payload, encoding="utf-8")
