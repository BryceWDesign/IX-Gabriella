from ix_assistant_core.receipts import ReceiptEventType, ReceiptLedger


def test_receipt_chain_verifies_for_one_intent() -> None:
    ledger = ReceiptLedger()
    ledger.append(intent_id="intent-1", event_type=ReceiptEventType.TRANSCRIPT_RECEIVED, summary="heard")
    ledger.append(intent_id="intent-1", event_type=ReceiptEventType.INTENT_DECODED, summary="decoded")
    assert ledger.verify_intent_chain("intent-1") is True
    records = ledger.filter_by_intent("intent-1")
    assert records[1].previous_receipt_id == records[0].receipt_id
    assert records[1].previous_chain_digest == records[0].chain_digest


def test_ledger_export_contains_event_type() -> None:
    ledger = ReceiptLedger()
    ledger.append(intent_id="intent-2", event_type=ReceiptEventType.POLICY_ALLOWED, summary="allowed")
    assert "policy_allowed" in ledger.export_json()
