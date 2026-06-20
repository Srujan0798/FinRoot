# Session Index

Maps each durable session event log to its wave/task. Append a row when a task is first dispatched.

| Session file | Wave | Task | Started | Status |
|---|---|---|---|---|
| _(created on first /dispatch)_ | wave-1 | 0X | — | — |

## Format
`orchestrator/memory/session/<wave>-<task>.events.jsonl` — append-only, one JSON event per line.
Event types: task.dispatched · worker.started · report.received · acceptance.run ·
review.decision · merge.complete · wave.shipped · handoff.written · audit.complete.

Reconstruct context with: `bash orchestrator/scripts/replay_session.sh <wave> <task>`.
