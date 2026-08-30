from __future__ import annotations

from dataclasses import dataclass, field

from .hashing import stable_hash
from .models import MemoryCandidate, MemoryState
from .text import lower_ascii

_SENSITIVE_MARKERS = {
    "medical", "diagnosis", "religion", "political", "password", "ssn", "social security",
    "credit card", "bank", "address", "sex", "mental health", "criminal",
}


@dataclass
class MemoryQuarantine:
    candidates: dict[str, MemoryCandidate] = field(default_factory=dict)
    approved: dict[str, MemoryCandidate] = field(default_factory=dict)
    rejected: dict[str, MemoryCandidate] = field(default_factory=dict)

    def propose(self, text: str, *, source_request_hash: str) -> MemoryCandidate:
        cleaned = text.strip()
        reason = "requires explicit user approval before long-term memory"
        if any(marker in lower_ascii(cleaned) for marker in _SENSITIVE_MARKERS):
            reason = "sensitive memory requires stronger approval and may be better left unstored"
        memory_id = "mem-" + stable_hash({"text": cleaned, "source": source_request_hash})[:16]
        candidate = MemoryCandidate(memory_id=memory_id, text=cleaned, reason=reason, source_request_hash=source_request_hash)
        self.candidates[memory_id] = candidate
        return candidate

    def approve(self, memory_id: str) -> MemoryCandidate:
        candidate = self.candidates.get(memory_id)
        if candidate is None:
            raise KeyError(f"unknown memory candidate: {memory_id}")
        approved = MemoryCandidate(
            memory_id=candidate.memory_id,
            text=candidate.text,
            reason=candidate.reason,
            state=MemoryState.APPROVED,
            source_request_hash=candidate.source_request_hash,
        )
        self.approved[memory_id] = approved
        self.candidates.pop(memory_id, None)
        return approved

    def reject(self, memory_id: str) -> MemoryCandidate:
        candidate = self.candidates.get(memory_id)
        if candidate is None:
            raise KeyError(f"unknown memory candidate: {memory_id}")
        rejected = MemoryCandidate(
            memory_id=candidate.memory_id,
            text=candidate.text,
            reason=candidate.reason,
            state=MemoryState.REJECTED,
            source_request_hash=candidate.source_request_hash,
        )
        self.rejected[memory_id] = rejected
        self.candidates.pop(memory_id, None)
        return rejected

    def search(self, query: str) -> tuple[MemoryCandidate, ...]:
        needle = lower_ascii(query)
        return tuple(memory for memory in self.approved.values() if needle in lower_ascii(memory.text))

    def to_dict(self) -> dict[str, object]:
        return {
            "quarantined": {key: value.to_dict() for key, value in sorted(self.candidates.items())},
            "approved": {key: value.to_dict() for key, value in sorted(self.approved.items())},
            "rejected": {key: value.to_dict() for key, value in sorted(self.rejected.items())},
        }
