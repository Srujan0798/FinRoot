---
name: plan
description: Plan a wave — generate/refresh .specify/specs/wave-N/{spec,plan,tasks,contracts} from the PRD.
allowed-tools: Read Write Glob Grep
invocation: both
---

# /plan wave-N

Turn the PRD + ARCHITECTURE into an executable wave spec.

Steps:
1. Read `plan/PRD.md`, `plan/ARCHITECTURE.md`, `plan/EXECUTION.md`, and `docs/waves/wave-N-brief.md`.
2. Write `.specify/specs/wave-N/spec.md` (goal, in/out scope, acceptance commands, success signals).
3. Write `plan.md` (task breakdown with disjoint `writes` sets + dependency order).
4. Write `tasks.md` (index + per-task acceptance map).
5. Write `contracts/*.md` for any shared interface two tasks would otherwise both define.
6. Update `EXECUTION.md` status to "READY TO DISPATCH". Emit event.

Do NOT write task files here — that's `/dispatch`. Do NOT implement anything.
