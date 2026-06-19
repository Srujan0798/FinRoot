"""RiskAssessorAgent — computes VaR, volatility, Sharpe, and Monte Carlo simulation.

Part of the sub-agent fleet (wave-4, task 03). Runs on RISK_ASSESSMENT intent.
"""

from __future__ import annotations

import logging
from typing import Any

from finroot.agents.base import BaseAgent
from finroot.audit.trail import AuditTrail
from finroot.llm.base import LLMProvider
from finroot.schemas.state import AgentState
from finroot.tools.portfolio_sim import PortfolioSimulatorTool, SimInput
from finroot.tools.risk import RiskCalculationTool, RiskInput

logger = logging.getLogger(__name__)


class RiskAssessorAgent(BaseAgent):
    """ReAct sub-agent that computes risk metrics and runs Monte Carlo simulation.

    Tools:
        - RiskCalculationTool: VaR, volatility, Sharpe, max drawdown
        - PortfolioSimulatorTool: Monte Carlo portfolio simulation
    """

    name = "risk_assessor"
    tools: list = []

    def __init__(
        self,
        llm: LLMProvider,
        tools: list | None = None,
        audit: AuditTrail | None = None,
    ) -> None:
        _tools = tools or [
            RiskCalculationTool(audit=audit),
            PortfolioSimulatorTool(audit=audit),
        ]
        super().__init__(llm=llm, tools=_tools, audit=audit)

    def act(self, state: AgentState) -> AgentState:
        """Run risk assessment: extract returns/holdings, compute metrics, simulate.

        Args:
            state: current AgentState with potential returns or holdings data.

        Returns:
            Updated AgentState with risk metrics and/or simulation in tool_outputs.
        """
        returns = self._extract_returns(state)
        holdings = self._extract_holdings(state)

        if returns is not None and len(returns) >= 2:
            self._compute_risk_metrics(state, returns)

        if holdings is not None and len(holdings) > 0:
            self._run_monte_carlo(state, holdings)

        if returns is None and holdings is None:
            state.tool_outputs.append({
                "agent": self.name,
                "type": "error",
                "error": (
                    "RiskAssessorAgent: no returns or holdings data available "
                    "in state. Provide returns (list of float) or holdings "
                    "(list of dict with 'weight' field) to compute risk metrics."
                ),
            })

        return state

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_returns(state: AgentState) -> list[float] | None:
        """Pull daily returns from tool_outputs or twin_snapshot."""
        for out in state.tool_outputs:
            val = out.get("returns")
            if isinstance(val, list) and val:
                try:
                    return [float(v) for v in val]
                except (TypeError, ValueError):
                    continue
        snapshot = state.twin_snapshot
        val = snapshot.get("returns") if isinstance(snapshot, dict) else None
        if isinstance(val, list) and len(val) >= 2:
            try:
                return [float(v) for v in val]
            except (TypeError, ValueError):
                pass
        return None

    @staticmethod
    def _extract_holdings(state: AgentState) -> list[dict[str, Any]] | None:
        """Pull holdings from tool_outputs or twin_snapshot."""
        for out in state.tool_outputs:
            val = out.get("holdings")
            if isinstance(val, list) and val:
                return val
        snapshot = state.twin_snapshot
        val = snapshot.get("holdings") if isinstance(snapshot, dict) else None
        if isinstance(val, list) and val:
            return val
        return None

    # ------------------------------------------------------------------
    # Computation steps
    # ------------------------------------------------------------------

    def _compute_risk_metrics(self, state: AgentState, returns: list[float]) -> None:
        """Call RiskCalculationTool and record results."""
        try:
            result = self._call_tool(
                state, "risk_calculation", RiskInput(returns=returns)
            )
            state.tool_outputs.append({
                "agent": self.name,
                "type": "risk_metrics",
                "volatility_annual": result.volatility_annual,
                "var_95": result.var_95,
                "cvar_95": result.cvar_95,
                "sharpe_ratio": result.sharpe_ratio,
                "max_drawdown": result.max_drawdown,
                "citation": result.citation,
            })
        except Exception as exc:
            logger.error("RiskAssessorAgent risk calculation failed: %s", exc)
            state.tool_outputs.append({
                "agent": self.name,
                "type": "error",
                "error": f"Risk calculation failed: {exc}",
            })

    def _run_monte_carlo(
        self, state: AgentState, holdings: list[dict[str, Any]]
    ) -> None:
        """Call PortfolioSimulatorTool and record results."""
        try:
            sim_input = SimInput(holdings=holdings, horizon_years=1, scenarios=1000)
            result = self._call_tool(state, "portfolio_simulator", sim_input)
            state.tool_outputs.append({
                "agent": self.name,
                "type": "monte_carlo",
                "expected_return": result.expected_return,
                "p10_return": result.p10_return,
                "p90_return": result.p90_return,
                "probability_of_loss": result.probability_of_loss,
                "citation": result.citation,
            })
        except Exception as exc:
            logger.error("RiskAssessorAgent Monte Carlo simulation failed: %s", exc)
            state.tool_outputs.append({
                "agent": self.name,
                "type": "error",
                "error": f"Monte Carlo simulation failed: {exc}",
            })


__all__ = ["RiskAssessorAgent"]
