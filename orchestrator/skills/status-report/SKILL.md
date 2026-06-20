---
name: status-report
description: Use when you need a concise current-state summary (active wave, in-flight, pending reviews, next action).
allowed-tools: Read Grep Glob Bash(bash orchestrator/scripts/replay_session.sh:*)
invocation: both
subagent: false
metadata:
  author: finroot
  version: "1.0.0"
---

# Status Report

When to use: session start, or any "where are we?" moment.

Process:
1. Read `HANDOFF.md` + `EXECUTION.md`.
2. Summarize active wave, task ticks, in-flight tasks, reports awaiting review.
3. Pull the last few session events via replay.
4. Output ≤5 lines + the single recommended next action. Read-only.
