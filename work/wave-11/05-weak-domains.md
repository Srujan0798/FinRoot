# Task wave-11/05 — Weak Domain Improvements (portfolio/risk/international/news)

> Read `work/WORKER_PROMPT.md` then build. Directly boosts FRB scores.

## Objective
Improve the pipeline for the 4 weakest domains: portfolio (0.520), risk (0.535), international (0.540), news_impact (0.587). These domains need better tool coverage and synthesis.

## Writes (ONLY these)
- `src/finroot/tools/portfolio_sim.py` (improve simulation)
- `src/finroot/tools/risk.py` (improve risk metrics)
- `src/finroot/tools/news.py` (improve news retrieval)
- `src/finroot/tools/macro.py` (improve international data)

## Forbid
`evals/**`, `data/gold/**`, `tests/**` (other tasks).

## Steps
1. Read the FRB questions for these domains to understand what's expected.
2. Improve `portfolio_sim.py`:
   - Add more realistic Monte Carlo parameters
   - Add portfolio rebalancing simulation
   - Add tax-aware simulation
   - Ensure citations include methodology
3. Improve `risk.py`:
   - Add more risk metrics (VaR, CVaR, Sharpe, max drawdown)
   - Add stress testing
   - Add scenario analysis
   - Ensure citations include formulas
4. Improve `news.py`:
   - Add more news sources
   - Add sentiment analysis integration
   - Add news impact scoring
   - Ensure citations include source and date
5. Improve `macro.py`:
   - Add more international indicators
   - Add currency conversion
   - Add cross-country comparison
   - Ensure citations include data source

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_tools_risk.py tests/unit/test_tools_market.py -v
ruff check src/finroot/tools/portfolio_sim.py src/finroot/tools/risk.py src/finroot/tools/news.py src/finroot/tools/macro.py
```

## Report
`work/reports/wave-11/05-weak-domains.report.md`
