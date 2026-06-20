"""Reusable Plotly chart builders for the FinRoot Streamlit UI.

All builders honour the dark finance theme from :mod:`interface.ui.theme` and
return a :class:`plotly.graph_objects.Figure`. Plotly is imported lazily so the
rest of the UI keeps working when Plotly is not installed — callers should
gate on :func:`is_plotly_available` and fall back to ``st.info`` if False.

Writes: ``src/interface/ui/components/charts.py`` (wave-7, task 06).
"""

from __future__ import annotations

from typing import Any

from interface.ui.theme import (
    ACCENT,
    BG_NAVY,
    CARD_BG,
    GREEN,
    RED,
    TEXT_DEFAULT,
    TEXT_MUTED,
)

# -- Lazy Plotly import (per task: "Lazy-import plotly") ---------------------

try:
    import plotly.graph_objects as go

    _HAS_PLOTLY = True
except ImportError:  # pragma: no cover - exercised only without plotly
    go = None  # type: ignore[assignment]
    _HAS_PLOTLY = False


# -- Public API ---------------------------------------------------------------


def is_plotly_available() -> bool:
    """Return True if Plotly was imported successfully at module load."""
    return _HAS_PLOTLY


def _require_plotly() -> None:
    """Raise a clear error if Plotly is not importable."""
    if not _HAS_PLOTLY:
        msg = (
            "Plotly is required for this chart. Install it with: "
            "`pip install plotly` (or `pip install 'finroot[charts]'`)."
        )
        raise ImportError(msg)


# -- Common theming helpers ---------------------------------------------------

_PALETTE: tuple[str, ...] = (
    ACCENT,
    GREEN,
    "#F0883E",  # orange (mid-warm)
    "#A371F7",  # purple
    "#56D4DD",  # cyan
    RED,
    "#DB61A2",  # pink
    "#7D8590",  # muted gray
)


def _dark_layout(title: str | None = None) -> dict[str, Any]:
    """Return a baseline layout dict matching the FinRoot dark theme."""
    layout: dict[str, Any] = {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {
            "family": "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
            "color": TEXT_DEFAULT,
            "size": 12,
        },
        "margin": {"l": 24, "r": 16, "t": 36, "b": 24},
        "hoverlabel": {
            "bgcolor": CARD_BG,
            "bordercolor": TEXT_MUTED,
            "font": {"color": TEXT_DEFAULT, "family": "monospace"},
        },
        "legend": {
            "bgcolor": "rgba(0,0,0,0)",
            "font": {"color": TEXT_DEFAULT},
        },
    }
    if title:
        layout["title"] = {
            "text": title,
            "font": {"color": TEXT_DEFAULT, "size": 14},
            "x": 0.02,
            "xanchor": "left",
        }
    return layout


def _empty_figure(message: str = "No data") -> Any:
    """Return a placeholder Figure shown when there is nothing to chart."""
    _require_plotly()
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font={"color": TEXT_MUTED, "size": 14},
    )
    fig.update_layout(**_dark_layout())
    return fig


def _holding_value(holding: dict[str, Any]) -> float:
    """Return ``quantity * unit_price`` for a holding dict (FM-11: 0 default)."""
    qty = holding.get("quantity", 0) or 0
    price = holding.get("unit_price", 0) or 0
    return float(qty) * float(price)


def _holding_label(holding: dict[str, Any]) -> str:
    """Return the human-readable label for a holding."""
    return str(holding.get("name") or holding.get("asset_id") or "Unknown")


# -- Chart builders -----------------------------------------------------------


def allocation_pie(holdings: list[dict[str, Any]]) -> Any:
    """Build a donut pie chart of portfolio allocation by holding value.

    Each slice is sized by ``quantity * unit_price``. Empty holdings return an
    annotated placeholder figure so the UI can still render the panel.
    """
    _require_plotly()

    if not holdings:
        return _empty_figure("No holdings to chart")

    labels: list[str] = []
    values: list[float] = []
    for h in holdings:
        value = _holding_value(h)
        if value <= 0:
            continue
        labels.append(_holding_label(h))
        values.append(value)

    if not values:
        return _empty_figure("Holdings have zero value")

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker={
                    "colors": [_PALETTE[i % len(_PALETTE)] for i in range(len(labels))],
                    "line": {"color": BG_NAVY, "width": 2},
                },
                textinfo="percent",
                hovertemplate="<b>%{label}</b><br>Value: \u20b9%{value:,.0f}"
                "<br>Share: %{percent}<extra></extra>",
            )
        ]
    )
    layout = _dark_layout(title="Allocation Breakdown")
    layout["showlegend"] = True
    layout["legend"]["orientation"] = "v"
    layout["legend"]["yanchor"] = "middle"
    layout["legend"]["y"] = 0.5
    layout["legend"]["xanchor"] = "left"
    layout["legend"]["x"] = 1.02
    fig.update_layout(**layout)
    return fig


def domain_bar_chart(scores: dict[str, float]) -> Any:
    """Build a horizontal bar chart of FRB domain scores.

    ``scores`` is a mapping of domain name -> mean score (typically 0-1).
    Empty dicts return a placeholder figure.
    """
    _require_plotly()

    if not scores:
        return _empty_figure("No per-domain scores")

    ordered = sorted(scores.items(), key=lambda kv: kv[1])
    domains = [k for k, _ in ordered]
    values = [float(v) for _, v in ordered]

    # Colour each bar green if >=0.7, accent if 0.4-0.7, red otherwise.
    bar_colors: list[str] = []
    for v in values:
        if v >= 0.7:
            bar_colors.append(GREEN)
        elif v >= 0.4:
            bar_colors.append(ACCENT)
        else:
            bar_colors.append(RED)

    fig = go.Figure(
        data=[
            go.Bar(
                x=values,
                y=domains,
                orientation="h",
                marker={"color": bar_colors, "line": {"color": BG_NAVY, "width": 1}},
                text=[f"{v:.2f}" for v in values],
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Score: %{x:.3f}<extra></extra>",
            )
        ]
    )
    layout = _dark_layout(title="Mean Score by Domain")
    layout["xaxis"] = {
        "range": [0, 1],
        "gridcolor": "#21262D",
        "zerolinecolor": "#21262D",
        "color": TEXT_MUTED,
        "title": {"text": "score", "font": {"color": TEXT_MUTED}},
    }
    layout["yaxis"] = {
        "gridcolor": "rgba(0,0,0,0)",
        "color": TEXT_DEFAULT,
        "automargin": True,
    }
    fig.update_layout(**layout)
    return fig


def confidence_gauge(score: float, label: str = "Confidence") -> Any:
    """Build a gauge chart for a confidence score in [0, 1].

    Bands: red 0-0.4, accent 0.4-0.7, green 0.7-1.0 — matches theme badges.
    Scores outside [0, 1] are clamped; non-numeric input raises ValueError.
    """
    _require_plotly()

    try:
        numeric = float(score)
    except (TypeError, ValueError) as exc:
        msg = f"confidence_gauge score must be numeric, got {score!r}"
        raise ValueError(msg) from exc
    clamped = max(0.0, min(1.0, numeric))

    fig = go.Figure(
        data=[
            go.Indicator(
                mode="gauge+number",
                value=clamped,
                number={"suffix": "", "valueformat": ".0%", "font": {"color": TEXT_DEFAULT}},
                title={
                    "text": f"{label} ({clamped:.0%})",
                    "font": {"color": TEXT_MUTED, "size": 12},
                },
                gauge={
                    "axis": {
                        "range": [0, 1],
                        "tickvals": [0, 0.25, 0.5, 0.75, 1.0],
                        "tickformat": ".0%",
                        "tickcolor": TEXT_MUTED,
                        "tickfont": {"color": TEXT_MUTED},
                    },
                    "bar": {"color": ACCENT, "thickness": 0.25},
                    "bgcolor": CARD_BG,
                    "borderwidth": 0,
                    "steps": [
                        {"range": [0.0, 0.4], "color": RED},
                        {"range": [0.4, 0.7], "color": ACCENT},
                        {"range": [0.7, 1.0], "color": GREEN},
                    ],
                    "threshold": {
                        "line": {"color": TEXT_DEFAULT, "width": 3},
                        "thickness": 0.75,
                        "value": clamped,
                    },
                },
                domain={"x": [0, 1], "y": [0, 1]},
            )
        ]
    )
    layout = _dark_layout()
    layout["margin"] = {"l": 16, "r": 16, "t": 48, "b": 8}
    fig.update_layout(**layout)
    return fig


# Map risk band keywords to a numeric 0-1 score for the risk meter.
_RISK_SCORES: dict[str, float] = {
    "VERY LOW": 0.1,
    "LOW": 0.2,
    "CONSERVATIVE": 0.25,
    "MODERATE": 0.5,
    "MEDIUM": 0.55,
    "HIGH": 0.8,
    "AGGRESSIVE": 0.9,
    "VERY HIGH": 0.95,
}


def risk_meter(risk_level: str) -> Any:
    """Build a visual risk meter for a risk band string (e.g. ``MODERATE``).

    Unrecognised labels fall back to a centred (0.5) reading and add a note
    in the title — never fails loud on unknown inputs, but never silently
    fabricates a category either.
    """
    _require_plotly()

    upper = (risk_level or "").strip().upper()
    score = _RISK_SCORES.get(upper)
    if score is None:
        display_title = f"Risk Meter (unknown: '{risk_level}')"
        score = 0.5
    else:
        display_title = f"Risk Meter \u2014 {upper}"

    fig = go.Figure(
        data=[
            go.Indicator(
                mode="gauge+number",
                value=score,
                number={
                    "valueformat": ".0%",
                    "font": {"color": TEXT_DEFAULT, "size": 28},
                },
                title={
                    "text": display_title,
                    "font": {"color": TEXT_MUTED, "size": 12},
                },
                gauge={
                    "axis": {
                        "range": [0, 1],
                        "tickvals": [0, 0.25, 0.5, 0.75, 1.0],
                        "tickformat": ".0%",
                        "tickcolor": TEXT_MUTED,
                        "tickfont": {"color": TEXT_MUTED},
                    },
                    "bar": {"color": BG_NAVY, "thickness": 0},  # hide bar; use threshold only
                    "bgcolor": CARD_BG,
                    "borderwidth": 0,
                    "steps": [
                        {"range": [0.0, 0.4], "color": GREEN},
                        {"range": [0.4, 0.7], "color": ACCENT},
                        {"range": [0.7, 1.0], "color": RED},
                    ],
                    "threshold": {
                        "line": {"color": TEXT_DEFAULT, "width": 6},
                        "thickness": 0.85,
                        "value": score,
                    },
                },
                domain={"x": [0, 1], "y": [0, 1]},
            )
        ]
    )
    layout = _dark_layout()
    layout["margin"] = {"l": 16, "r": 16, "t": 48, "b": 8}
    fig.update_layout(**layout)
    return fig


__all__ = [
    "is_plotly_available",
    "allocation_pie",
    "domain_bar_chart",
    "confidence_gauge",
    "risk_meter",
]
