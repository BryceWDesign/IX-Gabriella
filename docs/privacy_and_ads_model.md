# Privacy and Ads Model

IX-Gabriella is intended to support a free tier with bottom-screen ads without
sacrificing user trust.

## Hard rules

- Do not use private voice content for ad targeting.
- Do not retain raw audio by default.
- Do not save memory without explicit user approval.
- Do not execute sensitive actions without confirmation.
- Suppress ads on screens containing sensitive context.

## Current implementation

- `PrivacyControls` rejects voice-content ad targeting.
- `AdPolicy` allows only generic screen-level bottom banner decisions.
- Sensitive terms suppress ads for that interaction.
- `MemoryStore` raises `PermissionError` unless the write is approved.

## App Store readiness

The future iOS app needs, at minimum:

- privacy policy
- account deletion path if accounts exist
- microphone permission copy
- ad disclosure
- data deletion and memory controls
- clear explanation of local versus remote processing
