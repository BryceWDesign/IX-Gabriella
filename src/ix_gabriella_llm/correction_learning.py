from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CorrectionExample:
    original: str
    corrected: str
    note: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class CorrectionStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self._items: list[CorrectionExample] = []
        if path and path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            self._items = [CorrectionExample(**item) for item in raw]

    def add(self, *, original: str, corrected: str, note: str = "user_correction") -> CorrectionExample:
        item = CorrectionExample(original=original.strip(), corrected=corrected.strip(), note=note.strip())
        if item.original and item.corrected:
            self._items.append(item)
            self._save()
        return item

    def examples_for(self, text: str, *, limit: int = 5) -> tuple[CorrectionExample, ...]:
        words = {part.lower() for part in text.split() if len(part) > 2}
        scored: list[tuple[int, CorrectionExample]] = []
        for item in self._items:
            haystack = f"{item.original} {item.corrected}".lower().split()
            score = sum(1 for word in words if word in haystack)
            if score:
                scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return tuple(item for _, item in scored[:limit])

    def all(self) -> tuple[CorrectionExample, ...]:
        return tuple(self._items)

    def _save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps([item.to_dict() for item in self._items], indent=2, sort_keys=True),
            encoding="utf-8",
        )
