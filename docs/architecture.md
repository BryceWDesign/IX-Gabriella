# Architecture

IX-Gabriella uses a governed assistant pipeline with brain-first routing and a policy-bound LLM layer.

```text
InputNormalizer
-> IX-Gabriella-Brain
-> fast lane / clarify lane / approval lane / brain lane
-> IX-Gabriella LLM layer when useful
-> BrainBridge
-> ActionPlanner
-> GovernancePolicy
-> ApprovalGate when needed
-> safe local execution, staged draft, or refusal
-> ReceiptLedger
-> MemoryStore only with approval
-> AdPolicy and PrivacyControls
```

## Modules

- `input`: wake phrase stripping and transcript normalization.
- `transcription`: provider-neutral speech-to-text contract.
- `ix_gabriella_brain`: fast intent registry, cognitive routing, planning, uncertainty, memory quarantine, WorldTwin Lite, and assurance readiness.
- `ix_gabriella_llm`: LLM contracts, prompt policy, provider adapters, safe tool schemas, and deliberation boundary.
- `intent`: deterministic fallback intent parser.
- `actions`: action preview and risk assignment.
- `governance`: policy decision and human approval gate.
- `receipts`: tamper-evident event chain, including brain and LLM deliberation events.
- `memory`: opt-in approved memory records.
- `privacy`: default privacy controls.
- `ads`: generic bottom-banner policy with sensitive-context suppression.
- `assistant`: pipeline orchestration.
- `appstore`: static readiness checks for mobile wrapper planning.
- `voice`: wake phrase scoring utility.

## LLM rule

The LLM does not execute actions. It drafts language, critiques plans, asks clarifying questions, and proposes reviewable steps. The main assistant core remains responsible for approval, execution, memory writes, and receipts.
