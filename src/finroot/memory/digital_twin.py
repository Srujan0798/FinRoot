from __future__ import annotations

import json
import logging
import sqlite3
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


class RiskTolerance(str, Enum):  # noqa: UP042  (contract: str, Enum)
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class InvestmentHorizon(str, Enum):  # noqa: UP042  (contract: str, Enum)
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class DigitalTwin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str
    name: str
    age: int = Field(ge=18, le=120)
    risk_tolerance: RiskTolerance = RiskTolerance.MODERATE
    investment_horizon: InvestmentHorizon = InvestmentHorizon.MEDIUM
    monthly_income: float = Field(ge=0)
    monthly_expenses: float = Field(ge=0)
    tax_bracket_pct: float = Field(ge=0, le=50)
    goals: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    holdings: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at")
    @classmethod
    def _utc_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError(f"{v} must be timezone-aware (UTC)")
        return v.astimezone(UTC)

    @model_validator(mode="after")
    def _expenses_sanity(self) -> DigitalTwin:
        if self.monthly_expenses > self.monthly_income * 2:
            logger.warning(
                "monthly_expenses (%.2f) > 2× monthly_income (%.2f) for user %s "
                "— verify data",
                self.monthly_expenses,
                self.monthly_income,
                self.user_id,
            )
        return self

    @property
    def monthly_surplus(self) -> float:
        return self.monthly_income - self.monthly_expenses


_SCHEMA_SQL = """CREATE TABLE IF NOT EXISTS digital_twins (
    user_id           TEXT PRIMARY KEY,
    name              TEXT NOT NULL,
    age               INTEGER NOT NULL,
    risk_tolerance    TEXT NOT NULL DEFAULT 'moderate',
    investment_horizon TEXT NOT NULL DEFAULT 'medium',
    monthly_income    REAL NOT NULL DEFAULT 0,
    monthly_expenses  REAL NOT NULL DEFAULT 0,
    tax_bracket_pct   REAL NOT NULL DEFAULT 0,
    goals             TEXT NOT NULL DEFAULT '[]',
    constraints       TEXT NOT NULL DEFAULT '[]',
    holdings          TEXT NOT NULL DEFAULT '[]',
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);"""


def _load_schema_sql() -> str:
    schema_path = Path(__file__).resolve().parents[3] / "schema" / "db_struct.sql"
    if schema_path.exists():
        return schema_path.read_text()
    return _SCHEMA_SQL


class DigitalTwinStore:
    def __init__(self, db_path: str = "data/digital_twin.db") -> None:
        self._db_path = db_path
        self._fallback_path = f"{db_path}.json"
        self._use_sqlite = True
        self._init_db()

    def _init_db(self) -> None:
        try:
            conn = sqlite3.connect(self._db_path)
            conn.executescript(_load_schema_sql())
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.warning("SQLite unavailable (%s) — falling back to JSON", exc)
            self._use_sqlite = False

    def save(self, twin: DigitalTwin) -> None:
        twin.updated_at = datetime.now(UTC)
        if self._use_sqlite:
            self._save_sqlite(twin)
        else:
            self._save_json(twin)

    def _save_sqlite(self, twin: DigitalTwin) -> None:
        conn = sqlite3.connect(self._db_path)
        try:
            conn.execute(
                """INSERT OR REPLACE INTO digital_twins
                   (user_id, name, age, risk_tolerance, investment_horizon,
                    monthly_income, monthly_expenses, tax_bracket_pct,
                    goals, constraints, holdings, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    twin.user_id,
                    twin.name,
                    twin.age,
                    twin.risk_tolerance.value,
                    twin.investment_horizon.value,
                    twin.monthly_income,
                    twin.monthly_expenses,
                    twin.tax_bracket_pct,
                    json.dumps(twin.goals),
                    json.dumps(twin.constraints),
                    json.dumps(twin.holdings),
                    twin.created_at.isoformat(),
                    twin.updated_at.isoformat(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def _save_json(self, twin: DigitalTwin) -> None:
        path = Path(self._fallback_path)
        data: dict[str, Any] = {}
        if path.exists():
            data = json.loads(path.read_text())
        data[twin.user_id] = twin.model_dump(mode="json")
        path.write_text(json.dumps(data, indent=2, default=str))

    def load(self, user_id: str) -> DigitalTwin:
        if self._use_sqlite:
            return self._load_sqlite(user_id)
        return self._load_json(user_id)

    def _load_sqlite(self, user_id: str) -> DigitalTwin:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT * FROM digital_twins WHERE user_id = ?", (user_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"Digital twin not found for user_id: {user_id}")
            return self._row_to_twin(dict(row))
        finally:
            conn.close()

    @staticmethod
    def _row_to_twin(data: dict[str, Any]) -> DigitalTwin:
        return DigitalTwin(
            user_id=data["user_id"],
            name=data["name"],
            age=data["age"],
            risk_tolerance=RiskTolerance(data["risk_tolerance"]),
            investment_horizon=InvestmentHorizon(data["investment_horizon"]),
            monthly_income=data["monthly_income"],
            monthly_expenses=data["monthly_expenses"],
            tax_bracket_pct=data["tax_bracket_pct"],
            goals=json.loads(data["goals"]),
            constraints=json.loads(data["constraints"]),
            holdings=json.loads(data["holdings"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    def _load_json(self, user_id: str) -> DigitalTwin:
        path = Path(self._fallback_path)
        if not path.exists():
            raise KeyError(f"Digital twin not found for user_id: {user_id}")
        data = json.loads(path.read_text())
        if user_id not in data:
            raise KeyError(f"Digital twin not found for user_id: {user_id}")
        return DigitalTwin.model_validate(data[user_id])

    def list_ids(self) -> list[str]:
        if self._use_sqlite:
            conn = sqlite3.connect(self._db_path)
            try:
                rows = conn.execute("SELECT user_id FROM digital_twins").fetchall()
                return [r[0] for r in rows]
            finally:
                conn.close()
        path = Path(self._fallback_path)
        if not path.exists():
            return []
        return list(json.loads(path.read_text()).keys())

    def delete(self, user_id: str) -> None:
        if self._use_sqlite:
            conn = sqlite3.connect(self._db_path)
            try:
                conn.execute(
                    "DELETE FROM digital_twins WHERE user_id = ?", (user_id,)
                )
                conn.commit()
            finally:
                conn.close()
        else:
            path = Path(self._fallback_path)
            if not path.exists():
                return
            data = json.loads(path.read_text())
            data.pop(user_id, None)
            path.write_text(json.dumps(data, indent=2, default=str))


__all__ = [
    "DigitalTwin",
    "DigitalTwinStore",
    "InvestmentHorizon",
    "RiskTolerance",
]
