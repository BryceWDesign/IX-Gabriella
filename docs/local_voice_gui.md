# IX-Gabriella Local Voice GUI

IX-Gabriella v0.2.0 includes a working local browser interface for typed chat, microphone dictation, spoken replies, confirmation gates, correction flow, and receipt export.

## Run on Windows PowerShell

```powershell
cd IX-Gabriella
py scripts\run_gui.py
```

Or run the helper script:

```powershell
.\scripts\run_voice_gui.ps1
```

The server opens a local browser at:

```text
http://127.0.0.1:8765/
```

## What works now

- Type to Gabriella in the chat UI.
- Click the microphone button and speak when the browser supports speech recognition.
- Hear Gabriella's reply through browser speech synthesis.
- See what Gabriella heard, the decoded intent, confidence, risk, and policy result.
- Approve or reject risky actions.
- Correct a pending action before it is executed or staged.
- Export receipt JSON.
- Save local timers, reminders, notes, list items, email drafts, calendar drafts, and smart-home staged commands.

## Real boundary

This is not an App Store binary yet. It is a local desktop/browser development surface for the assistant core. It does not provide always-on background wake-word detection. Browser microphone dictation depends on browser support and permission. Chrome and Edge are the intended first test browsers.

## Safety behavior

IX-Gabriella treats decoded intent as a proposal, not permission. Email sending, calendar invites, memory writes, and smart-home control are either approval-gated or staged for a verified connector. This is intentional product behavior.
