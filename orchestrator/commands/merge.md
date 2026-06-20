---
name: merge
description: Merge approved work — integrate, run cross-cutting gate, update state.
allowed-tools: Read Write Bash(git:*) Bash(ruff:*) Bash(pytest:*) Bash(python:*)
invocation: both
---

# /merge [task]

Integrate APPROVED work only.

Steps:
1. Confirm the task was APPROVED in the events log.
2. Run the cross-cutting gate: `ruff check src/ && pytest tests/unit -v` (+ smoke for foundation waves).
3. Commit with a conventional message: `feat(wave-N): <task title> (task 0X)`.
4. Update the task's tick in `EXECUTION.md` (e.g., 3/6). Emit `merge.complete` with the commit hash.
5. If a gotcha surfaced, ensure it's in `docs/waves/wave-N-gotchas.md`.

If the gate fails after a merge, revert and send the task back to REVISE — never leave main red.
