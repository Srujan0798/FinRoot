"""Tests for the Plotly chart builders (wave-7, task 06).

Covers:
* Module imports succeed even when Plotly is absent (defensive import).
* Each chart builder returns a :class:`plotly.graph_objects.Figure`.
* Empty / malformed inputs return a placeholder figure rather than raising.
* Theme colour constants from ``interface.ui.theme`` are applied.
* ``twin.py`` and ``harness.py`` reference the new builders.
"""

from __future__ import annotations

import types

import pytest

from interface.ui.components import charts


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


SAMPLE_HOLDINGS: list[dict] = [
    {
        "asset_id": "EQ_RELIANCE",
        "name": "Reliance Industries",
        "asset_type": "equity",
        "quantity": 10,
        "unit_price": 2400.0,
    },
    {
        "asset_id": "FD_HDFC",
        "name": "HDFC Fixed Deposit",
        "asset_type": "fixed_deposit",
        "quantity": 1,
        "unit_price": 500000.0,
    },
    {
        "asset_id": "GLD_ETF",
        "name": "Gold ETF",
        "asset_type": "gold",
        "quantity": 25,
        "unit_price": 5800.0,
    },
]


@pytest.fixture(scope="module")
def go_module():
    """Return the real plotly.graph_objects module, or skip the test if absent."""
    if not charts.is_plotly_available():
        pytest.skip("plotly is not installed in this environment")
    return charts.go


# ---------------------------------------------------------------------------
# Module-level tests
# ---------------------------------------------------------------------------


class TestImports:
    """charts module imports correctly and exposes its public surface."""

    def test_module_imports(self) -> None:
        """charts.py imports as a module."""
        assert isinstance(charts, types.ModuleType)

    def test_public_api(self) -> None:
        """All four chart builders and the availability helper are exported."""
        for name in ("is_plotly_available", "allocation_pie", "domain_bar_chart",
                     "confidence_gauge", "risk_meter"):
            assert hasattr(charts, name), f"missing public name: {name}"

    def test_is_plotly_available_returns_bool(self) -> None:
        """is_plotly_available returns a boolean (not raising)."""
        assert isinstance(charts.is_plotly_available(), bool)


# ---------------------------------------------------------------------------
# allocation_pie
# ---------------------------------------------------------------------------


class TestAllocationPie:
    """allocation_pie builds a donut pie of holdings values."""

    def test_returns_figure(self, go_module) -> None:
        """Returns a plotly.graph_objects.Figure instance."""
        fig = charts.allocation_pie(SAMPLE_HOLDINGS)
        assert isinstance(fig, go_module.Figure)

    def test_includes_all_value_holdings(self, go_module) -> None:
        """Every holding with positive value appears as a pie slice."""
        fig = charts.allocation_pie(SAMPLE_HOLDINGS)
        pie_traces = [t for t in fig.data if isinstance(t, go_module.Pie)]
        assert len(pie_traces) == 1
        labels = list(pie_traces[0].labels)
        assert set(labels) == {
            "Reliance Industries",
            "HDFC Fixed Deposit",
            "Gold ETF",
        }

    def test_empty_holdings_returns_placeholder(self, go_module) -> None:
        """Empty holdings list returns a placeholder figure, not raise."""
        fig = charts.allocation_pie([])
        assert isinstance(fig, go_module.Figure)
        # No actual pie trace for empty data.
        pies = [t for t in fig.data if isinstance(t, go_module.Pie)]
        assert pies == []

    def test_zero_value_holdings_returns_placeholder(self, go_module) -> None:
        """Holdings with quantity=0 or unit_price=0 yield placeholder."""
        fig = charts.allocation_pie([{"name": "Ghost", "quantity": 0, "unit_price": 0}])
        pies = [t for t in fig.data if isinstance(t, go_module.Pie)]
        assert pies == []

    def test_uses_dark_theme_paper_bgcolor(self, go_module) -> None:
        """Paper background is transparent (dark theme)."""
        fig = charts.allocation_pie(SAMPLE_HOLDINGS)
        # paper_bgcolor should be set to a transparent dark colour.
        assert "rgba(0,0,0,0)" in (fig.layout.paper_bgcolor or "")


# ---------------------------------------------------------------------------
# domain_bar_chart
# ---------------------------------------------------------------------------


class TestDomainBarChart:
    """domain_bar_chart builds a horizontal bar chart of FRB domain scores."""

    def test_returns_figure(self, go_module) -> None:
        """Returns a plotly.graph_objects.Figure instance."""
        fig = charts.domain_bar_chart({"risk": 0.8, "tax": 0.55, "portfolio": 0.35})
        assert isinstance(fig, go_module.Figure)

    def test_sorted_ascending(self, go_module) -> None:
        """Bars are ordered ascending by score (worst at top)."""
        fig = charts.domain_bar_chart({"alpha": 0.9, "beta": 0.5, "gamma": 0.7})
        bar = next(t for t in fig.data if isinstance(t, go_module.Bar))
        y_vals = list(bar.y)
        assert y_vals == ["beta", "gamma", "alpha"]

    def test_empty_dict_returns_placeholder(self, go_module) -> None:
        """Empty scores dict returns a placeholder figure, not raise."""
        fig = charts.domain_bar_chart({})
        assert isinstance(fig, go_module.Figure)
        bars = [t for t in fig.data if isinstance(t, go_module.Bar)]
        assert bars == []

    def test_x_axis_range(self, go_module) -> None:
        """X-axis is bounded to [0, 1]."""
        fig = charts.domain_bar_chart({"x": 0.42})
        assert tuple(fig.layout.xaxis.range) == (0, 1)


# ---------------------------------------------------------------------------
# confidence_gauge
# ---------------------------------------------------------------------------


class TestConfidenceGauge:
    """confidence_gauge builds a gauge for a [0, 1] score."""

    def test_returns_figure(self, go_module) -> None:
        """Returns a plotly.graph_objects.Figure instance."""
        fig = charts.confidence_gauge(0.75)
        assert isinstance(fig, go_module.Figure)

    def test_clamps_above_one(self, go_module) -> None:
        """Scores > 1.0 are clamped to 1.0."""
        fig = charts.confidence_gauge(1.5)
        ind = fig.data[0]
        assert ind.value == 1.0

    def test_clamps_below_zero(self, go_module) -> None:
        """Scores < 0.0 are clamped to 0.0."""
        fig = charts.confidence_gauge(-0.5)
        assert fig.data[0].value == 0.0

    def test_non_numeric_raises(self) -> None:
        """Non-numeric input raises ValueError (fail loud, FM-11)."""
        with pytest.raises(ValueError, match="numeric"):
            charts.confidence_gauge("not-a-number")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# risk_meter
# ---------------------------------------------------------------------------


class TestRiskMeter:
    """risk_meter builds a visual gauge for a risk band string."""

    def test_returns_figure(self, go_module) -> None:
        """Returns a plotly.graph_objects.Figure instance."""
        fig = charts.risk_meter("MODERATE")
        assert isinstance(fig, go_module.Figure)

    def test_known_levels_map_to_numeric(self, go_module) -> None:
        """Each known risk level maps to a 0-1 numeric value."""
        for level in ("CONSERVATIVE", "MODERATE", "AGGRESSIVE"):
            fig = charts.risk_meter(level)
            value = fig.data[0].value
            assert 0.0 <= value <= 1.0, f"{level} -> {value}"

    def test_unknown_level_falls_back_to_centre(self, go_module) -> None:
        """Unknown risk levels do not raise; value defaults to 0.5."""
        fig = charts.risk_meter("WHO_KNOWS")
        assert fig.data[0].value == 0.5

    def test_case_insensitive(self, go_module) -> None:
        """Risk level matching is case-insensitive."""
        assert charts.risk_meter("aggressive").data[0].value == pytest.approx(
            charts.risk_meter("AGGRESSIVE").data[0].value
        )


# ---------------------------------------------------------------------------
# Integration: components that USE charts.py
# ---------------------------------------------------------------------------


class TestComponentsUseCharts:
    """twin.py and harness.py import & branch on is_plotly_available."""

    def test_twin_imports_charts(self) -> None:
        """twin.py imports allocation_pie / is_plotly_available from charts."""
        from interface.ui.components import twin as twin_mod

        # At import time we resolve either real callables or None; both are fine.
        assert hasattr(twin_mod, "allocation_pie")
        assert hasattr(twin_mod, "is_plotly_available")

    def test_harness_imports_charts(self) -> None:
        """harness.py imports domain_bar_chart / is_plotly_available from charts."""
        from interface.ui.components import harness as harness_mod

        assert hasattr(harness_mod, "domain_bar_chart")
        assert hasattr(harness_mod, "is_plotly_available")
