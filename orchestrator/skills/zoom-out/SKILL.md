---
name: zoom-out
description: Use when lost in detail or after several tasks — step back to the wave goal, scoring weights, and the critical path.
allowed-tools: Read Grep Glob
invocation: both
subagent: false
metadata:
  author: finroot
  version: "1.0.0"
---

# Zoom Out

When to use: context feels noisy; decisions feel local; risk of optimizing the wrong thing.

Process:
1. Re-read the PRD one-liner + the scoring weights (Reasoning 35% first).
2. Ask: does the current work move a heavy-weighted axis? If not, why are we doing it?
3. Re-check the critical path in `EXECUTION.md`. Is the active wave the right one?
4. Re-affirm scope (SCOPE_GUARD). Park anything that drifted into BACKLOG.
5. Output: the one thing that most increases the chance of winning, and do that next.
