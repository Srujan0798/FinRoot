"""Tests for MarketDataTool + FundamentalAnalysisTool (wave-3, task 01).

Covers the contract in ``.specify/specs/wave-3/contracts/tools.contract.md``:

* mock mode shape + citation + determinism
* input validation (empty symbol, invalid period)
* TTL cache (hit on second call, distinct keys per input)
* audit emission (one event per ``__call__``)
* rate limiter (no raise under 10 req/s)
* live mode: loud failure (ToolError) when yfinance is missing
* live mode: missing fields surface as ``None`` (not error)
* currency inference for the common ticker suffixes
* TTL values match the contract (market=300, fundamentals=3600)
"""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import mkdtemp

import pytest
from pydantic import ValidationError

from finroot.audit import AuditTrail
from finroot.tools.base import ToolCallError
from finroot.tools.fundamentals import (
    FundamentalAnalysisTool,
    FundamentalInput,
    FundamentalOutput,
)
from finroot.tools.market import (
    MarketDataInput,
    MarketDataOutput,
    MarketDataTool,
    PricePoint,
    ToolError,
)


# ---------------------------------------------------------------------------
# Counter subclasses (test seams — verify the base-class cache layer)
# ---------------------------------------------------------------------------


class _CountingMarketTool(MarketDataTool):
    """Count how many times ``_run`` is actually invoked (cache misses)."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.run_count = 0

    def _run(self, inp: MarketDataInput) -> MarketDataOutput:
        self.run_count += 1
        return super()._run(inp)


class _CountingFundamentalTool(FundamentalAnalysisTool):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.run_count = 0

    def _run(self, inp: FundamentalInput) -> FundamentalOutput:
        self.run_count += 1
        return super()._run(inp)


def _fast_tool(tool) -> None:
    """Disable retries/backoff so tests don't sleep."""
    tool.max_retries = 0
    tool.base_delay = 0.0


# ===========================================================================
# MarketDataTool — mock mode
# ===========================================================================


class TestMarketDataToolMock:
    def test_returns_market_data_output(self) -> None:
        tool = MarketDataTool(mock=True)
        out = tool(MarketDataInput(symbol="AAPL"))
        assert isinstance(out, MarketDataOutput)
        assert out.symbol == "AAPL"
        assert out.source == "mock"

    def test_citation_is_offline_judging(self) -> None:
        tool = MarketDataTool(mock=True)
        out = tool(MarketDataInput(symbol="AAPL"))
        assert out.citation == "Mock data (offline judging mode)"

    def test_returns_exactly_5_price_points(self) -> None:
        tool = MarketDataTool(mock=True)
        out = tool(MarketDataInput(symbol="AAPL"))
        assert len(out.prices) == 5
        for p in out.prices:
            assert isinstance(p, PricePoint)
            assert p.high >= p.low
            assert p.volume > 0

    def test_latest_price_matches_contract_formula(self) -> None:
        """``latest_price == 100.0 * stable_hash(symbol) % 500 + 100``."""
        from finroot.tools.market import _stable_hash_int

        tool = MarketDataTool(mock=True)
        out = tool(MarketDataInput(symbol="RELIANCE.NS"))
        expected = 100.0 * (_stable_hash_int("RELIANCE.NS") % 500) + 100.0
        # Mock closes end at the base; latest is the last point's close.
        assert out.latest_price == pytest.approx(expected, rel=1e-9)
        # The latest price point's close must equal the reported latest_price.
        assert out.prices[-1].close == pytest.approx(out.latest_price, rel=1e-9)

    def test_different_symbols_produce_different_prices(self) -> None:
        """Mock is hash-derived, so two symbols → two distinct outputs."""
        tool = MarketDataTool(mock=True)
        a = tool(MarketDataInput(symbol="AAPL"))
        b = tool(MarketDataInput(symbol="MSFT"))
        assert a.latest_price != b.latest_price

    def test_period_is_ignored_in_mock_mode(self) -> None:
        """All four supported periods must return the same mock data."""
        tool = MarketDataTool(mock=True)
        first = tool(MarketDataInput(symbol="AAPL", period="1d"))
        for p in ("5d", "1mo", "3mo", "1y"):
            again = tool(MarketDataInput(symbol="AAPL", period=p))
            assert again.latest_price == first.latest_price
            assert [pt.close for pt in again.prices] == [
                pt.close for pt in first.prices
            ]

    def test_currency_inference_for_ns_symbols(self) -> None:
        tool = MarketDataTool(mock=True)
        assert tool(MarketDataInput(symbol="RELIANCE.NS")).currency == "INR"
        assert tool(MarketDataInput(symbol="TCS.BO")).currency == "INR"
        assert tool(MarketDataInput(symbol="AAPL")).currency == "USD"
        assert tool(MarketDataInput(symbol="HSBC.L")).currency == "GBP"

    def test_change_pct_is_finite_float(self) -> None:
        tool = MarketDataTool(mock=True)
        out = tool(MarketDataInput(symbol="AAPL"))
        assert isinstance(out.change_pct, float)
        # First close is non-zero (base >= 100) → no division-by-zero.
        assert -100.0 <= out.change_pct <= 100.0

    def test_mock_mode_default_via_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``FINROOT_LLM_PROVIDER=mock`` activates mock mode without args."""
        monkeypatch.setenv("FINROOT_LLM_PROVIDER", "mock")
        tool = MarketDataTool()
        assert tool.mock is True
        assert tool(MarketDataInput(symbol="AAPL")).source == "mock"


# ===========================================================================
# MarketDataTool — input validation
# ===========================================================================


class TestMarketDataToolInputValidation:
    def test_empty_symbol_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            MarketDataInput(symbol="")

    def test_missing_symbol_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            MarketDataInput()  # type: ignore[call-arg]

    def test_invalid_period_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            MarketDataInput(symbol="AAPL", period="10y")  # type: ignore[arg-type]

    def test_extra_field_raises_validation_error(self) -> None:
        """``extra="forbid"`` is the wave-1 typo guard (G-0a)."""
        with pytest.raises(ValidationError):
            MarketDataInput(symbol="AAPL", bogus="x")  # type: ignore[call-arg]


# ===========================================================================
# MarketDataTool — TTL cache
# ===========================================================================


class TestMarketDataToolCache:
    def test_cache_hit_on_second_call(self) -> None:
        tool = _CountingMarketTool(mock=True)
        inp = MarketDataInput(symbol="AAPL")
        r1 = tool(inp)
        r2 = tool(inp)
        assert r1 is r2                   # object identity → cache hit
        assert tool.run_count == 1        # underlying fetch only once

    def test_different_symbols_have_distinct_caches(self) -> None:
        tool = _CountingMarketTool(mock=True)
        tool(MarketDataInput(symbol="AAPL"))
        tool(MarketDataInput(symbol="MSFT"))
        tool(MarketDataInput(symbol="AAPL"))  # cached, no extra fetch
        assert tool.run_count == 2

    def test_ttl_is_300_per_contract(self) -> None:
        assert MarketDataTool.ttl_seconds == 300
        assert MarketDataTool(mock=True).ttl_seconds == 300


# ===========================================================================
# MarketDataTool — audit emission
# ===========================================================================


class TestMarketDataToolAudit:
    def test_audit_event_emitted_on_call(self) -> None:
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        tool = MarketDataTool(audit=audit, mock=True)
        tool(MarketDataInput(symbol="AAPL"))
        events = audit.replay()
        assert len(events) == 1
        assert events[0].type == "tool.called"
        assert events[0].payload["tool"] == "market_data"

    def test_no_audit_event_when_trail_omitted(self) -> None:
        tool = MarketDataTool(mock=True)
        out = tool(MarketDataInput(symbol="AAPL"))
        assert out.symbol == "AAPL"  # runs cleanly with no audit


# ===========================================================================
# MarketDataTool — rate limiter
# ===========================================================================


class TestMarketDataToolRateLimit:
    def test_no_raise_under_10_req_per_sec(self) -> None:
        """With rate_per_sec=20, 5 quick calls must not raise or block."""
        tool = MarketDataTool(mock=True)
        tool.rate_per_sec = 20.0
        for _ in range(5):
            out = tool(MarketDataInput(symbol="AAPL"))
            assert isinstance(out, MarketDataOutput)


# ===========================================================================
# MarketDataTool — live mode failure semantics
# ===========================================================================


class TestMarketDataToolLive:
    def test_yfinance_unavailable_raises_tool_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If yfinance cannot be imported, live mode must fail loud (FM-11)."""

        def _fail_import(self):  # noqa: ANN001 - monkeypatch seam
            raise ToolError("yfinance is not installed (test stub)")

        monkeypatch.setattr(MarketDataTool, "_import_yfinance", _fail_import)
        tool = MarketDataTool(mock=False)
        _fast_tool(tool)
        with pytest.raises((ToolCallError, ToolError)):
            tool(MarketDataInput(symbol="AAPL"))

    def test_live_network_error_maps_to_tool_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Any yfinance-side error must be wrapped as a ToolError (no silent fallback)."""

        class _BrokenTicker:
            def history(self, **_kwargs):  # noqa: ANN003
                raise RuntimeError("network down")

        def _fake_yf(self):  # noqa: ANN001 - monkeypatch seam
            class _Mod:
                Ticker = _BrokenTicker
            return _Mod

        monkeypatch.setattr(MarketDataTool, "_import_yfinance", _fake_yf)
        tool = MarketDataTool(mock=False)
        _fast_tool(tool)
        with pytest.raises((ToolCallError, ToolError)):
            tool(MarketDataInput(symbol="AAPL"))


# ===========================================================================
# FundamentalAnalysisTool — mock mode
# ===========================================================================


class TestFundamentalAnalysisToolMock:
    def test_returns_fundamental_output(self) -> None:
        tool = FundamentalAnalysisTool(mock=True)
        out = tool(FundamentalInput(symbol="AAPL"))
        assert isinstance(out, FundamentalOutput)
        assert out.symbol == "AAPL"
        assert out.source == "mock"

    def test_citation_is_offline_judging(self) -> None:
        tool = FundamentalAnalysisTool(mock=True)
        assert tool(FundamentalInput(symbol="AAPL")).citation == (
            "Mock data (offline judging mode)"
        )

    def test_ratios_match_contract_values(self) -> None:
        """Mock must return the exact contract values, regardless of symbol."""
        tool = FundamentalAnalysisTool(mock=True)
        for sym in ("AAPL", "RELIANCE.NS", "TCS.BO", "A", "ZZZZ"):
            out = tool(FundamentalInput(symbol=sym))
            assert out.pe_ratio == 22.5
            assert out.pb_ratio == 3.1
            assert out.eps == 10.5
            assert out.dividend_yield == 0.015
            assert out.market_cap == 1_500_000_000.0
            assert out.revenue_ttm == 800_000_000.0
            assert out.debt_to_equity == 0.6

    def test_all_fields_are_floats_in_mock(self) -> None:
        tool = FundamentalAnalysisTool(mock=True)
        out = tool(FundamentalInput(symbol="AAPL"))
        for fld in (
            "pe_ratio", "pb_ratio", "eps", "dividend_yield",
            "market_cap", "revenue_ttm", "debt_to_equity",
        ):
            assert isinstance(getattr(out, fld), float), fld

    def test_mock_mode_default_via_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FINROOT_LLM_PROVIDER", "mock")
        tool = FundamentalAnalysisTool()
        assert tool.mock is True
        assert tool(FundamentalInput(symbol="AAPL")).pe_ratio == 22.5


# ===========================================================================
# FundamentalAnalysisTool — input validation
# ===========================================================================


class TestFundamentalAnalysisToolInputValidation:
    def test_empty_symbol_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            FundamentalInput(symbol="")

    def test_extra_field_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            FundamentalInput(symbol="AAPL", foo=1)  # type: ignore[call-arg]


# ===========================================================================
# FundamentalAnalysisTool — TTL cache + audit
# ===========================================================================


class TestFundamentalAnalysisToolCacheAndAudit:
    def test_cache_hit_on_second_call(self) -> None:
        tool = _CountingFundamentalTool(mock=True)
        inp = FundamentalInput(symbol="AAPL")
        r1 = tool(inp)
        r2 = tool(inp)
        assert r1 is r2
        assert tool.run_count == 1

    def test_ttl_is_3600_per_contract(self) -> None:
        assert FundamentalAnalysisTool.ttl_seconds == 3600

    def test_audit_event_emitted_on_call(self) -> None:
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        tool = FundamentalAnalysisTool(audit=audit, mock=True)
        tool(FundamentalInput(symbol="AAPL"))
        events = audit.replay()
        assert len(events) == 1
        assert events[0].type == "tool.called"
        assert events[0].payload["tool"] == "fundamental_analysis"


# ===========================================================================
# FundamentalAnalysisTool — live mode semantics
# ===========================================================================


class TestFundamentalAnalysisToolLive:
    def test_yfinance_unavailable_raises_tool_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _fail_import(self):  # noqa: ANN001 - monkeypatch seam
            raise ToolError("yfinance is not installed (test stub)")

        monkeypatch.setattr(
            FundamentalAnalysisTool, "_import_yfinance", _fail_import
        )
        tool = FundamentalAnalysisTool(mock=False)
        _fast_tool(tool)
        with pytest.raises((ToolCallError, ToolError)):
            tool(FundamentalInput(symbol="AAPL"))

    def test_live_missing_fields_surface_as_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A sparse ``Ticker.info`` must NOT raise; missing fields → None."""

        class _SparseTicker:
            info: dict[str, object] = {
                "trailingPE": 25.0,
                "priceToBook": 5.0,
                # everything else missing
            }

        def _fake_yf(self):  # noqa: ANN001 - monkeypatch seam
            class _Mod:
                Ticker = lambda _symbol: _SparseTicker()
            return _Mod

        monkeypatch.setattr(
            FundamentalAnalysisTool, "_import_yfinance", _fake_yf
        )
        tool = FundamentalAnalysisTool(mock=False)
        _fast_tool(tool)
        out = tool(FundamentalInput(symbol="AAPL"))
        assert out.source == "yfinance"
        assert out.pe_ratio == 25.0
        assert out.pb_ratio == 5.0
        assert out.eps is None
        assert out.dividend_yield is None
        assert out.market_cap is None
        assert out.revenue_ttm is None
        assert out.debt_to_equity is None

    def test_live_sentinel_values_surface_as_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """yfinance uses ``1e308`` as a "not applicable" sentinel — treat as None."""

        class _SentinelTicker:
            info: dict[str, object] = {
                "trailingPE": 1e308,
                "priceToBook": float("nan"),
            }

        def _fake_yf(self):  # noqa: ANN001 - monkeypatch seam
            class _Mod:
                Ticker = lambda _symbol: _SentinelTicker()
            return _Mod

        monkeypatch.setattr(
            FundamentalAnalysisTool, "_import_yfinance", _fake_yf
        )
        tool = FundamentalAnalysisTool(mock=False)
        _fast_tool(tool)
        out = tool(FundamentalInput(symbol="AAPL"))
        assert out.pe_ratio is None
        assert out.pb_ratio is None
