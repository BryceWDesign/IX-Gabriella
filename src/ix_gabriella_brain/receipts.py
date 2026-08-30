from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .hashing import stable_hash, utc_now_iso


@dataclass
class ReceiptLedger:
    path: Path | None = None
    entries: list[dict[str, Any]] = field(default_factory=list)

    def append(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        previous_hash = self.entries[-1]["receipt_hash"] if self.entries else "GENESIS"
        entry_without_hash = {
            "kind": kind,
            "payload": payload,
            "previous_hash": previous_hash,
            "created_at": utc_now_iso(),
        }
        receipt_hash = stable_hash(entry_without_hash)
        entry = {**entry_without_hash, "receipt_hash": receipt_hash}
        self.entries.append(entry)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    def verify(self) -> bool:
        previous = "GENESIS"
        for entry in self.entries:
            expected_payload = {
                "kind": entry["kind"],
                "payload": entry["payload"],
                "previous_hash": previous,
                "created_at": entry["created_at"],
            }
            if entry.get("previous_hash") != previous:
                return False
            if stable_hash(expected_payload) != entry.get("receipt_hash"):
                return False
            previous = entry["receipt_hash"]
        return True

    def export(self) -> list[dict[str, Any]]:
        return list(self.entries)
