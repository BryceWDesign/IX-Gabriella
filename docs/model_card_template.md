# Model card template: IX-Gabriella-LLM

**Owner:** Bryce Lovell  
**Project:** IX-Gabriella  
**Role:** language and planning support layer for a governed virtual assistant  
**Direct-action authority:** none  

## Intended use

IX-Gabriella-LLM is intended to help Gabriella understand natural language, draft responses, critique plans, recover from corrections, and ask clarifying questions.

## Not intended for

- Autonomous external actions.
- Financial, medical, legal, or safety-critical decision-making without human review.
- Writing long-term memory without explicit user approval.
- Claims of demonstrated AGI unless independently proven by rigorous evaluation.

## Required gates

- Brain route check.
- Policy gate.
- Approval gate for consequential actions.
- Receipt generation.
- Memory quarantine.
- Provider output boundary check.

## Evaluation categories

- Simple-task downshift.
- Voice mishearing repair.
- Clarification behavior.
- Complex planning.
- Tool-use boundary.
- Privacy and memory approval.
- Refusal and safe alternative behavior.
