from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .hashing import stable_hash, utc_now_iso


@dataclass
class BrainState:
    notes: list[dict[str, Any]] = field(default_factory=list)
    lists: dict[str, list[str]] = field(default_factory=dict)
    timers: list[dict[str, Any]] = field(default_factory=list)
    reminders: list[dict[str, Any]] = field(default_factory=list)
    pending: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "notes": self.notes,
            "lists": self.lists,
            "timers": self.timers,
            "reminders": self.reminders,
            "pending": self.pending,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BrainState":
        return cls(
            notes=list(data.get("notes", [])),
            lists={str(k): list(v) for k, v in data.get("lists", {}).items()},
            timers=list(data.get("timers", [])),
            reminders=list(data.get("reminders", [])),
            pending=dict(data.get("pending", {})),
        )

    def commit_local(self, intent_name: str, slots: dict[str, Any]) -> dict[str, Any]:
        event = {"intent": intent_name, "slots": slots, "created_at": utc_now_iso()}
        event["local_id"] = "local-" + stable_hash(event)[:12]
        if intent_name == "set_timer":
            self.timers.append(event)
        elif intent_name == "create_reminder":
            self.reminders.append(event)
        elif intent_name == "take_note":
            self.notes.append(event)
        elif intent_name == "add_list_item":
            list_name = str(slots.get("list", "default")).strip() or "default"
            item = str(slots.get("item", "")).strip()
            self.lists.setdefault(list_name, []).append(item)
            event["list"] = list_name
            event["item"] = item
        return event

    def stage_pending(self, packet_id: str, action: dict[str, Any]) -> None:
        self.pending[packet_id] = {"action": action, "created_at": utc_now_iso()}

    def approve_pending(self, packet_id: str) -> dict[str, Any]:
        action = self.pending.pop(packet_id)
        action["approved_at"] = utc_now_iso()
        action["approved"] = True
        return action

    def reject_pending(self, packet_id: str) -> dict[str, Any]:
        action = self.pending.pop(packet_id)
        action["rejected_at"] = utc_now_iso()
        action["approved"] = False
        return action


class StateRepository:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else None
        self.state = BrainState()
        if self.path and self.path.exists():
            self.state = BrainState.from_dict(json.loads(self.path.read_text(encoding="utf-8")))

    def save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.state.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
