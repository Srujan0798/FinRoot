---
name: handoff
description: Rewrite HANDOFF.md to current truth before ending a session or switching orchestrators.
allowed-tools: Read Write Grep Glob
invocation: both
---

# /handoff

Steps:
1. Read `EXECUTION.md` + recent events.
2. Rewrite `HANDOFF.md` (do NOT append — replace to current truth, FM-01/14): snapshot, active
   wave, what exists, what's not done, immediate next action, open decisions, last-session note.
3. Confirm active wave matches `EXECUTION.md` (validate_execution.sh).
4. Emit `handoff.written`.

A cold session must be able to resume correctly from HANDOFF.md alone.
