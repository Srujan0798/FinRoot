"""MacroDataTool — Indian macro indicators (GDP, inflation, repo, unemployment).

Mock mode returns deterministic canned values for the default country ``IN``.
Live mode queries the World Bank public API (no key required):

    https://api.worldbank.org/v2/country/{country}/indicator/{wb_code}?format=json&mrv=1

Cache TTL is 3600s — macro indicators are slow-moving and the World Bank
endpoints update at most annually, so aggressive caching is appropriate.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from finroot.tools.base import BaseTool, ToolCallError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# I/O types (contract § MacroDataTool)
# ---------------------------------------------------------------------------

Indicator = Literal["gdp_growth", "inflation", "repo_rate", "unemployment"]


class MacroInput(BaseModel):
    """Input for MacroDataTool."""

    indicator: Indicator
    country: str = Field(default="IN", min_length=2, max_length=3)

    model_config = {"extra": "forbid"}

    @field_validator("country")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.upper()


class MacroOutput(BaseModel):
    """Output from MacroDataTool."""

    indicator: str
    country: str
    value: float
    unit: str
    period: str
    source: str  # "worldbank" | "mock"
    citation: str


# ---------------------------------------------------------------------------
# Indicator registry: name → (World Bank code, unit, period label, mock value)
# ---------------------------------------------------------------------------

_INDICATOR_TABLE: dict[str, dict[str, object]] = {
    "gdp_growth": {
        "wb_code": "NY.GDP.MKTP.KD.ZG",
        "unit": "% YoY",
        "period": "2024",
        "mock_value": 7.2,
    },
    "inflation": {
        "wb_code": "FP.CPI.TOTL.ZG",
        "unit": "% CPI YoY",
        "period": "2024",
        "mock_value": 5.1,
    },
    "repo_rate": {
        "wb_code": "FM.RBL.BMNY.ZG",  # best public World Bank proxy for monetary stance
        "unit": "%",
        "period": "Jun 2024",
        "mock_value": 6.5,
    },
    "unemployment": {
        "wb_code": "SL.UEM.TOTL.ZS",
        "unit": "%",
        "period": "2024",
        "mock_value": 7.8,
    },
}


# ---------------------------------------------------------------------------
# Mock fixtures (canonical India macro snapshot, used in mock mode)
# ---------------------------------------------------------------------------

_MOCK_VALUES: dict[str, MacroOutput] = {
    indicator: MacroOutput(
        indicator=indicator,
        country="IN",
        value=float(meta["mock_value"]),  # type: ignore[arg-type]
        unit=str(meta["unit"]),
        period=str(meta["period"]),
        source="mock",
        citation=(
            f"Mock {indicator} value for IN ({meta['unit']}, period {meta['period']})"
        ),
    )
    for indicator, meta in _INDICATOR_TABLE.items()
}


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------


class MacroDataTool(BaseTool[MacroInput, MacroOutput]):
    """Return a macro indicator for a country (default IN).

    Mock mode (default in tests / ``FINROOT_LLM_PROVIDER=mock``) returns the
    deterministic canned fixture. Live mode hits the World Bank public API.
    """

    name = "macro_data"
    ttl_seconds = 3600  # macro data is slow-moving

    def __init__(self, *, mock: bool = False, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._mock = mock

    def _run(self, inp: MacroInput) -> MacroOutput:
        if self._mock or os.environ.get("FINROOT_LLM_PROVIDER") == "mock":
            return self._run_mock(inp)
        return self._run_live(inp)

    # ------------------------------------------------------------------ mock
    def _run_mock(self, inp: MacroInput) -> MacroOutput:
        if inp.indicator not in _MOCK_VALUES:
            # Defence in depth: Literal already restricts this, but keep the
            # loud-failure contract explicit (FM-11).
            raise ToolCallError(
                f"MacroDataTool: unknown indicator {inp.indicator!r}. "
                f"Valid indicators: {sorted(_MOCK_VALUES)}"
            )
        out = _MOCK_VALUES[inp.indicator]
        if inp.country == "IN":
            return out
        # Mock table is IN-only; be honest about that.
        return MacroOutput(
            indicator=out.indicator,
            country=inp.country,
            value=out.value,
            unit=out.unit,
            period=out.period,
            source="mock",
            citation=(
                f"Mock {out.indicator} for {inp.country} "
                f"(IN fixture reused; live data not available in mock mode)"
            ),
        )

    # ------------------------------------------------------------------ live
    def _run_live(self, inp: MacroInput) -> MacroOutput:
        meta = _INDICATOR_TABLE.get(inp.indicator)
        if meta is None:  # pragma: no cover - Literal guards this
            raise ToolCallError(
                f"MacroDataTool: unknown indicator {inp.indicator!r}"
            )
        wb_code = str(meta["wb_code"])
        unit = str(meta["unit"])
        country = inp.country.upper()

        url = (
            "https://api.worldbank.org/v2/"
            f"country/{country}/indicator/{wb_code}?format=json&mrv=1"
        )

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "FinRoot/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
            raise ToolCallError(
                f"MacroDataTool: World Bank request failed for {inp.indicator} "
                f"({country}): {exc}"
            ) from exc

        try:
            data_list = payload[1]
        except (IndexError, TypeError) as exc:
            raise ToolCallError(
                f"MacroDataTool: unexpected World Bank response shape for "
                f"{inp.indicator} ({country}): {payload!r}"
            ) from exc

        if not data_list:
            raise ToolCallError(
                f"MacroDataTool: World Bank returned no data points for "
                f"{inp.indicator} ({country})"
            )

        point = data_list[0]
        value = point.get("value")
        if value is None:
            raise ToolCallError(
                f"MacroDataTool: World Bank returned null value for "
                f"{inp.indicator} ({country}); refusing to fabricate (FM-11)"
            )

        period = str(point.get("date") or meta["period"])

        return MacroOutput(
            indicator=inp.indicator,
            country=country,
            value=float(value),
            unit=unit,
            period=period,
            source="worldbank",
            citation=(
                f"World Bank indicator {wb_code} for {country}, period {period}"
            ),
        )


__all__ = ["MacroDataTool", "MacroInput", "MacroOutput"]
