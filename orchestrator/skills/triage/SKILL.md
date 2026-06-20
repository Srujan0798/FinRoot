---
name: triage
description: Use when new requests, bugs, or ideas arrive and must be routed to a wave, BACKLOG, or HALL_OF_SHAME.
allowed-tools: Read Write Grep Glob
invocation: both
subagent: false
metadata:
  author: finroot
  version: "1.0.0"
---

# Triage

When to use: something new lands (feature idea, bug, scope question).

Process:
1. Classify: in-scope-now / backlog / bug / out-of-scope (check `docs/SCOPE_GUARD.md`).
2. In-scope-now → add a task to the active or next wave (only if it serves the scoring weights).
3. Idea but not now → `BACKLOG.md` (title · why · size · earliest wave).
4. Bug → `/diagnose`; if a recurring pattern, also `HALL_OF_SHAME.md`.
5. Out-of-scope → record the decision and decline; do not silently build (FM-08).

Bias toward NOT expanding scope. Protect the deadline.
