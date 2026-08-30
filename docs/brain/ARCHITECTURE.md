# Architecture

IX-Gabriella-Brain is built as a cognitive layer, not as a replacement for the IX-Gabriella app shell.

## Control rule

```text
Brain proposes
Policy decides
User approves
Tools execute
Receipts prove
```

## Lanes

### Fast lane

The fast lane handles recognizable, low-risk assistant requests without invoking heavy planning:

- timers
- reminders
- notes
- list items
- approval or rejection of pending action
- corrections

Fast lane exists because an assistant should not overthink a simple recognizable task.

### Clarification lane

The clarification lane is used when the request shape is recognizable but required details are missing. Example: a timer without duration or a reminder without a time hint.

### Approval lane

The approval lane stages anything consequential, private, external, or persistent. Examples include memory, email, calendar, search, and smart-home staging.

### Brain lane

The brain lane handles open-ended work: planning, comparing, researching, preparing, building, deciding, and multi-step goals.

## Cognitive components

```text
FastIntentRegistry
DownshiftRouter
UncertaintyEngine
MissionEnvelopeBuilder
GoalPlanner
BeliefGraph
MemoryQuarantine
BrainPolicy
WorldTwinLite
AssuranceCase
ReceiptLedger
GabriellaBrainAdapter
```

## Safety boundary

The brain layer does not silently authorize itself. It creates cognitive packets, plans, staged actions, memory proposals, and receipts. Consequential execution remains outside the brain and must pass user approval plus downstream policy.
