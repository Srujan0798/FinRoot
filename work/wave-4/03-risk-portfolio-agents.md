# Task wave-4/03 — RiskAssessorAgent + PortfolioOptimizerAgent

> Read `work/WORKER_PROMPT.md` then build. Parallel with tasks 01, 02, 04.

## Objective
Implement two ReAct sub-agents: `RiskAssessorAgent` (VaR, Monte Carlo) and
`PortfolioOptimizerAgent` (allocation analysis, rebalancing simulation).

## Writes (ONLY these)
- `src/finroot/agents/risk_agent.py`
- `src/finroot/agents/portfolio_agent.py`
- `tests/unit/test_agents_risk_portfolio.py`

## Forbid
All other `src/finroot/agents/` and `src/finroot/workflows/` files.

## Contract
Read `.specify/specs/wave-4/contracts/graph.contract.md` § Sub-Agents.
Read `src/finroot/agents/base.py` for `BaseAgent`.
Read `src/finroot/tools/risk.py`, `portfolio_sim.py`, `market.py` for tool APIs.

## Steps
1. `RiskAssessorAgent(BaseAgent)`:
   - `name = "risk_assessor"`
   - `tools = [RiskCalculationTool(), PortfolioSimulatorTool()]`
   - `run(state)`:
     - Extract returns/holdings from state.tool_outputs or context
     - If returns data available: compute VaR, volatility, Sharpe, max drawdown
     - If holdings available: run Monte Carlo simulation
     - Add results to tool_outputs with citations
     - Handle missing data: add tool_output with error message, not crash (FM-11)

2. `PortfolioOptimizerAgent(BaseAgent)`:
   - `name = "portfolio_optimizer"`
   - `tools = [MarketDataTool(), RiskCalculationTool(), PortfolioSimulatorTool()]`
   - `run(state)`:
     - Fetch current prices for holdings
     - Compute current allocation weights
     - Run risk metrics on current allocation
     - Simulate alternative allocations (equal-weight, risk-parity)
     - Add comparison to tool_outputs

3. Tests (minimum 12):
   - RiskAssessor with mock returns → VaR/volatility in tool_outputs
   - RiskAssessor with missing data → graceful error in tool_outputs
   - PortfolioOptimizer with mock holdings → allocation analysis
   - Audit trail entries after each agent

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_agents_risk_portfolio.py -v
ruff check src/finroot/agents/risk_agent.py src/finroot/agents/portfolio_agent.py
```

## Report
`work/reports/wave-4/03-risk-portfolio-agents.report.md`
