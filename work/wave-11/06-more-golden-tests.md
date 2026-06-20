# Task wave-11/06 — More Golden Tests + Edge Cases

> Read `work/WORKER_PROMPT.md` then build. Adds reasoning quality proof.

## Objective
Expand the golden test suite with more edge cases, weak domain coverage, and adversarial scenarios.
Target: 40+ golden tests (from 22).

## Writes (ONLY these)
- `tests/golden/test_golden_portfolio.py` (expand existing)
- `tests/golden/test_golden_risk.py` (new)
- `tests/golden/test_golden_news.py` (new)
- `tests/golden/test_golden_international.py` (new)

## Forbid
`src/**` (import only), `evals/**`, `data/gold/**`.

## Steps
1. Read existing `tests/golden/` to understand the pattern.
2. Expand `test_golden_portfolio.py`:
   - Add tests for portfolio diversification
   - Add tests for portfolio rebalancing
   - Add tests for portfolio risk assessment
   - Add tests for portfolio optimization
3. Create `test_golden_risk.py` (5+ tests):
   - Risk metrics calculation (VaR, CVaR, Sharpe)
   - Stress testing
   - Scenario analysis
   - Risk tolerance matching
   - Risk warnings
4. Create `test_golden_news.py` (5+ tests):
   - News retrieval
   - Sentiment analysis
   - News impact scoring
   - News citations
   - News freshness
5. Create `test_golden_international.py` (5+ tests):
   - Currency conversion
   - International markets
   - Cross-country comparison
   - FX risk
   - International tax
6. Each test should run the full pipeline and verify the recommendation quality.
7. Use `@pytest.mark.golden` marker.

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/golden/ -v -m golden
ruff check tests/golden/
```

## Report
`work/reports/wave-11/06-more-golden-tests.report.md`
