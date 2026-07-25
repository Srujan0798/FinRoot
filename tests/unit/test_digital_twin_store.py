"""Tests for DigitalTwinStore — SQLite persistence layer."""

from __future__ import annotations

import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path

import pytest

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
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_db(tmp_path: Path) -> str:
    """Return a temp SQLite path that gets cleaned up."""
    return str(tmp_path / "test_twin.db")


@pytest.fixture()
def store(tmp_db: str) -> DigitalTwinStore:
    return DigitalTwinStore(db_path=tmp_db)


# ---------------------------------------------------------------------------
# Store init creates DB
# ---------------------------------------------------------------------------


@pytest.mark.wave1
def test_store_init_creates_db(tmp_path: Path) -> None:
    db_path = str(tmp_path / "new.db")
    DigitalTwinStore(db_path=db_path)
    assert Path(db_path).exists()
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = {r[0] for r in rows}
        assert "digital_twins" in table_names
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Save and load round-trip
# ---------------------------------------------------------------------------


@pytest.mark.wave1
def test_store_save_load_profile(store: DigitalTwinStore) -> None:
    twin = _make_twin(
        user_id="alice",
        name="Alice Smith",
        age=35,
        risk_tolerance=RiskTolerance.AGGRESSIVE,
        investment_horizon=InvestmentHorizon.LONG,
        monthly_income=12000.0,
        monthly_expenses=6000.0,
        tax_bracket_pct=25.0,
        goals=["retire early", "buy house"],
        constraints=["no crypto"],
        holdings=[{"symbol": "AAPL", "qty": 10}],
    )
    store.save(twin)
    loaded = store.load("alice")
    assert loaded.user_id == "alice"
    assert loaded.name == "Alice Smith"
    assert loaded.age == 35
    assert loaded.risk_tolerance is RiskTolerance.AGGRESSIVE
    assert loaded.investment_horizon is InvestmentHorizon.LONG
    assert loaded.monthly_income == 12000.0
    assert loaded.monthly_expenses == 6000.0
    assert loaded.tax_bracket_pct == 25.0
    assert loaded.goals == ["retire early", "buy house"]
    assert loaded.constraints == ["no crypto"]
    assert loaded.holdings == [{"symbol": "AAPL", "qty": 10}]


# ---------------------------------------------------------------------------
# List profiles
# ---------------------------------------------------------------------------


@pytest.mark.wave1
def test_store_list_profiles(store: DigitalTwinStore) -> None:
    assert store.list_ids() == []
    store.save(_make_twin(user_id="a"))
    store.save(_make_twin(user_id="b"))
    store.save(_make_twin(user_id="c"))
    ids = store.list_ids()
    assert sorted(ids) == ["a", "b", "c"]
    assert len(ids) == 3


# ---------------------------------------------------------------------------
# Delete profile
# ---------------------------------------------------------------------------


@pytest.mark.wave1
def test_store_delete_profile(store: DigitalTwinStore) -> None:
    store.save(_make_twin(user_id="to-delete"))
    store.save(_make_twin(user_id="to-keep"))
    store.delete("to-delete")
    remaining = store.list_ids()
    assert "to-delete" not in remaining
    assert "to-keep" in remaining
    with pytest.raises(KeyError):
        store.load("to-delete")


# ---------------------------------------------------------------------------
# Non-existent profile returns KeyError
# ---------------------------------------------------------------------------


@pytest.mark.wave1
def test_store_nonexistent_profile(store: DigitalTwinStore) -> None:
    with pytest.raises(KeyError, match="not found"):
        store.load("does-not-exist")


# ---------------------------------------------------------------------------
# Concurrent writes
# ---------------------------------------------------------------------------


@pytest.mark.wave1
def test_store_concurrent_writes(tmp_path: Path) -> None:
    db_path = str(tmp_path / "concurrent.db")
    store = DigitalTwinStore(db_path=db_path)

    errors: list[Exception] = []

    def writer(user_id: str) -> None:
        try:
            twin = _make_twin(
                user_id=user_id,
                name=f"User {user_id}",
                age=30,
                monthly_income=10000.0,
                monthly_expenses=5000.0,
                tax_bracket_pct=20.0,
            )
            store.save(twin)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=writer, args=(f"user-{i}",)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    ids = store.list_ids()
    assert len(ids) == 10
    for i in range(10):
        assert f"user-{i}" in ids
