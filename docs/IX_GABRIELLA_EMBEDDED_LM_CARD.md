# IX-Gabriella-LLM-Micro Model Card

## Identity

```text
Model name: IX-Gabriella-LLM-Micro
Model id: ix-gabriella-llm-micro-v0.1.0
Author/copyright: Bryce Lovell
License: Source-Available Noncommercial Evaluation License v1.0
Packaged artifact: src/ix_gabriella_llm/data/ix_gabriella_micro_lm.json
```

## What it is

IX-Gabriella-LLM-Micro is an embedded trained language-model artifact for IX-Gabriella. It uses an interpolated trigram response-selection architecture trained from Gabriella alignment examples. The model scores candidate assistant responses against route, status, missing-slot, and user-text context, then returns a structured language packet through the same safety boundary used by hosted and local provider adapters.

## What it is not

It is not a frontier-scale large language model. It is not a demonstrated AGI. It is not a substitute for a strong hosted or local model when open-ended reasoning, broad factual knowledge, long-form writing, or complex conversation quality are required.

## Why it exists

The previous repo contained adapters and deterministic provider logic but no model weights. This embedded model gives IX-Gabriella a real packaged model artifact that can run without external services while preserving the higher-capability hosted/local provider path.

## Safety boundary

The embedded model can propose user-facing language and safe tool names only. It cannot send email, modify calendars, control smart-home devices, write long-term memory, spend money, delete data, or perform external actions. IX-Gabriella core policy, approval gates, and receipts remain authoritative.

## Expected score

```text
Standalone deterministic provider only: about 6 / 10 practical assistant language layer
Standalone embedded micro model: about 6.4 / 10 practical assistant language layer
Strong hosted or local model connected through the provider boundary: 8 / 10 plus capable
Full assistant with mobile shell, accounts, tools, search, calendar, email, and tuned voice UX: 8.5 / 10 plus potential
```

## Regeneration

```powershell
py scripts\train_embedded_llm.py
```
