# IX-Gabriella Release Audit

Build: v0.1.0-embedded-model
Public posture: first GitHub-ready public repo starting point
Author/copyright: Bryce Lovell
License: Source-Available Noncommercial Evaluation License v1.0

## Validation

```text
98 tests passed
LLM behavior evals passed
Python compile check passed
Quality gate passed
Forbidden marker scan clean
Authorship scan clean
Release manifest generated
```

## Intelligence boundary

This build includes IX-Gabriella-Brain, the IX-Gabriella-LLM control stack, and an actual packaged IX-Gabriella-LLM-Micro model artifact. It is not a demonstrated AGI and does not include frontier-scale large model weights. It is designed to improve standalone behavior while still requiring a capable hosted or local model for 8/10-class open-ended assistant intelligence.

## Added in this build

```text
Embedded IX-Gabriella-LLM-Micro model artifact
Embedded model runtime provider
Embedded model regeneration script
Embedded model tests
Ollama provider adapter
OpenAI-compatible provider adapter
Fallback provider modes
Structured JSON validation
Deterministic repair for nonconforming provider output
Approved-memory retrieval
Correction learning store
IX-Gabriella-LLM CLI
Expanded LLM behavior evals
Model strategy and model card docs
External model manifest example
```
