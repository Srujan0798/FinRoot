from __future__ import annotations

import logging
import os
import sqlite3
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from finroot.memory.digital_twin import (
    DigitalTwin,
    DigitalTwinStore,
    InvestmentHorizon,
    RiskTolerance,
)

UTC_NOW = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)


def _make_twin(**kwargs: object) -> DigitalTwin:
    fields: dict[str, object] = {
        "user_id": "user-1",
        "name": "Test User",
        "age": 30,
        "risk_tolerance": RiskTolerance.MODERATE,
        "investment_horizon": InvestmentHorizon.MEDIUM,
        "monthly_income": 10000.0,
        "monthly_expenses": 5000.0,
        "tax_bracket_pct": 20.0,
        "created_at": UTC_NOW,
        "updated_at": UTC_NOW,
    }
    fields.update(kwargs)
    return DigitalTwin(**fields)


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------


class TestRiskTolerance:
    def test_values(self) -> None:
        assert RiskTolerance.CONSERVATIVE.value == "conservative"
        assert RiskTolerance.MODERATE.value == "moderate"
        assert RiskTolerance.AGGRESSIVE.value == "aggressive"

    def test_is_str_enum(self) -> None:
        assert RiskTolerance.CONSERVATIVE == "conservative"
        assert isinstance(RiskTolerance.CONSERVATIVE, str)


class TestInvestmentHorizon:
    def test_values(self) -> None:
        assert InvestmentHorizon.SHORT.value == "short"
        assert InvestmentHorizon.MEDIUM.value == "medium"
        assert InvestmentHorizon.LONG.value == "long"

    def test_is_str_enum(self) -> None:
        assert InvestmentHorizon.SHORT == "short"
        assert isinstance(InvestmentHorizon.SHORT, str)


# ---------------------------------------------------------------------------
# DigitalTwin model tests
# ---------------------------------------------------------------------------


class TestDigitalTwin:
    def test_minimal_valid(self) -> None:
        twin = _make_twin()
        assert twin.user_id == "user-1"
        assert twin.monthly_surplus == 5000.0

    def test_monthly_surplus_property(self) -> None:
        twin = _make_twin(monthly_income=8000.0, monthly_expenses=3000.0)
        assert twin.monthly_surplus == 5000.0

    def test_monthly_surplus_negative(self) -> None:
        twin = _make_twin(monthly_income=3000.0, monthly_expenses=5000.0)
        assert twin.monthly_surplus == -2000.0

    def test_default_risk_tolerance(self) -> None:
        twin = DigitalTwin(
            user_id="u1",
            name="A",
            age=25,
            monthly_income=5000.0,
            monthly_expenses=2000.0,
            tax_bracket_pct=10.0,
            created_at=UTC_NOW,
            updated_at=UTC_NOW,
        )
        assert twin.risk_tolerance is RiskTolerance.MODERATE

    def test_default_investment_horizon(self) -> None:
        twin = DigitalTwin(
            user_id="u1",
            name="A",
            age=25,
            monthly_income=5000.0,
            monthly_expenses=2000.0,
            tax_bracket_pct=10.0,
            created_at=UTC_NOW,
            updated_at=UTC_NOW,
        )
        assert twin.investment_horizon is InvestmentHorizon.MEDIUM

    def test_default_goals_constraints_holdings(self) -> None:
        twin = _make_twin()
        assert twin.goals == []
        assert twin.constraints == []
        assert twin.holdings == []

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            DigitalTwin(
                user_id="u1",
                name="A",
                age=25,
                monthly_income=5000.0,
                monthly_expenses=2000.0,
                tax_bracket_pct=10.0,
                created_at=UTC_NOW,
                updated_at=UTC_NOW,
                extra_field="nope",
            )

    def test_age_below_18_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_twin(age=17)

    def test_age_above_120_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_twin(age=121)

    def test_negative_monthly_income_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_twin(monthly_income=-1.0)

    def test_negative_monthly_expenses_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_twin(monthly_expenses=-1.0)

    def test_tax_bracket_above_50_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_twin(tax_bracket_pct=55.0)

    def test_tax_bracket_below_0_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_twin(tax_bracket_pct=-5.0)

    def test_rejects_naive_datetime(self) -> None:
        with pytest.raises(ValidationError):
            DigitalTwin(
                user_id="u1",
                name="A",
                age=25,
                monthly_income=5000.0,
                monthly_expenses=2000.0,
                tax_bracket_pct=10.0,
                created_at=datetime(2026, 1, 1),
                updated_at=UTC_NOW,
            )

    def test_converts_non_utc_to_utc(self) -> None:
        from datetime import timezone

        ny = timezone(timedelta(hours=-5))
        dt_ny = datetime(2026, 6, 19, 8, 0, 0, tzinfo=ny)
        twin = _make_twin(created_at=dt_ny)
        assert twin.created_at.tzinfo is UTC
        assert twin.created_at.hour == 13

    def test_expenses_sanity_warns(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.WARNING)
        _make_twin(monthly_income=5000.0, monthly_expenses=12000.0)
        assert len(caplog.records) >= 1
        assert "monthly_expenses" in caplog.text
        assert "verify data" in caplog.text

    def test_expenses_sanity_passes_without_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.WARNING)
        _make_twin(monthly_income=5000.0, monthly_expenses=10000.0)
        assert len(caplog.records) == 0

    def test_round_trip_json(self) -> None:
        twin = _make_twin(
            goals=["retire early"],
            constraints=["no crypto"],
            holdings=[{"symbol": "AAPL", "qty": 10}],
        )
        json_str = twin.model_dump_json()
        restored = DigitalTwin.model_validate_json(json_str)
        assert restored == twin
        assert restored.goals == ["retire early"]
        assert restored.holdings == [{"symbol": "AAPL", "qty": 10}]


# ---------------------------------------------------------------------------
# DigitalTwinStore tests (SQLite via temp files)
# ---------------------------------------------------------------------------


class TestDigitalTwinStore:
    @pytest.fixture
    def store(self) -> DigitalTwinStore:
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        store = DigitalTwinStore(db_path=path)
        yield store
        Path(path).unlink(missing_ok=True)
        Path(path + ".json").unlink(missing_ok=True)

    def test_save_and_load(self, store: DigitalTwinStore) -> None:
        twin = _make_twin(user_id="alice")
        store.save(twin)
        loaded = store.load("alice")
        assert loaded.user_id == "alice"
        assert loaded.name == "Test User"
        assert loaded.risk_tolerance is RiskTolerance.MODERATE

    def test_load_missing_raises_key_error(self, store: DigitalTwinStore) -> None:
        with pytest.raises(KeyError, match="not found"):
            store.load("nonexistent")

    def test_list_ids(self, store: DigitalTwinStore) -> None:
        assert store.list_ids() == []
        store.save(_make_twin(user_id="a"))
        store.save(_make_twin(user_id="b"))
        ids = store.list_ids()
        assert sorted(ids) == ["a", "b"]

    def test_delete(self, store: DigitalTwinStore) -> None:
        store.save(_make_twin(user_id="to-delete"))
        store.delete("to-delete")
        assert store.list_ids() == []
        with pytest.raises(KeyError):
            store.load("to-delete")

    def test_delete_nonexistent_does_not_raise(self, store: DigitalTwinStore) -> None:
        store.delete("ghost")
        assert store.list_ids() == []

    def test_updated_at_changes_on_resave(self, store: DigitalTwinStore) -> None:
        twin = _make_twin(user_id="u", monthly_income=5000.0)
        original_updated = twin.updated_at
        store.save(twin)
        loaded1 = store.load("u")
        assert loaded1.monthly_income == 5000.0
        twin.monthly_income = 6000.0
        store.save(twin)
        loaded2 = store.load("u")
        assert loaded2.monthly_income == 6000.0
        assert loaded2.updated_at > original_updated

    def test_save_with_holdings(self, store: DigitalTwinStore) -> None:
        twin = _make_twin(
            user_id="h-user",
            holdings=[{"symbol": "AAPL", "quantity": 10.0, "cost_basis": 150.0}],
        )
        store.save(twin)
        loaded = store.load("h-user")
        assert len(loaded.holdings) == 1
        assert loaded.holdings[0]["symbol"] == "AAPL"

    def test_persistence_across_stores(self) -> None:
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            store1 = DigitalTwinStore(db_path=path)
            store1.save(_make_twin(user_id="persist"))
            del store1
            store2 = DigitalTwinStore(db_path=path)
            loaded = store2.load("persist")
            assert loaded.user_id == "persist"
        finally:
            Path(path).unlink(missing_ok=True)
            Path(path + ".json").unlink(missing_ok=True)

    def test_empty_store_list_ids(self, store: DigitalTwinStore) -> None:
        assert store.list_ids() == []

    def test_schema_table_created(self, store: DigitalTwinStore) -> None:
        conn = sqlite3.connect(store._db_path)
        try:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            assert ("digital_twins",) in tables
        finally:
            conn.close()

    def test_round_trip_full_twin(self, store: DigitalTwinStore) -> None:
        twin = _make_twin(
            user_id="full",
            name="Full User",
            age=45,
            risk_tolerance=RiskTolerance.AGGRESSIVE,
            investment_horizon=InvestmentHorizon.LONG,
            monthly_income=20000.0,
            monthly_expenses=8000.0,
            tax_bracket_pct=30.0,
            goals=["FIRE", "buy house"],
            constraints=["no options"],
            holdings=[{"symbol": "GOOGL", "qty": 5}],
        )
        store.save(twin)
        loaded = store.load("full")
        assert loaded.model_dump() == twin.model_dump()
