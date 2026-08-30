# Donor Integration Notes

IX-Gabriella v0.1 was built after inspecting two donor repositories supplied for
this project.

## IX-BlackFox lineage

Used architectural patterns:

- Policy gates before action.
- Approval as a first-class decision.
- Tamper-evident chained receipts.
- Evidence and replay mindset.
- Human decision boundaries.

Implemented IX-Gabriella modules:

- `ix_assistant_core.governance.policy`
- `ix_assistant_core.governance.approval`
- `ix_assistant_core.receipts.ledger`
- `ix_assistant_core.appstore.readiness`

## SynapDrive-AI lineage

Used architectural patterns:

- Fail-closed pre-action runtime.
- Confidence and uncertainty checks.
- Safe fallback action when confidence is low.
- Decoded intent is not permission.
- Runtime contracts that make actions testable.

Implemented IX-Gabriella modules:

- `ix_assistant_core.intent.parser`
- `ix_assistant_core.actions.planner`
- `ix_assistant_core.assistant.engine`
- `ix_assistant_core.privacy.controls`

## Boundary

The current repository is not a direct mobile app. It is the governed assistant
core intended to be wrapped by a future iOS client. The iOS client should call
this core or a port of this core for intent preview, policy decisions, receipts,
and privacy behavior.
