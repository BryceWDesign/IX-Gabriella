# Provider Boundaries

IX-Gabriella separates assistant governance from optional model, voice, ad, or device providers.

## Default mode

Default operation is local and deterministic. It requires no cloud key. This lets the core policy, approval, memory, receipt behavior, brain routing, and LLM boundary run consistently during development and testing.

## LLM provider

`ix_gabriella_llm` supports a default deterministic local Gabriella provider and an OpenAI-compatible chat-completions endpoint. Configure the optional endpoint only through environment variables:

```text
IX_GABRIELLA_LLM_MODE
IX_GABRIELLA_LLM_ENDPOINT
IX_GABRIELLA_LLM_MODEL
IX_GABRIELLA_LLM_API_KEY
```

The repository does not store secrets. Provider output is treated as a proposal. It cannot directly send messages, change calendars, control smart-home devices, write long-term memory, make purchases, transfer money, or execute account changes. If a provider proposes a blocked tool or effect, the result is rejected and the deterministic core response remains in control.

## Legacy chat provider

`OpenAICompatibleChatProvider` remains available for simple chat-completions experiments through:

```text
IX_GABRIELLA_CHAT_ENDPOINT
IX_GABRIELLA_CHAT_MODEL
IX_GABRIELLA_CHAT_API_KEY
```

The LLM layer is the preferred route for production-facing model work because it carries the brain packet, allowed tools, blocked effects, and safety contract.

## Voice provider

The GUI uses browser speech recognition for dictation and browser speech synthesis for spoken replies. Mobile-native builds should replace that surface with a platform speech interface while preserving the same transcript contract.

## Smart-home provider

Smart-home commands are staged with device and requested-state metadata. A future device connector must verify device identity, requested state, and user approval before real-world execution.

## Ads provider

The current repo includes ad policy guardrails, not a bundled ad SDK. Ads must not use private voice transcripts or approved memory as creepy targeting fuel.
