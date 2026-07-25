"""Edge-case and boundary-condition tests for critical components.

Covers: Pydantic schema validation, risk tool boundaries, tax tool edge cases,
and profile field handling.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from finroot.schemas.finance import Holding, Money, Portfolio
from finroot.schemas.state import AgentState
from finroot.tools.base import ToolCallError
from finroot.tools.profile import (
    ProfileReadInput,
    ProfileWriteInput,
    UserProfileTool,
)
from finroot.tools.risk import RiskCalculationTool, RiskInput, RiskOutput
from finroot.tools.tax import TaxInput, TaxOutput, TaxRuleTool

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def risk_tool() -> RiskCalculationTool:
    return RiskCalculationTool()


@pytest.fixture()
def tax_tool() -> TaxRuleTool:
    return TaxRuleTool()


@pytest.fixture()
def profiles_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect profiles JSON to a temp directory."""
    p = tmp_path / "twin_profiles.json"
    profiles = [
        {
            "user_id": "edge_user",
            "name": "Edge Tester",
            "risk_tolerance": "moderate",
            "portfolio_value_inr": 2000000,
        },
    ]
    p.write_text(json.dumps(profiles))
    monkeypatch.setattr("finroot.tools.profile._PROFILES_PATH", p)

    import finroot.memory.digital_twin as _twin_mod

    def _raise(*_args, **_kwargs):
        raise RuntimeError("DigitalTwinStore stubbed out for tests")

    monkeypatch.setattr(_twin_mod, "DigitalTwinStore", _raise, raising=True)
    monkeypatch.setattr(_twin_mod, "DigitalTwin", _raise, raising=True)
    yield p


@pytest.fixture()
def profile_tool() -> UserProfileTool:
    return UserProfileTool()


# ===========================================================================
# Schema edge cases — Holding
# ===========================================================================


@pytest.mark.wave1
class TestHoldingEdgeCases:
    def test_holding_zero_quantity(self) -> None:
        h = Holding(symbol="RELIANCE", name="Reliance", quantity=0)
        assert h.quantity == 0
        assert h.market_value is None

    def test_holding_zero_cost_basis(self) -> None:
        h = Holding(symbol="TCS", name="TCS", cost_basis=0)
        assert h.cost_basis == 0
        assert h.unrealized_pnl is None

    def test_holding_empty_symbol_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Holding(symbol="", name="Reliance")

    def test_holding_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Holding(symbol="RELIANCE", name="")

    def test_holding_negative_quantity_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Holding(symbol="RELIANCE", name="Reliance", quantity=-1)

    def test_holding_negative_cost_basis_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Holding(symbol="RELIANCE", name="Reliance", cost_basis=-100)

    def test_holding_market_price_without_as_of_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Holding(symbol="RELIANCE", name="Reliance", market_price=2500)

    def test_holding_none_quantity_market_value(self) -> None:
        h = Holding(symbol="RELIANCE", name="Reliance")
        assert h.market_value is None

    def test_holding_none_quantity_unrealized_pnl(self) -> None:
        h = Holding(symbol="RELIANCE", name="Reliance")
        assert h.unrealized_pnl is None


# ===========================================================================
# Schema edge cases — Money
# ===========================================================================


@pytest.mark.wave1
class TestMoneyEdgeCases:
    def test_money_zero_amount(self) -> None:
        m = Money(amount="0", currency="INR")
        assert m.amount == "0"

    def test_money_large_amount(self) -> None:
        m = Money(amount="99999999999999999.99", currency="INR")
        assert m.amount == "99999999999999999.99"

    def test_money_empty_amount_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Money(amount="", currency="INR")

    def test_money_invalid_decimal_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Money(amount="abc", currency="INR")

    def test_money_short_currency_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Money(amount="100", currency="IN")

    def test_money_long_currency_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Money(amount="100", currency="INDI")

    def test_money_currency_uppercased(self) -> None:
        m = Money(amount="100", currency="inr")
        assert m.currency == "INR"


# ===========================================================================
# Schema edge cases — Portfolio
# ===========================================================================


@pytest.mark.wave1
class TestPortfolioEdgeCases:
    def test_empty_portfolio(self) -> None:
        p = Portfolio()
        assert p.holdings == []
        assert p.base_currency == "USD"

    def test_portfolio_with_many_holdings(self) -> None:
        holdings = [Holding(symbol=f"T{i}", name=f"Stock {i}") for i in range(100)]
        p = Portfolio(holdings=holdings)
        assert len(p.holdings) == 100


# ===========================================================================
# Schema edge cases — AgentState
# ===========================================================================


@pytest.mark.wave1
class TestAgentStateEdgeCases:
    def test_agent_state_minimal(self) -> None:
        s = AgentState(query="test")
        assert s.query == "test"
        assert s.intent is None
        assert s.twin_snapshot == {}

    def test_agent_state_extra_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AgentState(query="test", unknown_field="oops")


# ===========================================================================
# Risk tool edge cases
# ===========================================================================


@pytest.mark.wave1
class TestRiskToolEdgeCases:
    def test_risk_tool_empty_portfolio(self, risk_tool: RiskCalculationTool) -> None:
        with pytest.raises(ToolCallError, match="at least 2 returns"):
            risk_tool(RiskInput(returns=[]))

    def test_risk_tool_single_stock(self, risk_tool: RiskCalculationTool) -> None:
        with pytest.raises(ToolCallError, match="at least 2 returns"):
            risk_tool(RiskInput(returns=[0.01]))

    def test_risk_tool_two_returns(self, risk_tool: RiskCalculationTool) -> None:
        result = risk_tool(RiskInput(returns=[0.01, -0.01]))
        assert isinstance(result, RiskOutput)
        assert result.n_observations == 2

    def test_risk_tool_all_zero_returns(self, risk_tool: RiskCalculationTool) -> None:
        result = risk_tool(RiskInput(returns=[0.0, 0.0, 0.0, 0.0]))
        assert result.volatility_annual == 0.0
        assert result.sharpe_ratio is None
        assert result.sortino_ratio is None

    def test_risk_tool_identical_returns(self, risk_tool: RiskCalculationTool) -> None:
        result = risk_tool(RiskInput(returns=[0.05] * 10))
        assert result.volatility_annual == 0.0
        assert result.skewness == 0.0
        assert result.kurtosis == 0.0

    def test_risk_tool_extreme_negative_return(self, risk_tool: RiskCalculationTool) -> None:
        result = risk_tool(RiskInput(returns=[0.1, -0.5, 0.2]))
        assert result.max_drawdown > 0

    def test_risk_tool_negative_weights_rejected(self, risk_tool: RiskCalculationTool) -> None:
        with pytest.raises(ToolCallError, match="non-negative"):
            risk_tool(RiskInput(returns=[0.01, -0.01, 0.02], weights=[-0.5, 1.5]))

    def test_risk_tool_zero_sum_weights_rejected(self, risk_tool: RiskCalculationTool) -> None:
        with pytest.raises(ToolCallError, match="sum to > 0"):
            risk_tool(RiskInput(returns=[0.01, -0.01], weights=[0.0, 0.0]))

    def test_risk_tool_valid_weights_hhi(self, risk_tool: RiskCalculationTool) -> None:
        result = risk_tool(RiskInput(returns=[0.01, -0.01, 0.02], weights=[0.5, 0.3, 0.2]))
        assert result.hhi is not None
        assert result.hhi_interpretation is not None

    def test_risk_tool_no_weights_hhi_none(self, risk_tool: RiskCalculationTool) -> None:
        result = risk_tool(RiskInput(returns=[0.01, -0.01, 0.02]))
        assert result.hhi is None
        assert result.hhi_interpretation is None

    def test_risk_tool_custom_stress_shocks(self, risk_tool: RiskCalculationTool) -> None:
        result = risk_tool(RiskInput(returns=[0.01, -0.01], stress_shocks=[-0.5]))
        assert len(result.stress_tests) == 1
        assert result.stress_tests[0].shock_pct == -0.5

    def test_risk_tool_skewness_kurtosis_small_sample(self, risk_tool: RiskCalculationTool) -> None:
        result = risk_tool(RiskInput(returns=[0.01, 0.02]))
        assert result.skewness is None
        assert result.kurtosis is None


# ===========================================================================
# Tax tool edge cases
# ===========================================================================


@pytest.mark.wave1
class TestTaxToolEdgeCases:
    def test_tax_tool_zero_income(self, tax_tool: TaxRuleTool) -> None:
        result = tax_tool(TaxInput(gain=100000, gain_type="STCG", annual_income=0))
        assert isinstance(result, TaxOutput)
        assert result.tax_amount >= 0

    def test_tax_tool_very_high_income(self, tax_tool: TaxRuleTool) -> None:
        result = tax_tool(TaxInput(gain=500000, gain_type="STCG", annual_income=15000000))
        assert isinstance(result, TaxOutput)
        assert result.tax_amount > 0

    def test_tax_tool_zero_gain(self, tax_tool: TaxRuleTool) -> None:
        result = tax_tool(TaxInput(gain=0, gain_type="STCG", annual_income=500000))
        assert result.tax_amount == 0
        assert result.effective_rate_pct == 0.0

    def test_tax_tool_negative_gain_rejected(self, tax_tool: TaxRuleTool) -> None:
        with pytest.raises(ToolCallError, match="Negative gain"):
            tax_tool(TaxInput(gain=-100, gain_type="STCG", annual_income=500000))

    def test_tax_tool_ltcg_with_exemption(self, tax_tool: TaxRuleTool) -> None:
        result = tax_tool(TaxInput(gain=100000, gain_type="LTCG", annual_income=500000))
        assert result.tax_amount >= 0
        assert result.breakdown["taxable_gain"] <= 100000

    def test_tax_tool_stcg_equity(self, tax_tool: TaxRuleTool) -> None:
        result = tax_tool(TaxInput(gain=200000, gain_type="STCG_EQUITY", annual_income=1000000))
        assert isinstance(result, TaxOutput)
        assert result.tax_amount > 0

    def test_tax_tool_no_cess(self, tax_tool: TaxRuleTool) -> None:
        with_cess = tax_tool(
            TaxInput(gain=100000, gain_type="STCG", annual_income=500000, cess=True)
        )
        without_cess = tax_tool(
            TaxInput(gain=100000, gain_type="STCG", annual_income=500000, cess=False)
        )
        assert without_cess.tax_amount <= with_cess.tax_amount

    def test_tax_tool_huge_gain(self, tax_tool: TaxRuleTool) -> None:
        result = tax_tool(TaxInput(gain=100000000, gain_type="STCG", annual_income=10000000))
        assert result.tax_amount > 0


# ===========================================================================
# Profile edge cases
# ===========================================================================


@pytest.mark.wave1
class TestProfileEdgeCases:
    def test_profile_empty_name(self, profile_tool: UserProfileTool, profiles_path: Path) -> None:
        result = profile_tool(ProfileWriteInput(user_id="edge_user", updates={"name": ""}))
        assert result.data["name"] == ""

    def test_profile_extreme_age_zero(
        self, profile_tool: UserProfileTool, profiles_path: Path
    ) -> None:
        result = profile_tool(ProfileWriteInput(user_id="edge_user", updates={"age": 0}))
        assert result.data["age"] == 0

    def test_profile_extreme_age_150(
        self, profile_tool: UserProfileTool, profiles_path: Path
    ) -> None:
        result = profile_tool(ProfileWriteInput(user_id="edge_user", updates={"age": 150}))
        assert result.data["age"] == 150

    def test_profile_zero_income(self, profile_tool: UserProfileTool, profiles_path: Path) -> None:
        result = profile_tool(ProfileWriteInput(user_id="edge_user", updates={"annual_income": 0}))
        assert result.data["annual_income"] == 0

    def test_profile_negative_income(
        self, profile_tool: UserProfileTool, profiles_path: Path
    ) -> None:
        result = profile_tool(
            ProfileWriteInput(user_id="edge_user", updates={"annual_income": -50000})
        )
        assert result.data["annual_income"] == -50000

    def test_profile_missing_optional_fields(
        self, profile_tool: UserProfileTool, profiles_path: Path
    ) -> None:
        result = profile_tool(ProfileReadInput(user_id="edge_user"))
        assert "name" in result.data
        assert "risk_tolerance" in result.data
        assert result.data.get("annual_income") is None

    def test_profile_read_nonexistent_user(self, profile_tool: UserProfileTool) -> None:
        with pytest.raises(ToolCallError, match="no profile found"):
            profile_tool(ProfileReadInput(user_id="nonexistent_xyz"))

    def test_profile_write_empty_updates_rejected(
        self, profile_tool: UserProfileTool, profiles_path: Path
    ) -> None:
        with pytest.raises(ValidationError):
            profile_tool(ProfileWriteInput(user_id="edge_user", updates={}))

    def test_profile_write_nonexistent_user(
        self, profile_tool: UserProfileTool, profiles_path: Path
    ) -> None:
        with pytest.raises(ToolCallError, match="no profile found"):
            profile_tool(ProfileWriteInput(user_id="ghost_user", updates={"name": "Ghost"}))
