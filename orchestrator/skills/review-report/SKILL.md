---
name: review-report
description: Use when a worker report arrives and you must verify it by re-running acceptance yourself before APPROVE/REVISE/REJECT.
allowed-tools: Read Bash Grep Glob
invocation: claude
subagent: true
metadata:
  author: finroot
  version: "1.0.0"
---

# Review Report

When to use: a `work/reports/<wave>/*.report.md` is ready.

Process (follow `core/review-protocol.md`):
1. Read the report; confirm it has real command output, not claims.
2. Re-run the task's acceptance commands yourself; capture exit codes + output (FM-09).
3. Check guardrails: disjoint writes honored, no secrets, in scope, no silent failures (FM-11),
   numbers cited, confidence labeled.
4. Decide: APPROVE (all pass) · REVISE (specific fixes) · REJECT (wrong approach → attic/).
5. Emit `review.decision` with exit codes.

Runs in a subagent context (read-heavy). Trust only your own captured output.
