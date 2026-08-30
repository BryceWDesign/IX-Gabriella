# Usage

## CLI

```powershell
ix-gabriella-brain "set a timer for 10 minutes"
ix-gabriella-brain "remember that I prefer short direct answers" --json
ix-gabriella-brain "help me prepare for tomorrow's meeting" --json
```

## Python

```python
from ix_gabriella_brain import GabriellaBrain

brain = GabriellaBrain()
packet = brain.think("add milk to my grocery list")
print(packet.decision.user_message)
print(packet.route.route.value)
print(packet.receipt_hash)
```

## Integration with IX-Gabriella

```python
from ix_gabriella_brain import GabriellaBrain
from ix_gabriella_brain.integrations.gabriella_core import GabriellaBrainAdapter

adapter = GabriellaBrainAdapter(GabriellaBrain())
result = adapter.handle_user_text("help me plan my day")
```

The adapter returns a dict with message, status, route, receipt hash, and the full cognitive packet.
