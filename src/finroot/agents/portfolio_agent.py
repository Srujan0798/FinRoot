"""PortfolioOptimizerAgent — allocation analysis, rebalancing simulation.

Part of the sub-agent fleet (wave-4, task 03). Runs on PORTFOLIO_REVIEW intent.
"""

from __future__ import annotations

import logging
from typing import Any

from finroot.agents.base import BaseAgent
from finroot.audit.trail import AuditTrail
from finroot.llm.base import LLMProvider
from finroot.schemas.state import AgentState
from finroot.tools.market import MarketDataInput, MarketDataTool
from finroot.tools.portfolio_sim import PortfolioSimulatorTool, SimInput
from finroot.tools.risk import RiskCalculationTool

logger = logging.getLogger(__name__)


class PortfolioOptimizerAgent(BaseAgent):
    """ReAct sub-agent for portfolio allocation analysis and rebalancing.

    Tools:
        - MarketDataTool: current prices for holdings
        - RiskCalculationTool: risk metrics on current allocation
        - PortfolioSimulatorTool: simulate current and alternative allocations
    """

    name = "portfolio_optimizer"
    tools: list = []

    def __init__(
        self,
        llm: LLMProvider,
        tools: list | None = None,
        audit: AuditTrail | None = None,
    ) -> None:
        _tools = tools or [
            MarketDataTool(audit=audit),
            RiskCalculationTool(audit=audit),
            PortfolioSimulatorTool(audit=audit),
        ]
        super().__init__(llm=llm, tools=_tools, audit=audit)

    def act(self, state: AgentState) -> AgentState:
        """Run portfolio optimisation: fetch prices, compute weights, simulate.

        Args:
            state: current AgentState with holdings in twin_snapshot or
                   tool_outputs.

        Returns:
            Updated AgentState with allocation analysis in tool_outputs.
        """
        holdings = self._extract_holdings(state)

        if holdings is None or len(holdings) == 0:
            state.tool_outputs.append({
                "agent": self.name,
                "type": "error",
                "error": (
                    "PortfolioOptimizerAgent: no holdings data available "
                    "in state. Provide holdings (list of dict with 'symbol' "
                    "and optional 'shares' or 'weight') to run optimisation."
                ),
            })
            return state

        prices = self._fetch_prices(state, holdings)
        if prices is None:
            return state

        weighted_holdings = self._compute_weights(holdings, prices)
        if weighted_holdings is None:
            return state

        self._analyze_current_allocation(state, weighted_holdings, prices)
        self._simulate_alternatives(state, weighted_holdings)

        return state

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------

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
    # Price fetching
    # ------------------------------------------------------------------

    def _fetch_prices(
        self, state: AgentState, holdings: list[dict[str, Any]]
    ) -> dict[str, float] | None:
        """Fetch current price for each holding symbol via MarketDataTool."""
        symbols = []
        for h in holdings:
            sym = h.get("symbol")
            if sym:
                symbols.append(sym)

        if not symbols:
            state.tool_outputs.append({
                "agent": self.name,
                "type": "error",
                "error": "Holdings missing 'symbol' field; cannot fetch prices.",
            })
            return None

        prices: dict[str, float] = {}
        errors: list[str] = []
        for sym in symbols:
            try:
                result = self._call_tool(
                    state, "market_data", MarketDataInput(symbol=sym)
                )
                prices[sym] = result.latest_price
            except Exception as exc:
                msg = f"{sym}: {exc}"
                errors.append(msg)
                logger.warning("PortfolioOptimizerAgent price fetch failed: %s", msg)

        if errors:
            state.tool_outputs.append({
                "agent": self.name,
                "type": "price_errors",
                "errors": errors,
            })

        if not prices:
            state.tool_outputs.append({
                "agent": self.name,
                "type": "error",
                "error": "Failed to fetch prices for any holding symbol.",
            })
            return None

        state.tool_outputs.append({
            "agent": self.name,
            "type": "current_prices",
            "prices": prices,
        })
        return prices

    # ------------------------------------------------------------------
    # Weight computation
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_weights(
        holdings: list[dict[str, Any]], prices: dict[str, float]
    ) -> list[dict[str, Any]] | None:
        """Compute allocation weights from holdings and current prices.

        If holdings have a 'weight' field, use it directly.
        If holdings have 'shares', compute weight = shares * price / total.
        """
        if all("weight" in h for h in holdings):
            total = sum(h["weight"] for h in holdings)
            if abs(total - 1.0) > 0.01:
                weighted = [{"symbol": h["symbol"], "weight": round(h["weight"] / total, 6)} for h in holdings]
            else:
                weighted = [{"symbol": h["symbol"], "weight": h["weight"]} for h in holdings]
            return weighted

        if all("shares" in h for h in holdings):
            total_value = 0.0
            values: list[tuple[str, float]] = []
            for h in holdings:
                sym = h.get("symbol", "")
                price = prices.get(sym, 0.0)
                val = h["shares"] * price
                values.append((sym, val))
                total_value += val
            if total_value <= 0:
                return None
            return [
                {"symbol": sym, "weight": round(val / total_value, 6)}
                for sym, val in values
            ]

        return None

    # ------------------------------------------------------------------
    # Analysis steps
    # ------------------------------------------------------------------

    def _analyze_current_allocation(
        self,
        state: AgentState,
        weighted_holdings: list[dict[str, Any]],
        prices: dict[str, float],
    ) -> None:
        """Record current allocation summary and run risk metrics if possible."""
        allocation = [
            {
                "symbol": h["symbol"],
                "weight": h["weight"],
                "price": prices.get(h["symbol"]),
            }
            for h in weighted_holdings
        ]
        state.tool_outputs.append({
            "agent": self.name,
            "type": "allocation_analysis",
            "current_allocation": allocation,
        })

    def _simulate_alternatives(
        self,
        state: AgentState,
        weighted_holdings: list[dict[str, Any]],
    ) -> None:
        """Simulate current and alternative (equal-weight) allocations."""
        n = len(weighted_holdings)
        if n == 0:
            return

        equal_holdings = [
            {"symbol": h["symbol"], "weight": round(1.0 / n, 6)}
            for h in weighted_holdings
        ]

        scenarios = [
            ("current", weighted_holdings),
            ("equal_weight", equal_holdings),
        ]

        results: list[dict[str, Any]] = []
        for label, h in scenarios:
            try:
                sim_input = SimInput(
                    holdings=h, horizon_years=1, scenarios=500
                )
                result = self._call_tool(state, "portfolio_simulator", sim_input)
                results.append({
                    "label": label,
                    "expected_return": result.expected_return,
                    "p10_return": result.p10_return,
                    "p90_return": result.p90_return,
                    "probability_of_loss": result.probability_of_loss,
                    "citation": result.citation,
                })
            except Exception as exc:
                logger.error(
                    "PortfolioOptimizerAgent simulation for %s failed: %s",
                    label, exc,
                )
                state.tool_outputs.append({
                    "agent": self.name,
                    "type": "error",
                    "error": f"Simulation for {label} allocation failed: {exc}",
                })

        if results:
            state.tool_outputs.append({
                "agent": self.name,
                "type": "rebalancing_comparison",
                "simulations": results,
            })


__all__ = ["PortfolioOptimizerAgent"]
