# Interview Runbook

How the orchestrator asks Srujan for a decision — rarely, and well.

## When to interview
- New feature/capability before `/plan`.
- Genuine ambiguity in a spec before `/dispatch`.
- A 2nd REVISE on the same task (something is unclear).
- A tech choice with multiple valid paths and real trade-offs.

## How
1. Use the `interviewer` sub-agent.
2. Frame as MULTIPLE CHOICE. Max 4 questions.
3. Mark the recommended option + the reason.
4. Record the answer + reasoning as an ADR in `docs/decisions/`.

## Don't ask
- Anything the PRD / ARCHITECTURE / SCOPE_GUARD already answers.
- Open-ended "any thoughts?" or "should we do X?" without alternatives.

## Examples
- Bad: "How should the reasoning trace work?"
- Good: "Reasoning trace in the UI: always-on / expandable-on-demand / off by default?"
- Good: "Wave-1 first dispatch: freeze schema contract then parallelize (recommended), or ship task 02 fully first?"
