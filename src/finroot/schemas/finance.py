"""Finance domain value objects used by the Digital Twin and tools.

These are the typed spine the tools (W2+) and the state pipeline operate on.
All datetimes are timezone-aware UTC. All money is non-negative when used as
`quantity`; deltas (PnL) may be negative.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from finroot.schemas.enums import Domain


class Horizon(str, Enum):  # noqa: UP042  (mirrors contract enums)
    """Investment / planning horizon. Drives confidence and risk framing."""

    SHORT = "short"          # < 1 year
    MEDIUM = "medium"        # 1-5 years
    LONG = "long"            # 5-20 years
    GENERATIONAL = "generational"  # > 20 years


class Money(BaseModel):
    """A monetary amount with explicit currency.

    Uses `Decimal` to avoid float drift on currency math. `amount` is stored as
    string to survive JSON round-trips without precision loss.
    """

    model_config = ConfigDict(extra="forbid")

    amount: str = Field(min_length=1, description="Decimal amount as string, e.g. '1234.56'")
    currency: str = Field(min_length=3, max_length=3, description="ISO-4217 currency code")

    @field_validator("currency")
    @classmethod
    def _upper_currency(cls, v: str) -> str:
        return v.upper()

    @field_validator("amount")
    @classmethod
    def _valid_decimal(cls, v: str) -> str:
        from decimal import Decimal, InvalidOperation

        try:
            Decimal(v)
        except InvalidOperation as e:
            raise ValueError(f"amount must be a valid decimal string, got {v!r}") from e
        return v


class Holding(BaseModel):
    """A single position held by the user (or scenario).

    `cost_basis` is the per-unit acquisition price in `currency`; current
    market value can be derived from `quantity * market_price` at the snapshot
    timestamp.
    """

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1, max_length=32, description="Ticker or identifier")
    name: str = Field(min_length=1, description="Human-readable name")
    domain: Domain = Domain.EQUITY
    quantity: float | None = Field(default=None, ge=0, description="Units held (>= 0)")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    cost_basis: float = Field(default=0.0, ge=0, description="Per-unit acquisition price")
    market_price: float | None = Field(default=None, ge=0, description="Per-unit last price")
    market_price_as_of: datetime | None = Field(default=None)
    horizon: Horizon = Horizon.MEDIUM
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("currency")
    @classmethod
    def _upper_currency(cls, v: str) -> str:
        return v.upper()

    @field_validator("market_price_as_of")
    @classmethod
    def _utc_aware(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return v
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError("market_price_as_of must be timezone-aware (UTC)")
        return v.astimezone(tz=__import__("datetime").timezone.utc)

    @model_validator(mode="after")
    def _price_as_of_required(self) -> Holding:
        if self.market_price is not None and self.market_price_as_of is None:
            raise ValueError("market_price_as_of is required when market_price is set")
        return self

    @property
    def market_value(self) -> float | None:
        if self.market_price is None or self.quantity is None:
            return None
        return self.quantity * self.market_price

    @property
    def unrealized_pnl(self) -> float | None:
        if self.market_price is None or self.quantity is None:
            return None
        return self.quantity * (self.market_price - self.cost_basis)


class Portfolio(BaseModel):
    """A collection of holdings, the Digital Twin's primary value object.

    The twin snapshot in `AgentState.twin_snapshot` serializes one of these.
    """

    model_config = ConfigDict(extra="forbid")

    holdings: list[Holding] = Field(default_factory=list)
    base_currency: str = Field(default="USD", min_length=3, max_length=3)
    as_of: datetime = Field(default_factory=lambda: datetime.now(tz=__import__("datetime").timezone.utc))
    notes: str = ""

    @field_validator("base_currency")
    @classmethod
    def _upper_currency(cls, v: str) -> str:
        return v.upper()

    @field_validator("as_of")
    @classmethod
    def _utc_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError("as_of must be timezone-aware (UTC)")
        return v.astimezone(tz=__import__("datetime").timezone.utc)


NonEmptyStr = Annotated[str, Field(min_length=1)]


__all__ = [
    "Holding",
    "Horizon",
    "Money",
    "NonEmptyStr",
    "Portfolio",
]
