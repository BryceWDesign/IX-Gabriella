# IX-Gabriella-LLM-Micro

This directory documents the embedded model artifact packaged with IX-Gabriella.

The artifact is intentionally small enough to keep the first GitHub-ready repo cloneable. It is a trained statistical language model for Gabriella response selection, not a frontier-scale neural model. It gives the repo a real local model artifact while the larger hosted or local model path remains available through the existing provider adapters.

The packaged artifact lives at:

```text
src/ix_gabriella_llm/data/ix_gabriella_micro_lm.json
```

Regenerate it with:

```powershell
py scripts\train_embedded_llm.py
```
