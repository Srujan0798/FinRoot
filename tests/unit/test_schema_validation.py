"""Tests for Pydantic schema validation — the typed spine of FinRoot.

Covers:
* Valid data passes validation for profile, holding, transaction, agent state.
* Invalid data (negative age, string income, empty symbol, missing fields) is rejected.
* JSON round-trip (serialize → deserialize) preserves data for Money, Holding, and profile-like dicts.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import BaseModel, Field, ValidationError

from finroot.schemas.enums import Domain, Intent
from finroot.schemas.finance import Holding, Horizon, Money

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

UTC_NOW = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Profile validation (using a lightweight model mirroring profile fields)
# ---------------------------------------------------------------------------


class _Profile(BaseModel):
    user_id: str
    name: str
    age: int = Field(ge=0, le=150)
    monthly_income: float = Field(ge=0)
    risk_tolerance: str = "moderate"

    model_config = {"extra": "forbid"}


@pytest.mark.wave1
class TestProfileValidation:
    def test_profile_valid(self) -> None:
        p = _Profile(user_id="u1", name="Alice", age=30, monthly_income=100000.0)
        assert p.user_id == "u1"
        assert p.age == 30
        assert p.monthly_income == 100000.0

    def test_profile_invalid_age(self) -> None:
        with pytest.raises(ValidationError):
            _Profile(user_id="u1", name="Alice", age=-5, monthly_income=100000.0)

    def test_profile_invalid_income(self) -> None:
        with pytest.raises(ValidationError):
            _Profile(user_id="u1", name="Alice", age=30, monthly_income="high")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Holding validation
# ---------------------------------------------------------------------------


@pytest.mark.wave1
class TestHoldingValidation:
    def test_holding_valid(self) -> None:
        h = Holding(symbol="AAPL", name="Apple Inc")
        assert h.symbol == "AAPL"
        assert h.domain == Domain.EQUITY

    def test_holding_empty_symbol(self) -> None:
        with pytest.raises(ValidationError):
            Holding(symbol="", name="Apple")

    def test_holding_negative_quantity_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Holding(symbol="AAPL", name="Apple", quantity=-10)

    def test_holding_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Holding(symbol="AAPL", name="Apple", bogus="x")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Transaction validation (using a lightweight model)
# ---------------------------------------------------------------------------


class _Transaction(BaseModel):
    symbol: str
    action: str
    quantity: float
    price: float

    model_config = {"extra": "forbid"}


@pytest.mark.wave1
class TestTransactionValidation:
    def test_transaction_valid(self) -> None:
        t = _Transaction(symbol="AAPL", action="buy", quantity=10, price=150.0)
        assert t.symbol == "AAPL"
        assert t.quantity == 10

    def test_transaction_missing_fields(self) -> None:
        with pytest.raises(ValidationError):
            _Transaction(symbol="AAPL")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# AgentState validation
# ---------------------------------------------------------------------------


@pytest.mark.wave1
class TestAgentStateValidation:
    def test_agent_state_valid(self) -> None:
        from finroot.schemas.state import AgentState

        s = AgentState(query="What is my risk?")
        assert s.query == "What is my risk?"
        assert s.intent is None

    def test_agent_state_missing_fields(self) -> None:
        from finroot.schemas.state import AgentState

        with pytest.raises(ValidationError):
            AgentState()  # type: ignore[call-arg]

    def test_agent_state_extra_fields_rejected(self) -> None:
        from finroot.schemas.state import AgentState

        with pytest.raises(ValidationError):
            AgentState(query="hi", unknown_field="x")  # type: ignore[call-arg]

    def test_agent_state_with_intent(self) -> None:
        from finroot.schemas.state import AgentState

        s = AgentState(query="risk", intent=Intent.RISK)
        assert s.intent is Intent.RISK


# ---------------------------------------------------------------------------
# JSON round-trip: Holding
# ---------------------------------------------------------------------------


@pytest.mark.wave1
class TestHoldingJsonRoundtrip:
    def test_holding_json_roundtrip(self) -> None:
        h = Holding(
            symbol="RELIANCE.NS",
            name="Reliance Industries",
            domain=Domain.EQUITY,
            quantity=100,
            cost_basis=2000.0,
            currency="INR",
            horizon=Horizon.LONG,
        )
        json_str = h.model_dump_json()
        h2 = Holding.model_validate_json(json_str)
        assert h2.symbol == h.symbol
        assert h2.name == h.name
        assert h2.domain == h.domain
        assert h2.quantity == h.quantity
        assert h2.cost_basis == h.cost_basis
        assert h2.currency == "INR"
        assert h2.horizon == Horizon.LONG

    def test_holding_with_market_price_roundtrip(self) -> None:
        h = Holding(
            symbol="TCS",
            name="Tata Consultancy Services",
            quantity=50,
            cost_basis=3000.0,
            market_price=3500.0,
            market_price_as_of=UTC_NOW,
        )
        h2 = Holding.model_validate_json(h.model_dump_json())
        assert h2.market_price == 3500.0
        assert h2.market_price_as_of is not None
        assert h2.market_value == 50 * 3500.0
        assert h2.unrealized_pnl == 50 * (3500.0 - 3000.0)


# ---------------------------------------------------------------------------
# JSON round-trip: Profile-like dict
# ---------------------------------------------------------------------------


@pytest.mark.wave1
class TestProfileJsonRoundtrip:
    def test_profile_json_roundtrip(self) -> None:
        p = _Profile(user_id="u42", name="Bob", age=45, monthly_income=200000.0)
        json_str = p.model_dump_json()
        p2 = _Profile.model_validate_json(json_str)
        assert p2.user_id == "u42"
        assert p2.name == "Bob"
        assert p2.age == 45
        assert p2.monthly_income == 200000.0


# ---------------------------------------------------------------------------
# JSON round-trip: Money
# ---------------------------------------------------------------------------


@pytest.mark.wave1
class TestMoneyJsonRoundtrip:
    def test_money_json_roundtrip(self) -> None:
        m = Money(amount="9999.99", currency="inr")
        json_str = m.model_dump_json()
        m2 = Money.model_validate_json(json_str)
        assert m2.amount == "9999.99"
        assert m2.currency == "INR"

    def test_money_preserves_decimal_precision(self) -> None:
        m = Money(amount="0.000001", currency="USD")
        m2 = Money.model_validate_json(m.model_dump_json())
        assert m2.amount == "0.000001"

    def test_money_rejects_invalid_decimal(self) -> None:
        with pytest.raises(ValidationError):
            Money(amount="abc", currency="USD")

    def test_money_rejects_short_currency(self) -> None:
        with pytest.raises(ValidationError):
            Money(amount="1.00", currency="US")
