---
name: review
description: Review worker reports — re-run acceptance yourself, then APPROVE / REVISE / REJECT.
allowed-tools: Read Bash Grep Glob
invocation: both
---

# /review [wave-N | task]

Follow `core/review-protocol.md`. Evidence before approval (FM-09).

Steps:
1. Read the report(s) in `work/reports/wave-N/`.
2. **Re-run the acceptance commands from the task/spec yourself.** Capture exit codes + output.
3. Run the `verifier` sub-agent on risky diffs.
4. Check guardrails: disjoint writes, no secrets, in-scope, no silent failures, numbers cited.
5. Decide per task: APPROVE → /merge · REVISE → rewrite brief with specific fixes · REJECT → attic/.
6. Emit `review.decision` to the events log with command exit codes.

Never approve on the worker's word alone — only on your own captured output.
