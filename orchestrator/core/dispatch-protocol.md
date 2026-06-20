# Dispatch Protocol

How the orchestrator turns a planned wave into parallel-safe worker tasks.

## Before writing any task file
1. Read the wave spec (`.specify/specs/wave-N/spec.md`) and plan (`plan.md`).
2. List every file the wave will touch. **Partition them into disjoint `writes` sets** — one set
   per task. No file appears in two sets (FM-13). Shared/foundation files go to ONE early task.
3. Freeze shared contracts (`.specify/specs/wave-N/contracts/`) before dispatch so no two workers
   redefine the same type/interface.
4. Identify dependencies. Independent tasks → parallel. Dependent tasks → sequence or gate.

## Task file requirements (use work/TASK_TEMPLATE.md)
Every task file is **self-contained** — a worker with no other context can execute it. It must have:
- **Objective** (one paragraph) and **why it matters** (link to scoring/PRD).
- **Writes** (exact files this task may create/modify) and **Forbid** (files it must NOT touch).
- **Contract** references (which `contracts/*.md` to honor).
- **Steps** (ordered, concrete).
- **Acceptance** (exact commands + expected output — the worker must paste real output, FM-09).
- **Report path** (`work/reports/wave-N/0X-*.report.md`) and the report template.
- **Domain rules** reminder (numbers cited, fail loud, confidence labels).

## Dispatch
1. Emit `task.dispatched` to the session events log.
2. Hand the task file + `work/WORKER_PROMPT.md` to a worker window.
3. Track which window owns which task in the session INDEX.

## Disjoint-write check (run mentally / via validate.sh before dispatch)
If two pending tasks list the same path under `Writes`, STOP — re-partition or sequence them.
