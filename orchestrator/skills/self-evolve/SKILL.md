---
name: self-evolve
description: Use before dispatching new tasks and after wave retros — scan failures and fold lessons back into rules, templates, and evals.
allowed-tools: Read Write Grep Glob
invocation: claude
subagent: false
metadata:
  author: finroot
  version: "1.0.0"
---

# Self-Evolve

When to use: before `/dispatch` of a new wave, and during `/reflect`.

Process:
1. Scan `HALL_OF_SHAME.md`, recent gotchas, and REVISE history.
2. For each recurring failure: add/strengthen a rule in `orchestrator/rules/`, tighten
   `work/TASK_TEMPLATE.md`, or add an eval task that would have caught it.
3. Update `orchestrator/memory/MEMORY.md` with the one-line lesson.
4. Promote capability evals at pass@5 ≥ 50% to the regression suite.

The guardrail library only grows. Every scar becomes a rule + a test.
