"""Tests for RiskCalculationTool and PortfolioSimulatorTool (wave-3, task 03).

Minimum 14 tests covering:
- RiskCalc: known returns → formula verification
- RiskCalc: fewer than 2 returns raises ToolError
- Sharpe=None when all returns identical
- PortfolioSim: deterministic in mock mode
- PortfolioSim: 0% loss on always-positive returns
- Holdings weight validation (weight > 0)
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from finroot.tools.base import ToolCallError
from finroot.tools.portfolio_sim import PortfolioSimulatorTool, SimInput
from finroot.tools.risk import RiskCalculationTool, RiskInput

# ======================================================================
# RiskCalculationTool tests
# ======================================================================


class TestRiskCalculationTool:
    """Risk metric computation."""

    def test_known_returns_match_formulas(self):
        """Verify tool output matches hand-computed / numpy reference values
        for a small known returns array."""
        returns = [0.01, 0.02]
        tool = RiskCalculationTool()
        result = tool(RiskInput(returns=returns))

        # Reference using numpy
        arr = np.array(returns)
        std = float(np.std(arr, ddof=1))
        ref_vol = std * math.sqrt(252)
        ref_var = float(np.percentile(arr, 5))
        ref_cvar = float(np.mean(arr[arr < ref_var])) if np.any(arr < ref_var) else 0.0
        ref_sharpe = float(np.mean(arr) / std * math.sqrt(252))
        cum = np.cumprod(1 + arr)
        running_max = np.maximum.accumulate(cum)
        ref_max_dd = float(np.max(1.0 - cum / running_max))

        assert result.volatility_annual == pytest.approx(ref_vol, rel=1e-6)
        assert result.var_95 == pytest.approx(ref_var, rel=1e-6)
        assert result.cvar_95 == pytest.approx(ref_cvar, rel=1e-6)
        assert result.sharpe_ratio == pytest.approx(ref_sharpe, rel=1e-6)
        assert result.max_drawdown == pytest.approx(ref_max_dd, rel=1e-6)

    def test_multiple_returns_consistency(self):
        """Verify consistency across a longer return series."""
        rng = np.random.default_rng(42)
        returns = list(rng.normal(0.0005, 0.01, size=100))
        tool = RiskCalculationTool()
        result = tool(RiskInput(returns=returns))

        arr = np.array(returns)
        std = float(np.std(arr, ddof=1))
        ref_vol = std * math.sqrt(252)
        ref_var = float(np.percentile(arr, 5))
        ref_cvar = float(np.mean(arr[arr < ref_var]))
        ref_sharpe = float(np.mean(arr) / std * math.sqrt(252))
        cum = np.cumprod(1 + arr)
        running_max = np.maximum.accumulate(cum)
        ref_max_dd = float(np.max(1.0 - cum / running_max))

        assert result.volatility_annual == pytest.approx(ref_vol, rel=1e-6)
        assert result.var_95 == pytest.approx(ref_var, rel=1e-6)
        assert result.cvar_95 == pytest.approx(ref_cvar, rel=1e-6)
        assert result.sharpe_ratio == pytest.approx(ref_sharpe, rel=1e-6)
        assert result.max_drawdown == pytest.approx(ref_max_dd, rel=1e-6)

    def test_fewer_than_two_returns_raises(self):
        """ToolError when fewer than 2 returns."""
        tool = RiskCalculationTool()
        with pytest.raises(ToolCallError, match="at least 2 returns"):
            tool(RiskInput(returns=[0.01]))

    def test_empty_returns_raises(self):
        """ToolError on empty list."""
        tool = RiskCalculationTool()
        with pytest.raises(ToolCallError, match="at least 2 returns"):
            tool(RiskInput(returns=[]))

    def test_sharpe_is_none_when_all_returns_identical(self):
        """Sharpe ratio is None when std is zero."""
        tool = RiskCalculationTool()
        result = tool(RiskInput(returns=[0.01, 0.01, 0.01]))
        assert result.sharpe_ratio is None

    def test_sharpe_is_none_single_return_repeated(self):
        """Also None with only two identical returns."""
        tool = RiskCalculationTool()
        result = tool(RiskInput(returns=[0.005, 0.005]))
        assert result.sharpe_ratio is None

    def test_confidence_level_variation(self):
        """Different confidence levels produce different VaR."""
        returns = [-0.05, -0.03, -0.01, 0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06]
        tool = RiskCalculationTool()
        r90 = tool(RiskInput(returns=returns, confidence=0.90))
        r99 = tool(RiskInput(returns=returns, confidence=0.99))
        # 99% VaR should be <= 90% VaR (lower tail)
        assert r99.var_95 <= r90.var_95

    def test_cvar_is_lower_than_var(self):
        """CVaR (mean of tail) should be <= VaR (tail threshold)."""
        returns = list(np.random.default_rng(42).normal(0.0, 0.02, size=200))
        tool = RiskCalculationTool()
        result = tool(RiskInput(returns=returns))
        assert result.cvar_95 <= result.var_95

    def test_positive_returns_have_zero_max_drawdown(self):
        """Strictly positive returns produce zero drawdown."""
        returns = [0.001, 0.002, 0.001, 0.003]
        tool = RiskCalculationTool()
        result = tool(RiskInput(returns=returns))
        assert result.max_drawdown == 0.0

    def test_zero_volatility_returns_low_risk(self):
        """All identical returns give None Sharpe and 0 vol."""
        returns = [0.01, 0.01, 0.01, 0.01, 0.01]
        tool = RiskCalculationTool()
        result = tool(RiskInput(returns=returns))
        assert result.sharpe_ratio is None
        assert result.volatility_annual == 0.0

    def test_output_contains_citation(self):
        """Citation string is populated correctly."""
        returns = [0.01, 0.02, -0.01]
        tool = RiskCalculationTool()
        result = tool(RiskInput(returns=returns))
        assert "3 daily returns" in result.citation
        assert "252" in result.citation


# ======================================================================
# PortfolioSimulatorTool tests
# ======================================================================


class TestPortfolioSimulatorTool:
    """Monte Carlo portfolio simulation."""

    def test_deterministic_in_mock_mode(self):
        """Same seed produces identical output."""
        holdings = [{"symbol": "RELIANCE.NS", "weight": 0.6}, {"symbol": "TCS.NS", "weight": 0.4}]
        inp = SimInput(holdings=holdings, horizon_years=1, scenarios=500)

        t1 = PortfolioSimulatorTool(mock=True)
        t2 = PortfolioSimulatorTool(mock=True)
        r1 = t1(inp)
        r2 = t2(inp)

        assert r1.expected_return == r2.expected_return
        assert r1.p10_return == r2.p10_return
        assert r1.p90_return == r2.p90_return
        assert r1.probability_of_loss == r2.probability_of_loss

    def test_zero_loss_on_always_positive_returns(self):
        """Degenerate simulation: positive drift with zero volatility must never
        produce a loss. mu/sigma are explicit SimInput fields (annual_mu /
        annual_sigma) in the current design."""
        holdings = [{"symbol": "TEST", "weight": 1.0}]
        inp = SimInput(
            holdings=holdings,
            horizon_years=1,
            scenarios=100,
            annual_mu=0.10,
            annual_sigma=0.0,  # no randomness → strictly positive drift
        )

        tool = PortfolioSimulatorTool(mock=True)
        result = tool(inp)
        assert result.probability_of_loss == 0.0

    def test_holdings_weight_zero_raises(self):
        """Weight <= 0 raises ToolError."""
        tool = PortfolioSimulatorTool()
        with pytest.raises(ToolCallError, match="weight must be positive"):
            tool(SimInput(holdings=[{"symbol": "X", "weight": 0.0}], horizon_years=1))

    def test_holdings_weight_negative_raises(self):
        """Negative weight raises ToolError."""
        tool = PortfolioSimulatorTool()
        with pytest.raises(ToolCallError, match="weight must be positive"):
            tool(SimInput(holdings=[{"symbol": "X", "weight": -0.5}], horizon_years=1))

    def test_holdings_missing_weight_raises(self):
        """Missing weight field raises ToolError."""
        tool = PortfolioSimulatorTool()
        with pytest.raises(ToolCallError, match="numeric 'weight' field"):
            tool(SimInput(holdings=[{"symbol": "X"}], horizon_years=1))

    def test_empty_holdings_raises(self):
        """Empty holdings list raises ToolError."""
        tool = PortfolioSimulatorTool()
        with pytest.raises(ToolCallError, match="at least one holding"):
            tool(SimInput(holdings=[], horizon_years=1))

    def test_expected_return_sensible_range(self):
        """Expected return should be positive given positive default μ."""
        holdings = [{"symbol": "RELIANCE.NS", "weight": 1.0}]
        tool = PortfolioSimulatorTool(mock=True)
        result = tool(SimInput(holdings=holdings, horizon_years=1, scenarios=500))
        # μ=0.0008/day over 252 days ≈ (1.0008)^252 - 1 ≈ 0.223
        assert result.expected_return > 0.05  # definitely above 5%
        assert result.expected_return < 0.50  # and below 50%

    def test_p10_lower_than_p90(self):
        """10th percentile return should be lower than 90th percentile."""
        holdings = [{"symbol": "RELIANCE.NS", "weight": 1.0}]
        tool = PortfolioSimulatorTool(mock=True)
        result = tool(SimInput(holdings=holdings, horizon_years=1, scenarios=500))
        assert result.p10_return < result.p90_return

    def test_output_contains_citation(self):
        """Citation string is populated."""
        holdings = [{"symbol": "X", "weight": 1.0}]
        tool = PortfolioSimulatorTool(mock=True)
        result = tool(SimInput(holdings=holdings, horizon_years=1, scenarios=100))
        assert "Monte Carlo" in result.citation
        assert "100 paths" in result.citation
        assert "1-year" in result.citation

    def test_mock_mode_from_env(self, monkeypatch):
        """Mock mode activated via FINROOT_LLM_PROVIDER=mock env var."""
        monkeypatch.setenv("FINROOT_LLM_PROVIDER", "mock")
        tool = PortfolioSimulatorTool()
        assert tool.mock is True
