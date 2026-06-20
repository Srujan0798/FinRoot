---
name: status
description: Report where we are — active wave, in-flight tasks, pending reviews, next action.
allowed-tools: Read Grep Glob Bash(bash orchestrator/scripts/replay_session.sh:*)
invocation: both
---

# /status

The first move of every session.

Steps:
1. Read `HANDOFF.md` and `plan/EXECUTION.md`.
2. List: active wave, task ticks (e.g., 2/6), tasks in flight, reports awaiting review.
3. Scan recent `orchestrator/memory/session/*.events.jsonl` for the last few events.
4. Print a 5-line summary + the single recommended next action.

No writes. Read-only (r0).
