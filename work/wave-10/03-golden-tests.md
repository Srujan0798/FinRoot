# Task wave-10/03 — Golden Eval Tests (hand-graded reasoning quality)

> Read `work/WORKER_PROMPT.md` then build. Proves reasoning quality to judges.

## Objective
Create `tests/golden/` — a set of hand-crafted, end-to-end tests that run the full pipeline on
specific queries and verify the reasoning quality (not just unit-level). These are the "show your
work" tests judges can run to see the agent reasoning.

## Writes (ONLY these)
- `tests/golden/__init__.py`
- `tests/golden/test_golden_portfolio.py`
- `tests/golden/test_golden_tax.py`
- `tests/golden/test_golden_trap.py`
- `tests/golden/conftest.py`

## Forbid
`evals/**`, `data/gold/**`, `src/**` (import only).

## Steps
1. `conftest.py` — shared fixtures:
   - `mock_state` fixture: builds AgentState with mock tool outputs
   - `run_pipeline` fixture: calls `interface.core.answer()` in mock mode
2. `test_golden_portfolio.py` (5+ tests):
   - Portfolio query produces allocation breakdown
   - Portfolio query includes Monte Carlo simulation
   - Portfolio query cites market data tool
   - Portfolio query has actions list
   - Portfolio query confidence is MEDIUM or HIGH
3. `test_golden_tax.py` (5+ tests):
   - Tax query for ₹2L LTCG produces ₹10,400
   - Tax query cites tax rules
   - Tax query has correct confidence
   - Tax query includes breakdown
   - Tax query mentions LTCG/STCG
4. `test_golden_trap.py` (5+ tests):
   - Emergency fund trap triggers prudence refusal
   - Emergency fund trap has LOW confidence
   - Emergency fund trap mentions "emergency fund"
   - Guaranteed returns trap triggers must_not
   - Leverage trap has risk warning
5. Each test runs the full pipeline end-to-end and checks the final Recommendation.
6. Use `@pytest.mark.golden` marker for selective running.

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/golden/ -v -m golden
ruff check tests/golden/
```

## Report
`work/reports/wave-10/03-golden-tests.report.md`
