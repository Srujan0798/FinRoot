# Report wave-3/03 — RiskCalculationTool + PortfolioSimulatorTool

## Result
DONE

## What I built
- `src/finroot/tools/risk.py` — RiskCalculationTool with RiskInput/RiskOutput Pydantic models
- `src/finroot/tools/portfolio_sim.py` — PortfolioSimulatorTool with SimInput/SimOutput Pydantic models
- `tests/unit/test_tools_risk.py` — 21 tests covering both tools

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_tools_risk.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 21 items

tests/unit/test_tools_risk.py .....................                      [100%]

============================= 21 passed in 47.02s ==============================

$ ruff check src/finroot/tools/risk.py src/finroot/tools/portfolio_sim.py
All checks passed!
```

## Tests
- 21 tests (11 RiskCalc + 10 PortfolioSim), all pass
- RiskCalc: formula verification against numpy reference, <2 returns error, Sharpe=None on zero std, confidence level variation, CVaR <= VaR, zero drawdown on positive returns, output citation
- PortfolioSim: deterministic mock mode, zero-loss on zero-sigma, weight validation (zero, negative, missing), empty holdings, sensible expected return range, p10 < p90, citation, mock mode from env

## Decisions / deviations
- Used sample standard deviation (ddof=1) for volatility computation (finance convention).
- `cvar_95` returns 0.0 when no returns fall below VaR threshold (edge case with very small samples).
- `max_drawdown` reported as a positive float (0.15 = 15% peak-to-trough decline).
- PortfolioSim uses `random.seed(42)` in mock mode for deterministic output.
- `round()` not applied to output floats; full precision preserved from computation.

## Surprises / gotchas
- None. All acceptance commands passed on first implementation attempt (after fixing test SimInput calls missing `horizon_years` field).

## Follow-ups (for orchestrator triage — do NOT build now)
- None

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
