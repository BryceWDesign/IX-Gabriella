# IX-Gabriella Product Thesis

IX-Gabriella is a governed virtual assistant project. The product promise is
simple: Gabriella asks before she acts.

The project does not copy Alexa, Google Assistant, Siri, Gemini, or any other
assistant. It studies public user frustrations with voice assistants and turns
those pain points into original product requirements.

## Positioning

IX-Gabriella should compete on trust before ecosystem size.

- Show what was heard.
- Show what the assistant thinks the user meant.
- Show what action is about to happen.
- Require approval before sensitive or uncertain actions.
- Keep tamper-evident receipts for important assistant actions.
- Make memory opt-in, visible, editable, and deletable.
- Keep ads away from private voice content.

## Minimum useful assistant loop

```text
voice or text input
-> transcript
-> decoded intent
-> confidence and uncertainty
-> action preview
-> policy gate
-> confirmation if required
-> safe execution or refusal
-> receipt
-> correction path
```

## What v0.1 proves

This repository proves a functional governed assistant core. It does not claim:

- App Store approval
- always-on iOS wake-word support
- Alexa parity
- Google Assistant parity
- certified smart-home control
- production privacy compliance
- production speech recognition
- production LLM inference

Those are later integration layers.
