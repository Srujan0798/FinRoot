# Task wave-3/03 — RiskCalculationTool + PortfolioSimulatorTool

> Read `work/WORKER_PROMPT.md` then build. Parallel with other wave-3 tasks.

## Objective
Pure-Python risk metrics (volatility, VaR, CVaR, Sharpe, max drawdown) and Monte Carlo portfolio
simulation. No external deps required — stdlib math + optional numpy for performance.

## Writes (ONLY these)
- `src/finroot/tools/risk.py`
- `src/finroot/tools/portfolio_sim.py`
- `tests/unit/test_tools_risk.py`

## Forbid
All other `src/finroot/tools/` files.

## Contract
Read `.specify/specs/wave-3/contracts/tools.contract.md` § RiskCalculationTool, § PortfolioSimulatorTool.

## Steps
1. `RiskCalculationTool(BaseTool)`:
   - Formulas (all cited in output):
     - `volatility_annual = std(returns) * sqrt(252)`
     - `var_95 = percentile(returns, 5%)` (historical, not parametric)
     - `cvar_95 = mean(returns below var_95)`
     - `sharpe_ratio = mean(returns) / std(returns) * sqrt(252)` — `None` if std==0
     - `max_drawdown` = max peak-to-trough decline
   - Use stdlib `statistics` + `math`; if `numpy` importable use it for speed (lazy import).
   - Minimum 2 returns required; raises `ToolError` if fewer (FM-11).
   - citation: `"Computed from {n} daily returns, annualised at 252 trading days"`

2. `PortfolioSimulatorTool(BaseTool)`:
   - Monte Carlo: `scenarios` paths over `horizon_years * 252` days using random daily returns from a normal distribution (μ=0.0008, σ=0.012 per day as default).
   - Seed: `random.seed(42)` in Mock mode → deterministic.
   - `expected_return` = median final portfolio value / initial - 1
   - `p10_return`, `p90_return` = 10th/90th percentile of final values
   - `probability_of_loss` = fraction of paths ending below 1.0
   - citation: `"Monte Carlo simulation: {scenarios} paths, {horizon_years}-year horizon"`

3. Tests (minimum 14):
   - RiskCalc: known returns array → verify formulas match hand-computed values
   - RiskCalc: fewer than 2 returns raises ToolError
   - Sharpe None when all returns identical
   - PortfolioSim: deterministic in mock mode (same seed → same output)
   - PortfolioSim: 0% loss probability on always-positive return stream
   - Holdings weight validation (weights should be > 0)

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_tools_risk.py -v
ruff check src/finroot/tools/risk.py src/finroot/tools/portfolio_sim.py
```

## Report
`work/reports/wave-3/03-risk-portfolio-tools.report.md`
