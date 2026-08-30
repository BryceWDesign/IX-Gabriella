# IX-Gabriella Brain and LLM Integration

This build wires the IX-Gabriella local assistant shell to the IX-Gabriella-Brain cognitive layer and the policy-bound IX-Gabriella LLM layer.

## Integration contract

The GUI and CLI send user input to `GabriellaAssistant.handle_text()`. The assistant normalizes the transcript, calls `GabriellaBrain.think()`, sends the resulting brain packet to the LLM deliberation layer when useful, converts the resulting `CognitivePacket` into the main assistant's intent and policy model, then either executes a low-risk local action, asks for clarification, asks for approval, or returns a plan-only cognitive response.

## Route behavior

| Brain route | Main assistant behavior | LLM behavior |
| --- | --- | --- |
| `fast_lane` | Execute low-risk local action through Gabriella core. | Skipped to preserve fast downshift. |
| `clarify_lane` | Ask for missing information and do not execute. | May draft clearer clarification language. |
| `approval_lane` | Show action preview and wait for user approval. | May draft approval wording, but cannot authorize action. |
| `brain_lane` | Produce a reviewable cognitive plan with no external execution. | May refine language and plan explanation. |

## Side-effect boundary

In integrated mode, the brain is initialized with `execute_fast_locally=False`. This prevents duplicate side effects. The brain decides and explains. The LLM drafts and critiques. Gabriella core owns local timers, notes, reminders, lists, drafts, memory writes, and receipt chains.

## Receipt behavior

Every handled turn writes a main assistant receipt chain containing:

1. transcript received,
2. brain packet created,
3. LLM deliberation completed or skipped,
4. intent decoded,
5. action planned,
6. policy result,
7. action completion when applicable.

The brain also maintains its own packet receipt hash for cognitive traceability.

## Claim boundary

IX-Gabriella-Brain is an AGI-candidate cognitive architecture component. The LLM layer is an LLM-ready control layer. Together they are not a demonstrated AGI. Their present role is assistant cognition: downshifting simple tasks, detecting uncertainty, creating plans, preserving memory boundaries, consulting language models safely, and keeping user approval in control.
