# Donor Integration Map

This repo uses the provided donor repositories as technical design input. The result is a new IX-Gabriella-Brain package shaped for virtual-assistant behavior.

| Donor | Mechanism extracted | Implemented in IX-Gabriella-Brain |
|---|---|---|
| IX-Gabriella v0.2.0 | Local assistant shell, approval pattern, receipts, voice GUI direction | `integrations/gabriella_core.py`, packet format, user-facing decision fields |
| IX-Sally | Goal graph, deterministic planning, uncertainty, world facts, cognitive snapshots, review bridge | `planner.py`, `uncertainty.py`, `belief.py`, `brain.py` |
| IX-BlackFox-Cognition | Mission envelope, belief graph, memory quarantine, authority boundaries, routing | `mission.py`, `belief.py`, `memory.py`, `routing.py` |
| IX-IntentRealityLoop | Intent → permission → action → feedback → memory → evidence loop | `fast_intents.py`, `policy.py`, `storage.py`, `receipts.py` |
| IX-BlackFox | Evidence-first governance, hash receipts, human approval discipline | `receipts.py`, `assurance.py`, packet payloads |
| SynapDrive-AI | Fail-closed posture, confidence gates, action admission | `routing.py`, `uncertainty.py`, `policy.py` |
| IX-Autonomy-Assurance-Case-Runtime | Assurance-case traceability and claim guardrails | `assurance.py`, `quality.py` |
| IX-BlackFox-WorldTwin | Scenario consequence checking and prediction accountability | `worldtwin.py` |
| IX-HapticSight | Consent state, safe hold, bounded interaction patterns | approval and memory quarantine behavior |
| IX-main | Readable behavior contracts and claim-boundary discipline | `README.md`, `NOTICE.md`, `docs/CLAIM_BOUNDARIES.md` |

## Integration choice

The donors were not dumped into the repo as a mass copy. The brain layer is purpose-built around assistant cognition, with donor concepts implemented as a smaller, testable, composable runtime.
