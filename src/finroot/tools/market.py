"""Live market price data (yfinance) with deterministic Mock responses.

Two operating modes, selected per-instance:

* **Live** (default): lazy-imports :mod:`yfinance` and pulls recent OHLCV
  history for the symbol. On any failure (missing dependency, network error,
  empty series) raises :class:`ToolError` so the base class surfaces a loud
  failure (FM-11). We never substitute a synthetic value (FM-09/FM-11).
* **Mock**: returns a deterministic 5-point series whose ``latest_price`` is
  derived from a stable hash of the symbol. Used for offline judging,
  unit tests, and any environment without network access.

Activation: set ``FINROOT_LLM_PROVIDER=mock`` in the environment, or pass
``mock=True`` to the constructor. Explicit ``mock=True``/``False`` wins
over the env var.
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from finroot.audit.trail import AuditTrail
from finroot.tools.base import BaseTool, ToolCallError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Contract types
# ---------------------------------------------------------------------------


class MarketDataInput(BaseModel):
    """Input for :class:`MarketDataTool`.

    Mirrors ``tools.contract.md`` § MarketDataTool. ``extra="forbid"`` is
    the typo guard from the wave-1 contract (G-0a).
    """

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(
        min_length=1,
        max_length=32,
        description="Ticker, e.g. 'RELIANCE.NS' or 'AAPL'",
    )
    period: Literal["1d", "5d", "1mo", "3mo", "1y"] = Field(
        default="1d",
        description="Lookback window forwarded to yfinance.Ticker.history()",
    )


class PricePoint(BaseModel):
    """A single OHLCV bar (one trading session)."""

    model_config = ConfigDict(extra="forbid")

    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class MarketDataOutput(BaseModel):
    """Output of :class:`MarketDataTool`.

    ``source`` is the literal string ``"yfinance"`` or ``"mock"`` so
    downstream consumers (UI, critic) can tell the provenance of a number
    (FM-09: evidence required).
    """

    model_config = ConfigDict(extra="forbid")

    symbol: str
    currency: str
    prices: list[PricePoint]
    latest_price: float
    change_pct: float
    source: str  # "yfinance" | "mock"
    citation: str


class ToolError(ToolCallError):
    """Tool-level failure mode named in ``tools.contract.md`` § Universal.

    Subclassing :class:`ToolCallError` (not aliasing it) preserves
    back-compat with callers that catch the base name, while letting
    contract-aware callers catch the documented name.
    """


# ---------------------------------------------------------------------------
# Mock-mode helpers (deterministic, stable across processes)
# ---------------------------------------------------------------------------


_MOCK_NUM_POINTS = 5


def _stable_hash_int(s: str) -> int:
    """Return a stable, non-negative 32-bit int hash of ``s``.

    Python's built-in :func:`hash` is randomised per process
    (``PYTHONHASHSEED``), which would make mock prices non-deterministic
    across runs. The first 4 bytes of SHA-256 are perfectly stable on any
    platform.
    """
    digest = hashlib.sha256(s.encode("utf-8")).digest()[:4]
    return int.from_bytes(digest, byteorder="big", signed=False)


def _infer_currency(symbol: str) -> str:
    """Best-effort currency inference from common ticker suffixes.

    Only used as a fallback when yfinance's ``fast_info`` is unavailable
    (older versions, private tickers, etc.).
    """
    sym = symbol.upper()
    if sym.endswith(".NS") or sym.endswith(".BO"):
        return "INR"
    if sym.endswith(".L"):
        return "GBP"
    if sym.endswith(".TO"):
        return "CAD"
    if sym.endswith(".T"):
        return "JPY"
    return "USD"


def _build_mock_prices(symbol: str, base: float) -> list[PricePoint]:
    """Construct ``_MOCK_NUM_POINTS`` deterministic OHLCV bars ending today.

    Closes walk:  ``base-1, base+0.5, base-0.5, base+0.25, base``
    so the series is monotonically non-monotonic (tests can verify the
    shape, not just the boundary values). Volume is also derived from the
    stable symbol hash so the whole output is reproducible for a given
    symbol across processes and platforms.
    """
    h = _stable_hash_int(symbol + ":vol")
    today = datetime.now(UTC).date()
    closes = [base - 1.0, base + 0.5, base - 0.5, base + 0.25, base]
    points: list[PricePoint] = []
    for i, c in enumerate(closes):
        d = today - timedelta(days=(_MOCK_NUM_POINTS - 1 - i))
        op = round(c - 0.1, 2)
        high = round(c + 0.5, 2)
        low = round(c - 0.5, 2)
        vol = 1_000_000 + (h % 1_000_000)
        points.append(
            PricePoint(
                date=d.isoformat(),
                open=op,
                high=max(high, op),
                low=min(low, op),
                close=round(c, 2),
                volume=vol,
            )
        )
    return points


def _mock_latest_price(symbol: str) -> float:
    """The contract's mock formula: ``100.0 * hash(symbol) % 500 + 100``.

    Result lies in ``[100.0, 600.0)`` for any non-empty symbol.
    """
    return 100.0 * (_stable_hash_int(symbol) % 500) + 100.0


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------


class MarketDataTool(BaseTool[MarketDataInput, MarketDataOutput]):
    """Live OHLCV price tool. See module docstring for mode semantics."""

    name = "market_data"
    ttl_seconds = 300      # contract: market/news = 300s
    rate_per_sec = 5.0     # contract: ≤ 10 req/s per tool instance

    def __init__(
        self,
        audit: AuditTrail | None = None,
        mock: bool | None = None,
    ) -> None:
        super().__init__(audit=audit)
        if mock is None:
            mock = os.environ.get("FINROOT_LLM_PROVIDER", "").lower() == "mock"
        self._mock = bool(mock)

    # -- public helpers (test seams; not part of BaseTool contract) -------

    @property
    def mock(self) -> bool:
        """Whether this instance is in mock mode (read-only after init)."""
        return self._mock

    # -- BaseTool --------------------------------------------------------

    def _run(self, inp: MarketDataInput) -> MarketDataOutput:
        if self._mock:
            return self._run_mock(inp)
        return self._run_live(inp)

    # -- mock path -------------------------------------------------------

    def _run_mock(self, inp: MarketDataInput) -> MarketDataOutput:
        base = _mock_latest_price(inp.symbol)
        prices = _build_mock_prices(inp.symbol, base)
        latest = prices[-1].close
        first = prices[0].close
        change_pct = round((latest - first) / first * 100.0, 4) if first else 0.0
        return MarketDataOutput(
            symbol=inp.symbol,
            currency=_infer_currency(inp.symbol),
            prices=prices,
            latest_price=latest,
            change_pct=change_pct,
            source="mock",
            citation="Mock data (offline judging mode)",
        )

    # -- live path -------------------------------------------------------

    def _import_yfinance(self):
        """Lazy import. Raises :class:`ToolError` if yfinance is missing.

        Pulled out as its own method so tests can monkeypatch the import
        seam without depending on whether the real package is installed.
        """
        try:
            import yfinance as yf
        except ImportError as e:
            raise ToolError(
                "MarketDataTool live mode requires the 'yfinance' package; "
                "install with `pip install yfinance` or run with "
                "FINROOT_LLM_PROVIDER=mock."
            ) from e
        return yf

    def _run_live(self, inp: MarketDataInput) -> MarketDataOutput:
        yf = self._import_yfinance()
        try:
            ticker = yf.Ticker(inp.symbol)
            hist = ticker.history(period=inp.period, auto_adjust=False)
        except Exception as e:  # yfinance raises a zoo of low-level errors
            raise ToolError(
                f"MarketDataTool live fetch failed for symbol={inp.symbol!r}: {e}"
            ) from e
        if hist is None or len(hist) == 0:
            raise ToolError(
                f"MarketDataTool received empty history for symbol={inp.symbol!r}"
            )
        prices: list[PricePoint] = []
        for idx, row in hist.iterrows():
            prices.append(
                PricePoint(
                    date=idx.strftime("%Y-%m-%d"),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=int(row["Volume"]),
                )
            )
        latest = float(hist["Close"].iloc[-1])
        first = float(hist["Close"].iloc[0])
        change_pct = round((latest - first) / first * 100.0, 4) if first else 0.0
        currency = self._safe_currency(ticker, inp.symbol)
        return MarketDataOutput(
            symbol=inp.symbol,
            currency=currency,
            prices=prices,
            latest_price=latest,
            change_pct=change_pct,
            source="yfinance",
            citation=(
                f"Yahoo Finance via yfinance, fetched "
                f"{datetime.now(UTC).isoformat()}"
            ),
        )

    @staticmethod
    def _safe_currency(ticker, symbol: str) -> str:
        """Best-effort currency extraction; never raises."""
        try:
            fi = getattr(ticker, "fast_info", None)
            if fi is not None:
                cur = getattr(fi, "currency", None)
                if cur:
                    return str(cur)
        except Exception as e:  # pragma: no cover - defensive
            logger.debug("fast_info currency lookup failed for %s: %s", symbol, e)
        return _infer_currency(symbol)


__all__ = [
    "MarketDataInput",
    "MarketDataOutput",
    "MarketDataTool",
    "PricePoint",
    "ToolError",
]
