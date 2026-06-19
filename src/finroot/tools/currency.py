"""CurrencyConverterTool — FX conversion via fixed mock table or live rates.

Mock mode uses a fixed INR-anchored rate table (as of 2026-06). Live mode
queries the free public API at ``https://open.er-api.com/v6/latest/{from}``
(no key required) and derives cross-rates from the returned basket.

Cache TTL is 300s — FX rates move intraday but the free tier updates once
per business day, so five minutes is plenty.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

from pydantic import BaseModel, Field, field_validator

from finroot.tools.base import BaseTool, ToolCallError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# I/O types (contract § CurrencyConverterTool)
# ---------------------------------------------------------------------------


class CurrencyInput(BaseModel):
    """Input for CurrencyConverterTool."""

    amount: float
    from_currency: str = Field(min_length=3, max_length=3)
    to_currency: str = Field(min_length=3, max_length=3)

    model_config = {"extra": "forbid"}

    @field_validator("from_currency", "to_currency")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.upper()


class CurrencyOutput(BaseModel):
    """Output from CurrencyConverterTool."""

    converted_amount: float
    rate: float
    from_currency: str
    to_currency: str
    source: str  # "open.er-api.com" | "mock"
    citation: str


# ---------------------------------------------------------------------------
# Mock rate table (INR-anchored; rates as of 2026-06)
# ---------------------------------------------------------------------------
#
# One unit of the key currency costs this many INR. Cross-rates are derived
# by computing X → INR → Y at runtime so we only store INR legs.
# (Note: JPY/INR=0.56 means 1 JPY = 0.56 INR, which is unrealistic; this is
#  the value the task brief explicitly mandates. We honour the brief. The
#  dev/test environment uses it for fixed-rate determinism; live mode is the
#  path that gives real-world accurate rates.)

_MOCK_RATES_TO_INR: dict[str, float] = {
    "USD": 83.5,
    "EUR": 90.2,
    "GBP": 106.0,
    "JPY": 0.56,
    "AED": 22.7,
    "INR": 1.0,
}


def _mock_convert(amount: float, from_ccy: str, to_ccy: str) -> tuple[float, float]:
    """Return (converted_amount, rate) using the INR-anchored mock table."""
    from_rate = _MOCK_RATES_TO_INR.get(from_ccy)
    to_rate = _MOCK_RATES_TO_INR.get(to_ccy)
    if from_rate is None or to_rate is None:
        raise ToolCallError(
            f"CurrencyConverterTool: mock rate table has no entry for "
            f"{from_ccy!r} or {to_ccy!r}. Supported: {sorted(_MOCK_RATES_TO_INR)}"
        )
    # amount * (INR-per-from) / (INR-per-to) = amount in to
    rate = from_rate / to_rate
    return amount * rate, rate


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------


class CurrencyConverterTool(BaseTool[CurrencyInput, CurrencyOutput]):
    """Convert an amount between two currencies.

    Mock mode (default in tests / ``FINROOT_LLM_PROVIDER=mock``) uses a
    fixed INR-anchored rate table. Live mode queries open.er-api.com and
    computes the cross-rate from the returned basket.
    """

    name = "currency_converter"
    ttl_seconds = 300  # FX changes intraday; 5 min is plenty

    def __init__(self, *, mock: bool = False, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._mock = mock

    def _run(self, inp: CurrencyInput) -> CurrencyOutput:
        # Zero / same-currency shortcut (FM-11: be explicit, never invent).
        if inp.amount == 0:
            return CurrencyOutput(
                converted_amount=0.0,
                rate=1.0 if inp.from_currency == inp.to_currency else 0.0,
                from_currency=inp.from_currency,
                to_currency=inp.to_currency,
                source="identity" if inp.from_currency == inp.to_currency else "zero",
                citation="Zero amount: identity result, no rate lookup performed",
            )
        if inp.from_currency == inp.to_currency:
            return CurrencyOutput(
                converted_amount=float(inp.amount),
                rate=1.0,
                from_currency=inp.from_currency,
                to_currency=inp.to_currency,
                source="identity",
                citation="Same currency: identity conversion, rate = 1.0",
            )

        if self._mock or os.environ.get("FINROOT_LLM_PROVIDER") == "mock":
            return self._run_mock(inp)
        return self._run_live(inp)

    # ------------------------------------------------------------------ mock
    def _run_mock(self, inp: CurrencyInput) -> CurrencyOutput:
        converted, rate = _mock_convert(inp.amount, inp.from_currency, inp.to_currency)
        return CurrencyOutput(
            converted_amount=converted,
            rate=rate,
            from_currency=inp.from_currency,
            to_currency=inp.to_currency,
            source="mock",
            citation=(
                f"Mock fixed-rate table (2026-06): "
                f"1 {inp.from_currency} = {rate:.6f} {inp.to_currency}"
            ),
        )

    # ------------------------------------------------------------------ live
    def _run_live(self, inp: CurrencyInput) -> CurrencyOutput:
        url = f"https://open.er-api.com/v6/latest/{inp.from_currency}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "FinRoot/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
            raise ToolCallError(
                f"CurrencyConverterTool: open.er-api.com request failed for "
                f"{inp.from_currency}: {exc}"
            ) from exc

        if payload.get("result") != "success":
            raise ToolCallError(
                f"CurrencyConverterTool: open.er-api.com returned non-success "
                f"for {inp.from_currency}: {payload.get('result')!r}"
            )

        rates = payload.get("rates") or {}
        target = rates.get(inp.to_currency)
        if target is None:
            raise ToolCallError(
                f"CurrencyConverterTool: open.er-api.com response has no entry "
                f"for {inp.to_currency!r} (base {inp.from_currency})"
            )

        rate = float(target)
        return CurrencyOutput(
            converted_amount=float(inp.amount) * rate,
            rate=rate,
            from_currency=inp.from_currency,
            to_currency=inp.to_currency,
            source="open.er-api.com",
            citation=(
                f"Exchange rate source: open.er-api.com / "
                f"Mock fixed-rate table (2026-06). "
                f"1 {inp.from_currency} = {rate:.6f} {inp.to_currency}"
            ),
        )


__all__ = ["CurrencyConverterTool", "CurrencyInput", "CurrencyOutput"]
