# Task wave-5/04 — Self-Consistency (N candidates → vote)

> Read `work/WORKER_PROMPT.md` then build. Parallel with tasks 01, 03.

## Objective
Implement `SelfConsistency` — generate N candidates with varied parameters and pick the majority
vote. Used for high-stakes queries to reduce variance.

## Writes (ONLY these)
- `src/finroot/reasoning/consistency.py`
- `tests/unit/test_consistency.py`

## Forbid
All other `src/finroot/reasoning/` files.

## Contract
Read `.specify/specs/wave-5/contracts/reasoning.contract.md` § Self-Consistency.
Read `src/finroot/schemas/recommendation.py` for `Recommendation`.

## Steps
1. `SelfConsistency`:
   - `N_CANDIDATES = 3`
   - `check(state: AgentState) -> ConsistencyResult`:
     - Generate 3 candidates from the same query (mock mode: deterministic seeds; live: vary temperature)
     - Compare core recommendation (the answer text) for agreement
     - `winner` = the candidate that appears most often (majority vote)
     - `agreement_score` = fraction of candidates that match the winner (0.0-1.0)
     - If `agreement_score < 0.7`: `dissenting_view = "Low consensus — verify independently"`
     - In mock mode: generate 3 variants by rewording the original candidate

2. Tests (minimum 10):
   - 3 identical candidates → agreement_score=1.0, no dissent
   - 2 agree, 1 differs → agreement_score=0.67, winner is majority
   - All 3 disagree → agreement_score=0.0, dissenting_view set
   - Result candidates list has exactly N items
   - Mock mode is deterministic (same input → same output)

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_consistency.py -v
ruff check src/finroot/reasoning/consistency.py
```

## Report
`work/reports/wave-5/04-consistency.report.md`
