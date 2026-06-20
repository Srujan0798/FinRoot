---
name: merge-work
description: Use when integrating approved worker output — run the cross-cutting gate, commit, update state.
allowed-tools: Read Write Bash(git:*) Bash(ruff:*) Bash(pytest:*) Bash(python:*)
invocation: claude
subagent: false
metadata:
  author: finroot
  version: "1.0.0"
---

# Merge Work

When to use: a task is APPROVED.

Process:
1. Confirm APPROVE in the events log.
2. Run `ruff check src/ && pytest tests/unit -v` (+ smoke for foundation waves). Must be green.
3. Commit (conventional): `feat(wave-N): <title> (task 0X)`.
4. Update the task tick in `EXECUTION.md`; emit `merge.complete` with the hash.
5. Ensure any gotcha is captured in `docs/waves/wave-N-gotchas.md`.

Never leave main red — a failing post-merge gate means revert + REVISE.
