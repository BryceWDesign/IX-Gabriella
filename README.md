# IX-Gabriella

**IX-Gabriella** is a governed, brain-integrated, intelligence-stack virtual assistant foundation by **Bryce Lovell**.

This repository is prepared as the first GitHub-ready public build. It combines the local IX-Gabriella voice/chat GUI, the dedicated **IX-Gabriella-Brain** cognitive layer, and a policy-bound **IX-Gabriella-LLM** stack built specifically for this assistant, including an embedded trained micro language-model artifact.

Gabriella's product promise is simple:

> **The assistant that asks before it acts.**

## What this repo is

IX-Gabriella is a local, source-available assistant foundation that can run in a browser GUI, accept typed chat, accept browser microphone dictation when supported, speak replies through browser speech synthesis, route user requests through IX-Gabriella-Brain, consult a governed IX-Gabriella-LLM stack for complex language work, require approval for higher-risk actions, and write tamper-evident receipts.

The current build is not an App Store app yet. It is the local assistant, cognitive core, and LLM-control foundation intended to move toward an App Store virtual assistant.

## Core architecture

```text
voice or typed input
→ transcript normalization
→ IX-Gabriella-Brain cognitive packet
→ fast lane / clarification lane / approval lane / brain planning lane
→ IX-Gabriella LLM layer when useful
→ Gabriella action planner
→ governance policy gate
→ approval or correction when required
→ safe local execution or staged draft
→ tamper-evident receipt
→ browser GUI response and optional speech output
```

The integrated design follows the operating rule:

```text
Brain proposes.
Policy decides.
User approves.
Tools execute.
Receipts prove.
```

## IX-Gabriella-LLM stack

The repository now includes:

- `ix_gabriella_llm` request and response contracts.
- A Gabriella system prompt and output contract.
- Safe tool schemas and blocked-effect rules.
- Embedded IX-Gabriella-LLM-Micro provider with a packaged trained model artifact.
- Deterministic no-key local Gabriella provider retained as a safe fallback.
- OpenAI-compatible provider adapter configured only through environment variables.
- Ollama local provider adapter for `/api/chat`.
- Fallback provider modes that safely degrade to the deterministic local provider.
- Structured JSON output validation and deterministic repair for nonconforming provider output.
- Correction learning store for user corrections.
- Approved-memory retrieval for model context.
- LLM deliberation engine that preserves fast-lane downshift behavior.
- Provider output boundary checks that reject direct side-effect attempts.
- Evaluation fixtures for simple tasks, complex planning, approval, clarification, correction, and memory behavior.
- Model strategy, model cards, scorecard, and external model manifest files.
- Actual embedded model artifact at `src/ix_gabriella_llm/data/ix_gabriella_micro_lm.json`.

The repo now includes a real trained micro language model for Gabriella response selection. It is intentionally small enough to remain GitHub-friendly and local. It is not a frontier-scale large language model. To reach real 8/10-class conversation quality, connect a capable hosted or local model through the provider boundary and validate it against the eval suite.

## What it can do now

- Run a local browser GUI.
- Accept typed messages.
- Accept microphone dictation in browsers that expose Web Speech Recognition, usually Chrome or Edge.
- Speak responses through browser speech synthesis.
- Route simple recognized tasks through a fast downshift lane.
- Keep simple fast-lane tasks out of the LLM path.
- Route missing-detail tasks to clarification instead of guessing.
- Route complex requests to IX-Gabriella-Brain for reviewable planning.
- Consult the LLM layer for complex, clarifying, and approval-sensitive language work.
- Stage or complete low-risk local actions such as timers, notes, reminders, and list items.
- Require confirmation for memory, drafts, calendar staging, smart-home staging, and higher-risk actions.
- Store approved memory only after explicit user approval.
- Generate tamper-evident receipt chains, including brain and LLM deliberation records.
- Export receipt JSON.
- Run a brain CLI and a main assistant CLI.
- Run an LLM behavior eval script.
- Run the IX-Gabriella-LLM CLI directly.
- Run a quality gate with tests, compile checks, manifest generation, and forbidden-marker scans.

## What it cannot honestly claim yet

- It is not a demonstrated AGI.
- It is not an Alexa, Google Assistant, Gemini, or Siri clone.
- It is not App Store approved yet.
- It is not a native iOS app yet.
- It does not include a production ad SDK.
- It is not always listening.
- It does not include an always-on wake-word daemon.
- It does not control real smart-home devices yet.
- It does not send real emails or modify a real calendar.
- It does not include frontier-scale large model weights. It does include the small IX-Gabriella-LLM-Micro artifact.
- It does not include production cloud scaling, production privacy certification, or safety certification.

## Install and run locally

From PowerShell:

```powershell
cd IX-Gabriella
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -e . pytest
pytest
py scripts\run_quality_gate.py
```

Run the local browser GUI:

```powershell
py scripts\run_gui.py
```

Then open:

```text
http://127.0.0.1:8765/
```

Run the main assistant CLI:

```powershell
ix-gabriella "Hey Gabriella, set a timer for 5 minutes"
```

Run the integrated brain CLI directly:

```powershell
ix-gabriella-brain "help me prepare for tomorrow's meeting with a plan" --json
```

Run the IX-Gabriella-LLM CLI using the default embedded micro model:

```powershell
ix-gabriella-llm "help me prepare for tomorrow's meeting" --json
```

Run LLM behavior evals:

```powershell
py scripts\run_llm_evals.py
```


## Embedded IX-Gabriella-LLM-Micro provider

By default, Gabriella now uses the packaged embedded micro model when the language layer is consulted:

```powershell
$env:IX_GABRIELLA_LLM_MODE="embedded_tiny"
ix-gabriella-llm "help me prepare for tomorrow's meeting" --json
```

You can regenerate the model artifact from the included alignment corpus:

```powershell
py scripts\train_embedded_llm.py
```

The model artifact is real and loaded at runtime, but it is small. It improves standalone behavior and proves the model boundary works without external services. It does not replace a capable hosted or local model for 8/10-class open-ended intelligence.

## Optional OpenAI-compatible LLM provider

By default, Gabriella uses the deterministic local Gabriella language provider. To connect a hosted or local OpenAI-compatible endpoint, set:

```powershell
$env:IX_GABRIELLA_LLM_MODE="openai_compatible"
$env:IX_GABRIELLA_LLM_ENDPOINT="http://127.0.0.1:8000/v1/chat/completions"
$env:IX_GABRIELLA_LLM_MODEL="your-model-name"
$env:IX_GABRIELLA_LLM_API_KEY="your-key-if-required"
```

Secrets are not stored in the repo or browser UI.

## Optional Ollama local provider

To connect a local Ollama model:

```powershell
$env:IX_GABRIELLA_LLM_MODE="ollama"
$env:IX_GABRIELLA_OLLAMA_ENDPOINT="http://127.0.0.1:11434/api/chat"
$env:IX_GABRIELLA_OLLAMA_MODEL="your-local-model"
```

To use provider fallback:

```powershell
$env:IX_GABRIELLA_LLM_MODE="fallback_ollama"
$env:IX_GABRIELLA_OLLAMA_MODEL="your-local-model"
```

## Intelligence score boundary

```text
Current standalone deterministic mode: about 6/10 practical language intelligence.
Current embedded micro-model mode: about 6.4/10 practical language intelligence.
With a strong connected model: 8/10 to 8.3/10 potential.
With a strong connected model plus real tools, mobile shell, accounts, search, calendar/email connectors, and tuned voice UX: 8.5/10 plus potential.
True 10/10 is not claimed.
```

## Public release note

Although earlier internal handoff ZIPs existed during development, this repository is prepared as the **first GitHub-ready public IX-Gabriella build** with brain integration and LLM-control architecture included from the starting point.

## Donor-informed architecture

This repo was built from IX-Gabriella and integrates a dedicated IX-Gabriella-Brain package. The brain and LLM-control design were informed by user-supplied donor repositories and prior IX-Gabriella work, including:

- IX-Gabriella v0.2.0 local voice/chat GUI foundation.
- IX-Gabriella-Brain v0.1.0 cognitive brain layer.
- IX-Sally cognitive/planning donor patterns.
- IX-BlackFox governance, approval, evidence, and receipt patterns.
- SynapDrive-AI fail-closed action gating and confidence patterns.
- IX-Autonomy-Assurance-Case-Runtime assurance-case patterns.
- IX-BlackFox-Cognition belief, planning, and memory-quarantine patterns.
- IX-BlackFox-WorldTwin scenario and reality-delta patterns.
- IX-IntentRealityLoop request, permission, feedback, memory, and evidence-loop patterns.
- IX-HapticSight consent and safe-hold interaction patterns.
- IX-main parser, trace, and safety-contract patterns.

## License

IX-Gabriella is source-available for personal noncommercial evaluation only under the included **Source-Available Noncommercial Evaluation License v1.0**.

Commercial use, production use, hosted use, redistribution, resale, App Store monetized use, incorporation into another product, organization-backed evaluation, or operational deployment requires prior written permission and a separate license from **Bryce Lovell**.
