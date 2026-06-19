"""Fundamental analysis ratios (yfinance) with deterministic Mock responses.

Mirrors :mod:`finroot.tools.market` in spirit: live mode lazy-imports
:mod:`yfinance` and reads ``Ticker.info``; mock mode returns the same
fixed ratios for every symbol so tests are reproducible. Per the
contract, missing fields in live mode are surfaced as ``None`` — not
errors — so a sparse ticker still produces a structured output.
"""

from __future__ import annotations

import logging
import math
import os
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from finroot.audit.trail import AuditTrail
from finroot.tools.base import BaseTool
from finroot.tools.market import ToolError  # contract name alias

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Contract types
# ---------------------------------------------------------------------------


class FundamentalInput(BaseModel):
    """Input for :class:`FundamentalAnalysisTool`."""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(
        min_length=1,
        max_length=32,
        description="Ticker, e.g. 'RELIANCE.NS' or 'AAPL'",
    )


class FundamentalOutput(BaseModel):
    """Output of :class:`FundamentalAnalysisTool`.

    Every ratio is ``float | None`` because live ``Ticker.info`` is sparse
    for many symbols (especially delisted or low-coverage tickers).
    """

    model_config = ConfigDict(extra="forbid")

    symbol: str
    pe_ratio: float | None
    pb_ratio: float | None
    eps: float | None
    dividend_yield: float | None
    market_cap: float | None
    revenue_ttm: float | None
    debt_to_equity: float | None
    source: str   # "yfinance" | "mock"
    citation: str


# ---------------------------------------------------------------------------
# Mock fixture
# ---------------------------------------------------------------------------


# Deterministic ratios returned for every symbol in mock mode. Values are
# reasonable mid-cap defaults so downstream numeric formatting (e.g. pct
# display) is exercised even when offline.
_MOCK_FUNDAMENTALS: dict[str, float] = {
    "pe_ratio": 22.5,
    "pb_ratio": 3.1,
    "eps": 10.5,
    "dividend_yield": 0.015,
    "market_cap": 1_500_000_000.0,
    "revenue_ttm": 800_000_000.0,
    "debt_to_equity": 0.6,
}


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------


class FundamentalAnalysisTool(BaseTool[FundamentalInput, FundamentalOutput]):
    """Fundamental ratios tool. See module docstring for mode semantics."""

    name = "fundamental_analysis"
    ttl_seconds = 3600   # contract: fundamentals = 3600s
    rate_per_sec = 5.0   # contract: ≤ 10 req/s per tool instance

    def __init__(
        self,
        audit: AuditTrail | None = None,
        mock: bool | None = None,
    ) -> None:
        super().__init__(audit=audit)
        if mock is None:
            mock = os.environ.get("FINROOT_LLM_PROVIDER", "").lower() == "mock"
        self._mock = bool(mock)

    # -- public helpers (test seams) -------------------------------------

    @property
    def mock(self) -> bool:
        """Whether this instance is in mock mode (read-only after init)."""
        return self._mock

    # -- BaseTool --------------------------------------------------------

    def _run(self, inp: FundamentalInput) -> FundamentalOutput:
        if self._mock:
            return self._run_mock(inp)
        return self._run_live(inp)

    # -- mock path -------------------------------------------------------

    def _run_mock(self, inp: FundamentalInput) -> FundamentalOutput:
        return FundamentalOutput(
            symbol=inp.symbol,
            **_MOCK_FUNDAMENTALS,
            source="mock",
            citation="Mock data (offline judging mode)",
        )

    # -- live path -------------------------------------------------------

    def _import_yfinance(self):
        """Lazy import. Raises :class:`ToolError` if yfinance is missing."""
        try:
            import yfinance as yf
        except ImportError as e:
            raise ToolError(
                "FundamentalAnalysisTool live mode requires the 'yfinance' "
                "package; install with `pip install yfinance` or run with "
                "FINROOT_LLM_PROVIDER=mock."
            ) from e
        return yf

    @staticmethod
    def _coerce_float(v) -> float | None:
        """Coerce a value to ``float``; return ``None`` on missing/sentinel.

        yfinance uses ``None`` for missing, and sometimes a large sentinel
        (``1e308``) for "not applicable" — both surface as ``None`` so the
        UI shows "—" instead of an obviously-wrong giant number.
        """
        if v is None:
            return None
        try:
            f = float(v)
        except (TypeError, ValueError):
            return None
        if math.isnan(f) or math.isinf(f) or abs(f) >= 1e30:
            return None
        return f

    def _run_live(self, inp: FundamentalInput) -> FundamentalOutput:
        yf = self._import_yfinance()
        try:
            ticker = yf.Ticker(inp.symbol)
            info = ticker.info
        except Exception as e:
            raise ToolError(
                f"FundamentalAnalysisTool live fetch failed for "
                f"symbol={inp.symbol!r}: {e}"
            ) from e
        if not info:
            raise ToolError(
                f"FundamentalAnalysisTool received empty info for "
                f"symbol={inp.symbol!r}"
            )
        return FundamentalOutput(
            symbol=inp.symbol,
            pe_ratio=self._coerce_float(info.get("trailingPE")),
            pb_ratio=self._coerce_float(info.get("priceToBook")),
            eps=self._coerce_float(info.get("trailingEps")),
            dividend_yield=self._coerce_float(info.get("dividendYield")),
            market_cap=self._coerce_float(info.get("marketCap")),
            revenue_ttm=self._coerce_float(info.get("totalRevenue")),
            debt_to_equity=self._coerce_float(info.get("debtToEquity")),
            source="yfinance",
            citation=(
                f"Yahoo Finance via yfinance, fetched "
                f"{datetime.now(UTC).isoformat()}"
            ),
        )


__all__ = [
    "FundamentalAnalysisTool",
    "FundamentalInput",
    "FundamentalOutput",
]
