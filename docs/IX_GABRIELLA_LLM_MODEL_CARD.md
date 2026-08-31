# IX-Gabriella-LLM Model Card

## Name

IX-Gabriella-LLM

## Owner

Bryce Lovell

## Role

Dedicated language layer for IX-Gabriella.

## Intended use

IX-Gabriella-LLM supports conversational response drafting, user-intent clarification, plan explanation, correction recovery, and safe plan summarization. It does not execute actions directly.

## Out-of-scope use

```text
autonomous external action
hidden memory writes
financial execution
medical, legal, or safety-critical decision authority
unapproved messaging or email sending
unapproved smart-home control
claiming demonstrated AGI
```

## Required controller

IX-Gabriella-LLM must be used behind the IX-Gabriella controller stack:

```text
IX-Gabriella-Brain
→ IX-Gabriella-LLM
→ policy gate
→ approval gate
→ tool/action layer
→ receipt ledger
```

## Safety boundary

The model may propose only allowed tool names. It may not trigger external side effects. The core assistant must validate structured output and reject unsafe tool attempts.

## Data boundary

Approved memory may be retrieved into context. Unapproved private conversation text must not be silently promoted to long-term memory.

## Current artifact status

This repo includes contracts, adapters, evals, correction learning, memory retrieval, structured validation, and deterministic fallback. It does not include trained large model weights.
