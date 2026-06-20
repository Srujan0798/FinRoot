# Review Protocol

How the orchestrator reviews a worker report. **Evidence before approval, always (FM-09).**

## On report received
1. Emit `report.received` to the session events log.
2. Read the report. Confirm it used `work/REPORT_TEMPLATE.md` and includes real command output.
3. **Re-run the acceptance commands yourself** (do not trust the report's claims). Capture output.
4. Run the verifier sub-agent (`agents/verifier.md`) for an independent read on risky changes.
5. Check guardrails: disjoint writes respected? secrets? scope? silent failures? cited numbers?

## Decision
- **APPROVE** — all acceptance commands pass with output; guardrails clean → `/merge`.
- **REVISE** — close but failing/incomplete. Rewrite the task brief with *specific* fixes (not
  "try again"). Re-dispatch. Second REVISE on the same task → interview the user (`interviewer`).
- **REJECT** — wrong approach / out of scope. Move the work to `attic/`, write why, replan.

## Emit
`review.decision` (APPROVE|REVISE|REJECT) with the acceptance command exit codes to the events log.

## Acceptance is non-negotiable
"The worker said it passes" is not evidence. The orchestrator's own captured command output is.
A wave is only SHIPPED when the spec's acceptance block passes in the orchestrator's hands.

## Swiss-cheese review layers (stack them)
Pydantic boundary · ruff · unit · integration · acceptance contract · evals (W6+) · verifier
sub-agent · (weekly) human transcript review. No single layer is trusted alone (§6.8).
