from ix_gabriella_brain.belief import BeliefGraph
from ix_gabriella_brain.hashing import stable_hash
from ix_gabriella_brain.memory import MemoryQuarantine
from ix_gabriella_brain.models import BeliefStatus, MemoryState
from ix_gabriella_brain.receipts import ReceiptLedger


def test_memory_quarantine_approve() -> None:
    quarantine = MemoryQuarantine()
    candidate = quarantine.propose("User prefers concise replies", source_request_hash="abc")
    approved = quarantine.approve(candidate.memory_id)
    assert approved.state == MemoryState.APPROVED
    assert quarantine.search("concise")


def test_memory_quarantine_reject() -> None:
    quarantine = MemoryQuarantine()
    candidate = quarantine.propose("User likes blue", source_request_hash="abc")
    rejected = quarantine.reject(candidate.memory_id)
    assert rejected.state == MemoryState.REJECTED
    assert not quarantine.search("blue")


def test_sensitive_memory_reason_is_stronger() -> None:
    quarantine = MemoryQuarantine()
    candidate = quarantine.propose("My password is abc", source_request_hash="abc")
    assert "sensitive" in candidate.reason


def test_belief_graph_records_belief() -> None:
    graph = BeliefGraph()
    record = graph.add("goal", "is", "build brain", confidence=0.8, evidence=("user",))
    assert record.status == BeliefStatus.INFERRED
    assert graph.query_subject("goal")


def test_belief_graph_contradicts_opposite_relation() -> None:
    graph = BeliefGraph()
    first = graph.add("feature", "enabled", "yes", confidence=0.7, evidence=("a",))
    graph.add("feature", "enabled", "not yes", confidence=0.9, evidence=("b",))
    assert graph.beliefs[first.belief_id].status == BeliefStatus.CONTRADICTED


def test_receipt_ledger_hash_chain_verifies() -> None:
    ledger = ReceiptLedger()
    ledger.append("one", {"a": 1})
    ledger.append("two", {"b": 2})
    assert ledger.verify()


def test_receipt_ledger_detects_tampering() -> None:
    ledger = ReceiptLedger()
    ledger.append("one", {"a": 1})
    ledger.entries[0]["payload"]["a"] = 99
    assert not ledger.verify()


def test_stable_hash_is_deterministic() -> None:
    assert stable_hash({"b": 2, "a": 1}) == stable_hash({"a": 1, "b": 2})
