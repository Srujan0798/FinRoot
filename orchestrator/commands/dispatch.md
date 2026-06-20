---
name: dispatch
description: Dispatch a planned wave — write self-contained, disjoint-write task files into work/wave-N/.
allowed-tools: Read Write Glob Grep Bash(bash orchestrator/scripts/validate.sh:*)
invocation: both
---

# /dispatch wave-N

Produce ready-to-paste worker task files. Follow `core/dispatch-protocol.md`.

Steps:
1. Read `.specify/specs/wave-N/{spec,plan,tasks}.md` and the contracts.
2. For each task, write `work/wave-N/0X-<slug>.md` from `work/TASK_TEMPLATE.md` with:
   Objective · Why · Writes · Forbid · Contracts · Steps · Acceptance(cmd+expected) · Report path.
3. **Verify disjoint write-sets** across all tasks (run `validate.sh` / mental check). If any two
   share a path, re-partition or sequence — do not dispatch (FM-13).
4. Emit `task.dispatched` per task to `orchestrator/memory/session/wave-N-0X.events.jsonl`.
5. Print the list of files to paste into worker windows + the `WORKER_PROMPT.md` preamble.

Output ends with: "Open N worker windows and paste work/wave-N/0X-*.md."
