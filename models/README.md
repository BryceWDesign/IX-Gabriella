# IX-Gabriella model artifacts

The main IX-Gabriella repository contains the model control layer, prompt contracts, tool schemas, provider adapters, and evaluation fixtures.

Large model weights should not be committed directly to this repo. Use an external model artifact location or a separate model repository, then point IX-Gabriella at that model through environment variables or a local runtime path.

Recommended environment variables:

```text
IX_GABRIELLA_LLM_MODE=local_gabriella | openai_compatible | disabled
IX_GABRIELLA_LLM_ENDPOINT=https://example.invalid/v1/chat/completions
IX_GABRIELLA_LLM_MODEL=your-model-name
IX_GABRIELLA_LLM_API_KEY=not-stored-in-repo
```

The default no-key mode is `local_gabriella`, a deterministic governed language layer. It is not a trained 8/10 model by itself. It preserves the assistant architecture and lets the repo run green without secrets or heavy binary weights.
