"""Tests for RiskAssessorAgent and PortfolioOptimizerAgent (wave-4, task 03).

Minimum 12 tests covering:
- RiskAssessor with mock returns → VaR/volatility in tool_outputs
- RiskAssessor with missing data → graceful error in tool_outputs
- PortfolioOptimizer with mock holdings → allocation analysis
- Audit trail entries after each agent
"""

from __future__ import annotations

import math
from pathlib import Path
from tempfile import mkdtemp

import numpy as np
import pytest

from finroot.agents.portfolio_agent import PortfolioOptimizerAgent
from finroot.agents.risk_agent import RiskAssessorAgent
from finroot.audit.trail import AuditTrail
from finroot.llm.mock import MockProvider
from finroot.schemas.state import AgentState
from finroot.tools.market import MarketDataTool
from finroot.tools.portfolio_sim import PortfolioSimulatorTool
from finroot.tools.risk import RiskCalculationTool

# ======================================================================
# RiskAssessorAgent tests
# ======================================================================


class TestRiskAssessorAgent:
    """Risk metric computation agent."""

    def test_returns_produce_risk_metrics(self):
        """RiskAssessor with mock returns produces VaR/volatility in tool_outputs."""
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        agent = RiskAssessorAgent(
            llm=MockProvider(),
            tools=[
                RiskCalculationTool(audit=audit),
                PortfolioSimulatorTool(audit=audit),
            ],
            audit=audit,
        )
        returns = [0.01, -0.02, 0.015, -0.005, 0.008, 0.012, -0.01, 0.005]
        state = AgentState(
            query="assess risk",
            twin_snapshot={"returns": returns},
        )
        result = agent.act(state)

        metrics = [o for o in result.tool_outputs if o.get("type") == "risk_metrics"]
        assert len(metrics) == 1
        m = metrics[0]
        assert m["agent"] == "risk_assessor"
        assert isinstance(m["volatility_annual"], float)
        assert m["volatility_annual"] > 0
        assert isinstance(m["var_95"], float)
        assert isinstance(m["cvar_95"], float)
        assert m["max_drawdown"] >= 0

        arr = np.array(returns)
        std = float(np.std(arr, ddof=1))
        ref_vol = std * math.sqrt(252)
        assert m["volatility_annual"] == pytest.approx(ref_vol, rel=1e-6)

    def test_missing_data_produces_error(self):
        """RiskAssessor with no returns or holdings produces graceful error."""
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        agent = RiskAssessorAgent(
            llm=MockProvider(),
            audit=audit,
        )
        state = AgentState(query="assess risk")
        result = agent.act(state)

        errors = [o for o in result.tool_outputs if o.get("type") == "error"]
        assert len(errors) >= 1
        assert "no returns or holdings data" in errors[0]["error"]

    def test_holdings_produce_monte_carlo(self):
        """RiskAssessor with mock holdings runs Monte Carlo simulation."""
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        agent = RiskAssessorAgent(
            llm=MockProvider(),
            tools=[
                RiskCalculationTool(audit=audit),
                PortfolioSimulatorTool(audit=audit, mock=True),
            ],
            audit=audit,
        )
        holdings = [
            {"symbol": "AAPL", "weight": 0.6},
            {"symbol": "GOOGL", "weight": 0.4},
        ]
        state = AgentState(
            query="assess risk",
            twin_snapshot={"holdings": holdings},
        )
        result = agent.act(state)

        mc = [o for o in result.tool_outputs if o.get("type") == "monte_carlo"]
        assert len(mc) == 1
        m = mc[0]
        assert m["agent"] == "risk_assessor"
        assert isinstance(m["expected_return"], float)
        assert isinstance(m["p10_return"], float)
        assert isinstance(m["p90_return"], float)
        assert isinstance(m["probability_of_loss"], float)
        assert 0 <= m["probability_of_loss"] <= 1

    def test_both_returns_and_holdings(self):
        """RiskAssessor with both returns and holdings computes both."""
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        agent = RiskAssessorAgent(
            llm=MockProvider(),
            tools=[
                RiskCalculationTool(audit=audit),
                PortfolioSimulatorTool(audit=audit, mock=True),
            ],
            audit=audit,
        )
        returns = [0.01, -0.02, 0.015, -0.005, 0.008]
        holdings = [{"symbol": "AAPL", "weight": 1.0}]
        state = AgentState(
            query="assess risk",
            twin_snapshot={"returns": returns, "holdings": holdings},
        )
        result = agent.act(state)

        types = {o.get("type") for o in result.tool_outputs}
        assert "risk_metrics" in types
        assert "monte_carlo" in types

    def test_returns_from_tool_outputs(self):
        """RiskAssessor reads returns from tool_outputs when no twin_snapshot."""
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        agent = RiskAssessorAgent(
            llm=MockProvider(),
            tools=[
                RiskCalculationTool(audit=audit),
                PortfolioSimulatorTool(audit=audit),
            ],
            audit=audit,
        )
        returns = [0.005, -0.003, 0.01, -0.008, 0.002]
        state = AgentState(
            query="assess risk",
            tool_outputs=[{"returns": returns}],
        )
        result = agent.act(state)

        metrics = [o for o in result.tool_outputs if o.get("type") == "risk_metrics"]
        assert len(metrics) == 1
        assert metrics[0]["volatility_annual"] > 0

    def test_empty_holdings_no_error(self):
        """RiskAssessor with empty holdings list does not run sim."""
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        agent = RiskAssessorAgent(
            llm=MockProvider(),
            audit=audit,
        )
        state = AgentState(
            query="assess risk",
            twin_snapshot={"holdings": []},
        )
        result = agent.act(state)

        errors = [o for o in result.tool_outputs if o.get("type") == "error"]
        assert len(errors) >= 1


# ======================================================================
# PortfolioOptimizerAgent tests
# ======================================================================


class TestPortfolioOptimizerAgent:
    """Portfolio allocation analysis agent."""

    def test_holdings_produce_allocation_analysis(self):
        """PortfolioOptimizer with mock holdings produces allocation analysis."""
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        agent = PortfolioOptimizerAgent(
            llm=MockProvider(),
            tools=[
                MarketDataTool(audit=audit, mock=True),
                RiskCalculationTool(audit=audit),
                PortfolioSimulatorTool(audit=audit, mock=True),
            ],
            audit=audit,
        )
        holdings = [
            {"symbol": "AAPL", "weight": 0.6},
            {"symbol": "GOOGL", "weight": 0.4},
        ]
        state = AgentState(
            query="optimise portfolio",
            twin_snapshot={"holdings": holdings},
        )
        result = agent.act(state)

        types = {o.get("type") for o in result.tool_outputs}
        assert "current_prices" in types
        assert "allocation_analysis" in types
        assert "rebalancing_comparison" in types

        allocation = [o for o in result.tool_outputs if o.get("type") == "allocation_analysis"]
        assert len(allocation) == 1
        assert len(allocation[0]["current_allocation"]) == 2
        for entry in allocation[0]["current_allocation"]:
            assert "symbol" in entry
            assert "weight" in entry
            assert entry["weight"] > 0

        rebal = [o for o in result.tool_outputs if o.get("type") == "rebalancing_comparison"]
        assert len(rebal) == 1
        sims = rebal[0]["simulations"]
        assert len(sims) == 2
        labels = {s["label"] for s in sims}
        assert labels == {"current", "equal_weight"}

    def test_shares_based_holdings(self):
        """PortfolioOptimizer handles shares-based holdings."""
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        agent = PortfolioOptimizerAgent(
            llm=MockProvider(),
            tools=[
                MarketDataTool(audit=audit, mock=True),
                RiskCalculationTool(audit=audit),
                PortfolioSimulatorTool(audit=audit, mock=True),
            ],
            audit=audit,
        )
        holdings = [
            {"symbol": "AAPL", "shares": 10},
            {"symbol": "GOOGL", "shares": 5},
        ]
        state = AgentState(
            query="optimise portfolio",
            twin_snapshot={"holdings": holdings},
        )
        result = agent.act(state)

        analysis = [o for o in result.tool_outputs if o.get("type") == "allocation_analysis"]
        assert len(analysis) == 1
        weights = [e["weight"] for e in analysis[0]["current_allocation"]]
        assert all(w > 0 for w in weights)
        assert abs(sum(weights) - 1.0) < 0.01

    def test_missing_holdings_produces_error(self):
        """PortfolioOptimizer with no holdings produces graceful error."""
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        agent = PortfolioOptimizerAgent(
            llm=MockProvider(),
            audit=audit,
        )
        state = AgentState(query="optimise portfolio")
        result = agent.act(state)

        errors = [o for o in result.tool_outputs if o.get("type") == "error"]
        assert len(errors) >= 1
        assert "no holdings data" in errors[0]["error"]

    def test_holdings_from_tool_outputs(self):
        """PortfolioOptimizer reads holdings from tool_outputs."""
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        agent = PortfolioOptimizerAgent(
            llm=MockProvider(),
            tools=[
                MarketDataTool(audit=audit, mock=True),
                RiskCalculationTool(audit=audit),
                PortfolioSimulatorTool(audit=audit, mock=True),
            ],
            audit=audit,
        )
        holdings = [
            {"symbol": "AAPL", "weight": 1.0},
        ]
        state = AgentState(
            query="optimise portfolio",
            tool_outputs=[{"holdings": holdings}],
        )
        result = agent.act(state)

        prices = [o for o in result.tool_outputs if o.get("type") == "current_prices"]
        assert len(prices) == 1
        assert "AAPL" in prices[0]["prices"]

    def test_single_holding_still_simulates(self):
        """PortfolioOptimizer with one holding still produces comparison."""
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        agent = PortfolioOptimizerAgent(
            llm=MockProvider(),
            tools=[
                MarketDataTool(audit=audit, mock=True),
                RiskCalculationTool(audit=audit),
                PortfolioSimulatorTool(audit=audit, mock=True),
            ],
            audit=audit,
        )
        holdings = [{"symbol": "AAPL", "weight": 1.0}]
        state = AgentState(
            query="optimise portfolio",
            twin_snapshot={"holdings": holdings},
        )
        result = agent.act(state)

        types = {o.get("type") for o in result.tool_outputs}
        assert "rebalancing_comparison" in types


# ======================================================================
# Audit trail tests
# ======================================================================


class TestAuditTrailAgents:
    """Audit trail entries generated by agent tool calls."""

    def test_risk_assessor_emits_audit_events(self):
        """RiskAssessor tool calls produce audit trail entries."""
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        agent = RiskAssessorAgent(
            llm=MockProvider(),
            tools=[
                RiskCalculationTool(audit=audit),
                PortfolioSimulatorTool(audit=audit),
            ],
            audit=audit,
        )
        returns = [0.01, -0.02, 0.015, -0.005, 0.008]
        state = AgentState(
            query="assess risk",
            twin_snapshot={"returns": returns},
        )
        agent.act(state)

        events = audit.replay()
        tool_called = [e for e in events if e.type == "tool.called"]
        assert len(tool_called) >= 1
        assert tool_called[0].payload["tool"] == "risk_calculation"

    def test_portfolio_optimizer_emits_audit_events(self):
        """PortfolioOptimizer tool calls produce audit trail entries."""
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        agent = PortfolioOptimizerAgent(
            llm=MockProvider(),
            tools=[
                MarketDataTool(audit=audit, mock=True),
                RiskCalculationTool(audit=audit),
                PortfolioSimulatorTool(audit=audit, mock=True),
            ],
            audit=audit,
        )
        holdings = [{"symbol": "AAPL", "weight": 1.0}]
        state = AgentState(
            query="optimise portfolio",
            twin_snapshot={"holdings": holdings},
        )
        agent.act(state)

        events = audit.replay()
        tool_called = [e for e in events if e.type == "tool.called"]
        assert len(tool_called) >= 2  # market_data + portfolio_simulator


# ======================================================================
# Edge case tests
# ======================================================================


class TestEdgeCases:
    """Additional edge cases for both agents."""

    def test_risk_bad_returns_type_ignored(self):
        """RiskAssessor gracefully handles non-list returns in snapshot."""
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        agent = RiskAssessorAgent(
            llm=MockProvider(),
            audit=audit,
        )
        state = AgentState(
            query="assess risk",
            twin_snapshot={"returns": "not-a-list"},
        )
        result = agent.act(state)
        errors = [o for o in result.tool_outputs if o.get("type") == "error"]
        assert len(errors) >= 1

    def test_portfolio_holdings_missing_symbol(self):
        """PortfolioOptimizer with holdings missing 'symbol' returns error."""
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        agent = PortfolioOptimizerAgent(
            llm=MockProvider(),
            tools=[
                MarketDataTool(audit=audit, mock=True),
                PortfolioSimulatorTool(audit=audit, mock=True),
            ],
            audit=audit,
        )
        holdings = [{"weight": 1.0}]
        state = AgentState(
            query="optimise portfolio",
            twin_snapshot={"holdings": holdings},
        )
        result = agent.act(state)
        errors = [o for o in result.tool_outputs if o.get("type") == "error"]
        assert len(errors) >= 1
