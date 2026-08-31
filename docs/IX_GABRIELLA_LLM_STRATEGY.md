# IX-Gabriella-LLM Strategy

IX-Gabriella-LLM is the dedicated language layer for IX-Gabriella. It is not allowed to directly execute external actions. It proposes user-facing language, plan summaries, clarifying questions, and review packets. The main IX-Gabriella core remains responsible for policy, approval, memory writes, staged actions, and receipts.

## Capability target

The near-term target is not a from-scratch base model. The practical target is an IX-Gabriella-specific model stack:

```text
IX-Gabriella-Brain
+ IX-Gabriella-LLM structured language layer
+ local deterministic fallback
+ hosted OpenAI-compatible provider support
+ Ollama local model support
+ structured response validation
+ correction learning
+ approved-memory retrieval
+ LLM behavior evals
+ receipts and policy gates
```

This is the honest path toward 8/10-class behavior. The repo is not 8/10 by itself without a capable external model. The repo is structured so a strong model can be connected, constrained, evaluated, and safely used.

## Why model weights are not committed

Large model weights should not be committed to the main repository. IX-Gabriella keeps model adapters, contracts, prompts, evals, and configuration in Git. Real model weights should live in an external model registry, release asset, Git LFS location, or local runtime.

## Provider modes

```text
local_gabriella      deterministic fallback, no key required
openai_compatible   hosted or local /v1/chat/completions endpoint
ollama              local Ollama /api/chat endpoint
fallback_openai     OpenAI-compatible primary with deterministic fallback
fallback_ollama     Ollama primary with deterministic fallback
disabled            no language layer
```

## Environment examples

OpenAI-compatible endpoint:

```powershell
$env:IX_GABRIELLA_LLM_MODE="openai_compatible"
$env:IX_GABRIELLA_LLM_ENDPOINT="http://127.0.0.1:8000/v1/chat/completions"
$env:IX_GABRIELLA_LLM_MODEL="your-model-name"
$env:IX_GABRIELLA_LLM_API_KEY="your-key-if-required"
```

Ollama local endpoint:

```powershell
$env:IX_GABRIELLA_LLM_MODE="ollama"
$env:IX_GABRIELLA_OLLAMA_ENDPOINT="http://127.0.0.1:11434/api/chat"
$env:IX_GABRIELLA_OLLAMA_MODEL="your-local-model"
```

Fallback local model:

```powershell
$env:IX_GABRIELLA_LLM_MODE="fallback_ollama"
$env:IX_GABRIELLA_OLLAMA_MODEL="your-local-model"
```

## Required model behavior

The model must return structured JSON with:

```json
{
  "assistant_response": "short user-facing answer",
  "confidence": 0.82,
  "risk": "medium",
  "requested_tool": "propose_plan",
  "requires_user_approval": true,
  "memory_write_requested": false
}
```

Invalid or nonconforming output is repaired or rejected. Unsafe direct tool names are blocked. Memory writes remain quarantined until the core system receives user approval.

## Upgrade ceiling

```text
Standalone repo with deterministic provider: about 6/10 practical language intelligence
Connected to a strong hosted or local model: about 8/10 to 8.3/10 potential
Connected to a tuned model plus real tools, mobile shell, accounts, search, and correction data: 8.5/10 plus potential
True 10/10: not honest to claim from this repo alone
```
