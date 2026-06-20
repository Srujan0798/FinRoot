---
name: diagnose
description: Use when a bug, test failure, or unexpected behavior appears — reproduce and root-cause before proposing a fix.
allowed-tools: Read Bash Grep Glob
invocation: both
subagent: true
metadata:
  author: finroot
  version: "1.0.0"
---

# Diagnose

When to use: any failure. Systematic debugging, not guess-and-check.

Process:
1. Reproduce deterministically (Mock mode, seeded RNG). Capture the exact failing command + output.
2. Read the relevant code + the audit trail / events for the failing run.
3. Form ONE hypothesis; write a failing test that encodes it (TDD).
4. Confirm the hypothesis; only then propose the fix (handed to a worker as a task).
5. If it's a recurring class → `HALL_OF_SHAME.md` + a prevention rule + an eval task (§6.7).

Finance-specific: check first for hallucinated/uncited numbers and silent tool fallbacks (FM-11).
