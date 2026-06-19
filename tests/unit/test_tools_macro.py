"""Tests for MacroDataTool + CurrencyConverterTool (wave-3, task 05).

Covers:
* Mock mode returns the canonical canned values.
* Literal indicator / currency code is enforced (Pydantic ``extra='forbid'``
  + ``Literal``).
* Unknown indicator → ``ToolCallError`` (FM-11).
* Cross-rate computation via the INR-anchored mock table.
* Zero amount handled (no error, no network call).
* Same-currency conversion is an identity.
* Cache TTL matches the contract (macro 3600, currency 300).
* Mock mode can be activated via ``FINROOT_LLM_PROVIDER=mock`` env var.
* Live mode is reached with the env var unset + ``mock=False``; we stub
  ``urllib.request.urlopen`` so tests do not depend on network.
"""

from __future__ import annotations

import json
import urllib.error
from unittest import mock

import pytest
from pydantic import ValidationError

from finroot.tools.base import ToolCallError
from finroot.tools.currency import (
    CurrencyConverterTool,
    CurrencyInput,
    CurrencyOutput,
)
from finroot.tools.macro import (
    MacroDataTool,
    MacroInput,
    MacroOutput,
)

# ---------------------------------------------------------------------------
# MacroDataTool — mock mode
# ---------------------------------------------------------------------------


class TestMacroMock:
    def test_gdp_growth_in(self) -> None:
        tool = MacroDataTool(mock=True)
        out = tool(MacroInput(indicator="gdp_growth"))
        assert isinstance(out, MacroOutput)
        assert out.indicator == "gdp_growth"
        assert out.country == "IN"
        assert out.value == 7.2
        assert out.unit == "% YoY"
        assert out.period == "2024"
        assert out.source == "mock"
        assert "gdp_growth" in out.citation

    def test_inflation_in(self) -> None:
        tool = MacroDataTool(mock=True)
        out = tool(MacroInput(indicator="inflation"))
        assert out.value == 5.1
        assert out.unit == "% CPI YoY"
        assert out.period == "2024"

    def test_repo_rate_in(self) -> None:
        tool = MacroDataTool(mock=True)
        out = tool(MacroInput(indicator="repo_rate"))
        assert out.value == 6.5
        assert out.unit == "%"
        assert out.period == "Jun 2024"

    def test_unemployment_in(self) -> None:
        tool = MacroDataTool(mock=True)
        out = tool(MacroInput(indicator="unemployment"))
        assert out.value == 7.8
        assert out.unit == "%"
        assert out.period == "2024"

    def test_default_country_is_in(self) -> None:
        tool = MacroDataTool(mock=True)
        out = tool(MacroInput(indicator="gdp_growth"))
        assert out.country == "IN"

    def test_explicit_country_in(self) -> None:
        tool = MacroDataTool(mock=True)
        out = tool(MacroInput(indicator="gdp_growth", country="IN"))
        assert out.country == "IN"

    def test_country_normalised_to_upper(self) -> None:
        tool = MacroDataTool(mock=True)
        out = tool(MacroInput(indicator="gdp_growth", country="in"))
        assert out.country == "IN"

    def test_unknown_indicator_rejected_by_literal(self) -> None:
        # Pydantic Literal guard at the boundary (FM-11).
        with pytest.raises(ValidationError):
            MacroInput(indicator="not_a_real_indicator")  # type: ignore[arg-type]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            MacroInput(indicator="gdp_growth", bogus="x")  # type: ignore[call-arg]

    def test_cache_ttl_macro(self) -> None:
        tool = MacroDataTool(mock=True)
        assert tool.ttl_seconds == 3600

    def test_mock_mode_via_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # If FINROOT_LLM_PROVIDER=mock is set and mock=False is not passed,
        # the tool must still take the mock path (contract §4).
        monkeypatch.setenv("FINROOT_LLM_PROVIDER", "mock")
        tool = MacroDataTool()  # mock=False
        out = tool(MacroInput(indicator="inflation"))
        assert out.source == "mock"
        assert out.value == 5.1


# ---------------------------------------------------------------------------
# MacroDataTool — live mode (HTTP stubbed, no network)
# ---------------------------------------------------------------------------


class TestMacroLive:
    def _payload(self, value: float, date: str = "2024") -> bytes:
        return json.dumps(
            [
                {"page": 1, "pages": 1, "per_page": "50", "total": 1},
                [
                    {
                        "indicator": {"id": "NY.GDP.MKTP.KD.ZG", "value": "GDP growth (annual %)"},
                        "country": {"id": "IN", "value": "India"},
                        "countryiso3code": "IND",
                        "date": date,
                        "value": value,
                    }
                ],
            ]
        ).encode("utf-8")

    def test_live_success(self) -> None:
        tool = MacroDataTool(mock=False)
        with mock.patch("urllib.request.urlopen") as u:
            u.return_value.__enter__.return_value.read.return_value = self._payload(6.49)
            out = tool(MacroInput(indicator="gdp_growth"))
        assert out.source == "worldbank"
        assert out.value == 6.49
        assert out.period == "2024"
        assert out.unit == "% YoY"
        assert "World Bank" in out.citation

    def test_live_network_failure_raises_loud(self) -> None:
        tool = MacroDataTool(mock=False)
        tool.base_delay = 0.001  # fast tests; retry tested separately
        tool.max_retries = 0
        with mock.patch("urllib.request.urlopen") as u:
            u.side_effect = urllib.error.URLError("dns down")
            with pytest.raises(ToolCallError) as exc:
                tool(MacroInput(indicator="gdp_growth"))
        assert "World Bank" in str(exc.value)
        assert "dns down" in str(exc.value)

    def test_live_null_value_raises_loud(self) -> None:
        # FM-11: refuse to fabricate a macro number when the API returns null.
        payload = json.dumps(
            [
                {"page": 1, "pages": 1, "per_page": "50", "total": 1},
                [
                    {
                        "indicator": {"id": "x", "value": "x"},
                        "country": {"id": "IN", "value": "India"},
                        "countryiso3code": "IND",
                        "date": "2024",
                        "value": None,
                    }
                ],
            ]
        ).encode("utf-8")
        tool = MacroDataTool(mock=False)
        tool.base_delay = 0.001
        tool.max_retries = 0
        with mock.patch("urllib.request.urlopen") as u:
            u.return_value.__enter__.return_value.read.return_value = payload
            with pytest.raises(ToolCallError) as exc:
                tool(MacroInput(indicator="gdp_growth"))
        assert "null value" in str(exc.value)

    def test_live_unexpected_shape_raises_loud(self) -> None:
        tool = MacroDataTool(mock=False)
        tool.base_delay = 0.001
        tool.max_retries = 0
        with mock.patch("urllib.request.urlopen") as u:
            u.return_value.__enter__.return_value.read.return_value = b"not a json array"
            with pytest.raises(ToolCallError):
                tool(MacroInput(indicator="gdp_growth"))


# ---------------------------------------------------------------------------
# CurrencyConverterTool — mock mode
# ---------------------------------------------------------------------------


class TestCurrencyMock:
    def test_usd_to_inr(self) -> None:
        tool = CurrencyConverterTool(mock=True)
        out = tool(CurrencyInput(amount=10.0, from_currency="USD", to_currency="INR"))
        assert isinstance(out, CurrencyOutput)
        assert out.converted_amount == pytest.approx(835.0)
        assert out.rate == pytest.approx(83.5)
        assert out.from_currency == "USD"
        assert out.to_currency == "INR"
        assert out.source == "mock"

    def test_eur_to_usd_via_inr_cross_rate(self) -> None:
        # Cross-rate via INR: EUR/INR ÷ USD/INR = 90.2 / 83.5
        tool = CurrencyConverterTool(mock=True)
        out = tool(CurrencyInput(amount=100.0, from_currency="EUR", to_currency="USD"))
        expected_rate = 90.2 / 83.5
        assert out.rate == pytest.approx(expected_rate, rel=1e-9)
        assert out.converted_amount == pytest.approx(100.0 * expected_rate, rel=1e-9)

    def test_inr_to_usd(self) -> None:
        tool = CurrencyConverterTool(mock=True)
        out = tool(CurrencyInput(amount=83.5, from_currency="INR", to_currency="USD"))
        assert out.rate == pytest.approx(1.0 / 83.5, rel=1e-9)
        assert out.converted_amount == pytest.approx(1.0, rel=1e-9)

    def test_jpy_to_inr_uses_tabled_value(self) -> None:
        # Brief mandates JPY/INR=0.56 in mock mode (documented, unusual but
        # intentional — live mode is the source of real-world rates).
        tool = CurrencyConverterTool(mock=True)
        out = tool(CurrencyInput(amount=100.0, from_currency="JPY", to_currency="INR"))
        assert out.rate == pytest.approx(0.56)
        assert out.converted_amount == pytest.approx(56.0)

    def test_zero_amount_returns_zero(self) -> None:
        tool = CurrencyConverterTool(mock=True)
        out = tool(CurrencyInput(amount=0.0, from_currency="USD", to_currency="INR"))
        assert out.converted_amount == 0.0
        # 0 USD → 0 INR; we explicitly do NOT call the rate table.
        assert "Zero amount" in out.citation

    def test_zero_amount_no_network_call(self) -> None:
        # Defence: ensure the zero shortcut is taken BEFORE any HTTP path.
        tool = CurrencyConverterTool(mock=False)  # would otherwise go live
        with mock.patch("urllib.request.urlopen") as u:
            out = tool(CurrencyInput(amount=0.0, from_currency="USD", to_currency="INR"))
            u.assert_not_called()
        assert out.converted_amount == 0.0

    def test_same_currency_is_identity(self) -> None:
        tool = CurrencyConverterTool(mock=True)
        out = tool(CurrencyInput(amount=42.0, from_currency="USD", to_currency="USD"))
        assert out.rate == 1.0
        assert out.converted_amount == 42.0
        assert "identity" in out.citation.lower()

    def test_currency_codes_normalised_to_upper(self) -> None:
        tool = CurrencyConverterTool(mock=True)
        out = tool(CurrencyInput(amount=1.0, from_currency="usd", to_currency="inr"))
        assert out.from_currency == "USD"
        assert out.to_currency == "INR"

    def test_unknown_mock_currency_raises_loud(self) -> None:
        tool = CurrencyConverterTool(mock=True)
        tool.base_delay = 0.001  # fast tests; retry tested separately
        tool.max_retries = 0
        with pytest.raises(ToolCallError) as exc:
            tool(CurrencyInput(amount=1.0, from_currency="XYZ", to_currency="INR"))
        assert "XYZ" in str(exc.value)
        assert "mock rate table" in str(exc.value).lower()

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            CurrencyInput(
                amount=1.0, from_currency="USD", to_currency="INR", extra="x"  # type: ignore[call-arg]
            )

    def test_short_currency_code_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CurrencyInput(amount=1.0, from_currency="US", to_currency="INR")  # type: ignore[arg-type]

    def test_cache_ttl_currency(self) -> None:
        tool = CurrencyConverterTool(mock=True)
        assert tool.ttl_seconds == 300

    def test_mock_mode_via_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FINROOT_LLM_PROVIDER", "mock")
        tool = CurrencyConverterTool()  # mock=False default
        out = tool(CurrencyInput(amount=1.0, from_currency="USD", to_currency="INR"))
        assert out.source == "mock"
        assert out.rate == pytest.approx(83.5)

    def test_citation_mentions_2026_06_mock_table(self) -> None:
        tool = CurrencyConverterTool(mock=True)
        out = tool(CurrencyInput(amount=1.0, from_currency="USD", to_currency="INR"))
        assert "2026-06" in out.citation
        assert "Mock" in out.citation


# ---------------------------------------------------------------------------
# CurrencyConverterTool — live mode (HTTP stubbed, no network)
# ---------------------------------------------------------------------------


class TestCurrencyLive:
    def _payload(self, from_ccy: str, rates: dict[str, float]) -> bytes:
        return json.dumps(
            {
                "result": "success",
                "base_code": from_ccy,
                "rates": rates,
            }
        ).encode("utf-8")

    def test_live_success(self) -> None:
        tool = CurrencyConverterTool(mock=False)
        with mock.patch("urllib.request.urlopen") as u:
            u.return_value.__enter__.return_value.read.return_value = self._payload(
                "USD", {"USD": 1.0, "INR": 83.5, "EUR": 0.92}
            )
            out = tool(CurrencyInput(amount=10.0, from_currency="USD", to_currency="EUR"))
        assert out.source == "open.er-api.com"
        assert out.rate == pytest.approx(0.92)
        assert out.converted_amount == pytest.approx(9.2)
        assert "open.er-api.com" in out.citation

    def test_live_network_failure_raises_loud(self) -> None:
        tool = CurrencyConverterTool(mock=False)
        tool.base_delay = 0.001
        tool.max_retries = 0
        with mock.patch("urllib.request.urlopen") as u:
            u.side_effect = urllib.error.URLError("offline")
            with pytest.raises(ToolCallError) as exc:
                tool(CurrencyInput(amount=1.0, from_currency="USD", to_currency="INR"))
        assert "open.er-api.com" in str(exc.value)
        assert "offline" in str(exc.value)

    def test_live_non_success_result_raises_loud(self) -> None:
        tool = CurrencyConverterTool(mock=False)
        tool.base_delay = 0.001
        tool.max_retries = 0
        bad = json.dumps({"result": "error", "base_code": "USD", "rates": {}}).encode("utf-8")
        with mock.patch("urllib.request.urlopen") as u:
            u.return_value.__enter__.return_value.read.return_value = bad
            with pytest.raises(ToolCallError) as exc:
                tool(CurrencyInput(amount=1.0, from_currency="USD", to_currency="INR"))
        assert "non-success" in str(exc.value)


# ---------------------------------------------------------------------------
# Cache behaviour (TTL respected; same input within TTL hits cache)
# ---------------------------------------------------------------------------


class TestCache:
    def test_macro_cache_repeated_call(self) -> None:
        # Repeated calls within TTL should not invoke _run twice. We verify
        # by counting _run invocations.
        tool = MacroDataTool(mock=True)
        runs = {"n": 0}
        original = tool._run

        def counting(inp: MacroInput) -> MacroOutput:
            runs["n"] += 1
            return original(inp)

        with mock.patch.object(tool, "_run", side_effect=counting):
            tool(MacroInput(indicator="gdp_growth"))
            tool(MacroInput(indicator="gdp_growth"))
            tool(MacroInput(indicator="gdp_growth"))
        assert runs["n"] == 1

    def test_currency_cache_repeated_call(self) -> None:
        tool = CurrencyConverterTool(mock=True)
        runs = {"n": 0}
        original = tool._run

        def counting(inp: CurrencyInput) -> CurrencyOutput:
            runs["n"] += 1
            return original(inp)

        with mock.patch.object(tool, "_run", side_effect=counting):
            tool(CurrencyInput(amount=1.0, from_currency="USD", to_currency="INR"))
            tool(CurrencyInput(amount=1.0, from_currency="USD", to_currency="INR"))
        assert runs["n"] == 1

    def test_macro_cache_key_differs_per_indicator(self) -> None:
        tool = MacroDataTool(mock=True)
        runs = {"n": 0}
        original = tool._run

        def counting(inp: MacroInput) -> MacroOutput:
            runs["n"] += 1
            return original(inp)

        with mock.patch.object(tool, "_run", side_effect=counting):
            tool(MacroInput(indicator="gdp_growth"))
            tool(MacroInput(indicator="inflation"))
            tool(MacroInput(indicator="repo_rate"))
            tool(MacroInput(indicator="unemployment"))
        assert runs["n"] == 4
