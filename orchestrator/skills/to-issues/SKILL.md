---
name: to-issues
description: Use when breaking a wave plan into trackable issues/task files with clear acceptance and ownership.
allowed-tools: Read Write Grep Glob
invocation: claude
subagent: false
metadata:
  author: finroot
  version: "1.0.0"
---

# To Issues

When to use: converting `.specify/specs/wave-N/plan.md` into discrete, trackable units.

Process:
1. One issue per task; title = `wave-N/0X <slug>`.
2. Each carries: acceptance commands, `writes` set, dependencies, scoring relevance.
3. Mirror them as `work/wave-N/0X-*.md` task files (the dispatch artifacts).
4. Keep status in `EXECUTION.md` (one row per wave) — issues are the per-task detail beneath it.
