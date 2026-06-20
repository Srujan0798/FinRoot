# Task wave-5/02 — Refinement Loop

> Read `work/WORKER_PROMPT.md` then build. **Dispatch AFTER task 01 completes.**

## Objective
Implement `RefinementLoop` — the critique → revise → re-score cycle that iteratively improves
recommendations until they pass the quality threshold.

## Writes (ONLY these)
- `src/finroot/reasoning/refine.py`
- `tests/unit/test_refine.py`

## Forbid
All other `src/finroot/reasoning/` files.

## Contract
Read `.specify/specs/wave-5/contracts/reasoning.contract.md` § Refinement Loop.
Read `src/finroot/reasoning/critic.py` for `SelfCritic` API (task 01).

## Steps
1. `RefinementLoop`:
   - `MAX_ITERATIONS = 3`
   - `refine(state: AgentState, critic: SelfCritic) -> AgentState`:
     - Loop: score → if `passed=True`, set `state.final = state.candidate`, break
     - Else: revise `state.candidate` based on `must_fix` items:
       - Add risk warnings if risk_awareness < 0.5
       - Add citations if evidence < 0.5
       - Soften language if overconfident ("guaranteed" → "may")
       - Add reasoning steps if explainability < 0.5
     - Re-score after each revision
     - After 3 iterations if still failing: set `final.confidence = LOW`, append disclaimer
     - Each iteration → `audit_events.append(...)` with iteration number + scores

2. Tests (minimum 12):
   - First attempt passes → no refinement, state.final = state.candidate
   - First attempt fails, second passes → 1 refinement
   - All 3 attempts fail → disclaimer added, confidence=LOW
   - Audit trail has entries for each iteration
   - must_fix items addressed in revision (check answer text changed)
   - Max iterations respected (never more than 3)

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_refine.py -v
ruff check src/finroot/reasoning/refine.py
```

## Report
`work/reports/wave-5/02-refine.report.md`
