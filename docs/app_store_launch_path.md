# App Store Launch Path

IX-Gabriella v0.1 is the governed assistant core. A public App Store release
needs an iOS shell and platform-specific compliance work.

## Practical v1 shape

- User opens the app.
- User taps or holds to speak.
- Speech-to-text produces transcript plus confidence.
- Core shows what Gabriella heard.
- Core previews the interpreted action.
- Core asks before sensitive or uncertain actions.
- Core writes a receipt for the turn.
- User can correct, approve, reject, or delete memory.

## iOS limitations to respect

Do not assume a third-party app can behave like a smart speaker with unlimited
always-on wake-word access. The first App Store version should be designed
around explicit app opening, tap-to-talk, widgets, Shortcuts, and App Intents
where available.

## Build milestones

1. Core Python package, complete in this repo.
2. Local CLI and test harness, complete in this repo.
3. API wrapper or Swift port.
4. iOS app shell.
5. Speech-to-text provider selection.
6. Text-to-speech provider selection.
7. Account, privacy, and memory settings.
8. Ad integration with sensitive-screen suppression.
9. App Store review materials.
10. Public beta.
