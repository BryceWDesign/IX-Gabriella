# IX-Gabriella LLM strategy

IX-Gabriella now includes a policy-bound LLM layer inside the main repo. The layer is built to improve natural conversation, complex planning language, correction recovery, and answer drafting while preserving the core rule:

```text
Brain proposes. Policy decides. User approves. Tools execute. Receipts prove.
```

## What lives inside this repo

- LLM request and response contracts.
- Gabriella system prompt and output contract.
- Safe tool schema registry.
- Blocked-effect list.
- OpenAI-compatible provider adapter.
- Deterministic local Gabriella provider for no-key operation.
- Deliberation engine that skips simple fast-lane tasks.
- Evaluation fixtures for fast-lane, brain-lane, approval, clarification, and memory behavior.

## What does not live inside this repo

- Large model weights.
- API keys.
- Hosted model credentials.
- App Store credentials.
- Claims that IX-Gabriella is a demonstrated AGI.

## Intelligence target

The repo now has the architecture needed to attach an 8/10-class language model safely. The included default local provider is deterministic and useful for offline operation, but it is not a trained large language model. Actual 8/10 conversational performance requires a strong hosted or local model connected through the provider boundary and tested against the evaluation set.

## Safety boundary

The LLM may draft text, propose plans, ask clarifying questions, and critique the brain packet. It cannot directly execute external side effects. If a provider proposes a blocked tool or effect, IX-Gabriella rejects that language result and falls back to the core deterministic response.
