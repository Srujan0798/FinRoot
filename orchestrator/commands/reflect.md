---
name: reflect
description: Retrospective — what worked, what didn't, what to change; capture as an ADR + rule updates.
allowed-tools: Read Write Grep Glob
invocation: both
---

# /reflect

Run after a wave or weekly.

Steps:
1. Read the wave's reports, gotchas, and HALL_OF_SHAME entries.
2. Identify: what sped us up, what slowed us down, recurring failure patterns.
3. Capture durable lessons as: an ADR in `docs/decisions/`, a new rule in `orchestrator/rules/`,
   or a new eval task. Update `orchestrator/memory/MEMORY.md` with the one-line lessons.
4. Promote any capability eval at pass@5 ≥ 50% into the regression suite (§5.5).
5. Emit `reflect.complete`.

Reflection produces artifacts (ADR/rule/eval), not just commentary.
