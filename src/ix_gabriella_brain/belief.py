from __future__ import annotations

from dataclasses import dataclass, field

from .hashing import stable_hash
from .models import BeliefRecord, BeliefStatus
from .text import lower_ascii

_NEGATIONS = ("not", "no", "never", "isn't", "can't", "cannot", "won't")


def _belief_id(subject: str, predicate: str, object_value: str) -> str:
    return "belief-" + stable_hash({"s": subject, "p": predicate, "o": object_value})[:16]


@dataclass
class BeliefGraph:
    beliefs: dict[str, BeliefRecord] = field(default_factory=dict)

    def add(self, subject: str, predicate: str, object_value: str, *, confidence: float, evidence: tuple[str, ...], status: BeliefStatus = BeliefStatus.INFERRED) -> BeliefRecord:
        normalized_subject = lower_ascii(subject)
        normalized_predicate = lower_ascii(predicate)
        normalized_object = lower_ascii(object_value)
        incoming_negated = self._is_negated(normalized_object)
        for existing in list(self.beliefs.values()):
            same_relation = existing.subject == normalized_subject and existing.predicate == normalized_predicate
            if same_relation and self._is_negated(existing.object_value) != incoming_negated:
                contradicted = BeliefRecord(
                    belief_id=existing.belief_id,
                    subject=existing.subject,
                    predicate=existing.predicate,
                    object_value=existing.object_value,
                    status=BeliefStatus.CONTRADICTED,
                    confidence=existing.confidence,
                    evidence=existing.evidence + ("contradicted_by_new_belief",),
                )
                self.beliefs[existing.belief_id] = contradicted
        record = BeliefRecord(
            belief_id=_belief_id(normalized_subject, normalized_predicate, normalized_object),
            subject=normalized_subject,
            predicate=normalized_predicate,
            object_value=normalized_object,
            status=status,
            confidence=max(0.0, min(1.0, confidence)),
            evidence=evidence,
        )
        self.beliefs[record.belief_id] = record
        return record

    def query_subject(self, subject: str) -> tuple[BeliefRecord, ...]:
        normalized = lower_ascii(subject)
        return tuple(record for record in self.beliefs.values() if record.subject == normalized)

    def active(self) -> tuple[BeliefRecord, ...]:
        return tuple(record for record in self.beliefs.values() if record.status != BeliefStatus.CONTRADICTED)

    def to_dict(self) -> dict[str, object]:
        return {key: record.to_dict() for key, record in sorted(self.beliefs.items())}

    def _is_negated(self, value: str) -> bool:
        words = value.split()
        return any(word in words for word in _NEGATIONS)
