# Report wave-11/06 — More Golden Tests + Edge Cases

## Result
DONE

## What I built
- `tests/golden/test_golden_portfolio.py` — expanded with 4 new tests (diversification, rebalancing, risk assessment, optimization)
- `tests/golden/test_golden_risk.py` — new file with 7 tests (risk metrics, stress testing, tolerance matching, risk warnings, plan, confidence, intent)
- `tests/golden/test_golden_news.py` — new file with 7 tests (recommendation, news retrieval, sentiment analysis, citations, actions, intent, plan)
- `tests/golden/test_golden_international.py` — new file with 6 tests (recommendation, currency concepts, market comparison, actions, citations, FX risk)

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -m pytest tests/golden/ -v -m golden
collected 46 items

tests/golden/test_golden_international.py ......                         [ 13%]
tests/golden/test_golden_news.py .......                                 [ 28%]
tests/golden/test_golden_portfolio.py ............                       [ 54%]
tests/golden/test_golden_risk.py .......                                 [ 69%]
tests/golden/test_golden_tax.py .......                                  [ 84%]
tests/golden/test_golden_trap.py .......                                 [100%]

======================= 46 passed in 8.36s =======================

$ ruff check tests/golden/
All checks passed!
```

## Tests
- 24 new golden tests added (from 22 → 46 total, target 40+)
- All 46 pass in mock mode
- ruff clean (0 errors)

### Test breakdown
| File | Before | After | New |
|---|---|---|---|
| `test_golden_portfolio.py` | 8 | 12 | +4 |
| `test_golden_risk.py` | — | 7 | +7 |
| `test_golden_news.py` | — | 7 | +7 |
| `test_golden_international.py` | — | 6 | +6 |
| `test_golden_tax.py` | 7 | 7 | 0 |
| `test_golden_trap.py` | 7 | 7 | 0 |
| **Total** | **22** | **46** | **+24** |

## Decisions / deviations
- Risk metrics test (`test_risk_metrics_in_tool_outputs`) checks for `monte_carlo`/`expected_return`/`probability_of_loss` rather than `var_95`/`sharpe_ratio` because the mock pipeline's `twin_snapshot` lacks `returns` data, so `RiskAssessorAgent._compute_risk_metrics()` is never called — only Monte Carlo runs via holdings. This is a real limitation of the mock test fixture (no returns data in twin snapshot), not a bug.
- International tests adapt to the pipeline's existing intent classification (no dedicated `INTERNATIONAL`/`CURRENCY` intent exists; queries route to `PORTFOLIO`, `NEWS_IMPACT`, `TAX`, or `GENERAL` based on keywords). Tests verify observable behavior rather than forcing a non-existent intent.

## Surprises / gotchas
- None added to `docs/waves/wave-11-gotchas.md` — all findings were minor test-assertion adjustments verifiable by running the pipeline.

## Follow-ups (for orchestrator triage — do NOT build now)
- Consider adding `returns` data to mock `twin_snapshot` so `RiskAssessorAgent._compute_risk_metrics()` exercises `var_95`/`cvar_95`/`sharpe_ratio` paths in golden tests.
- Consider adding a dedicated `Intent.INTERNATIONAL` or `Intent.CURRENCY` for cross-border/forex queries to improve routing coverage.

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
