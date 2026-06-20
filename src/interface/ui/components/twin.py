"""Digital Twin + Portfolio Viewer component for FinRoot Streamlit UI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import streamlit as st
except ImportError:
    st = None  # type: ignore[assignment]

try:
    from interface.ui.components.charts import allocation_pie, is_plotly_available
except ImportError:  # pragma: no cover - charts module is always present in this wave
    allocation_pie = None  # type: ignore[assignment]
    is_plotly_available = None  # type: ignore[assignment]

_PROFILES_PATH = Path(__file__).resolve().parents[4] / "data" / "samples" / "twin_profiles.json"


def load_demo_twin() -> dict[str, Any]:
    """Load the first twin profile from the sample JSON file."""
    raw = json.loads(_PROFILES_PATH.read_text())
    if not raw:
        msg = f"No twin profiles found in {_PROFILES_PATH}"
        raise FileNotFoundError(msg)
    return raw[0]


def _holdings_value(holdings: list[dict[str, Any]]) -> float:
    """Sum of (quantity * unit_price) across all holdings."""
    total = 0.0
    for h in holdings:
        qty = h.get("quantity", 0)
        price = h.get("unit_price", 0)
        total += qty * price
    return total


def load_twin_by_user_id(user_id: str) -> dict[str, Any]:
    """Load a twin profile by user_id, falling back to the first profile."""
    raw = json.loads(_PROFILES_PATH.read_text())
    if not raw:
        msg = f"No twin profiles found in {_PROFILES_PATH}"
        raise FileNotFoundError(msg)
    for profile in raw:
        if profile.get("user_id") == user_id or profile.get("name", "").lower() == user_id.lower():
            return profile
    return raw[0]


def render(twin: dict[str, Any] | None = None, user_id: str | None = None) -> None:
    """Render the Digital Twin viewer panel in Streamlit.

    Parameters
    ----------
    twin:
        A raw twin dict (as loaded from ``twin_profiles.json``).  When
        ``None``, the first demo profile is loaded via ``load_demo_twin()``.
    user_id:
        Optional user ID to load a specific profile. Falls back to first profile.
    """
    if st is None:
        msg = "Streamlit is required to render the twin viewer. Install it with: pip install streamlit"
        raise ImportError(msg)

    if twin is None:
        twin = load_twin_by_user_id(user_id) if user_id else load_demo_twin()

    name = twin.get("name")
    age = twin.get("age")
    risk = twin.get("risk_tolerance", "N/A")
    horizon = twin.get("investment_horizon", "N/A")
    income = twin.get("monthly_income", 0.0)
    expenses = twin.get("monthly_expenses", 0.0)
    tax_bracket = twin.get("tax_bracket_pct", 0.0)
    goals = twin.get("goals", [])
    constraints = twin.get("constraints", [])
    holdings = twin.get("holdings", [])

    if not name:
        st.info("No profile name available.")
        return

    st.header(f"Financial Digital Twin: {name}")

    # --- Profile card ---
    st.subheader("Profile")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Age", age)
    col2.metric("Risk Tolerance", risk.title())
    col3.metric("Investment Horizon", horizon.title())
    col4.metric("Tax Bracket", f"{tax_bracket}%")

    # --- Financial headline numbers ---
    st.subheader("Monthly Finances")
    surplus = income - expenses
    c1, c2, c3 = st.columns(3)
    c1.metric("Monthly Income", f"\u20b9{income:,.0f}")
    c2.metric("Monthly Expenses", f"\u20b9{expenses:,.0f}")
    c3.metric("Monthly Surplus", f"\u20b9{surplus:,.0f}")

    # --- Goals ---
    st.subheader("Goals")
    if goals:
        for g in goals:
            st.markdown(f"- {g}")
    else:
        st.info("No goals defined for this profile.")

    # --- Constraints ---
    st.subheader("Constraints")
    if constraints:
        for c in constraints:
            st.markdown(f"- {c}")
    else:
        st.info("No constraints defined for this profile.")

    # --- Holdings ---
    st.subheader("Portfolio Holdings")
    if not holdings:
        st.info("No holdings data available.")
        return

    total_value = _holdings_value(holdings)

    rows: list[dict[str, Any]] = []
    for h in holdings:
        qty = h.get("quantity", 0)
        price = h.get("unit_price", 0)
        value = qty * price
        pct = (value / total_value * 100) if total_value > 0 else 0.0
        rows.append(
            {
                "Symbol": h.get("name", h.get("asset_id", "—")),
                "Type": h.get("asset_type", "—"),
                "Quantity": f"{qty:,.2f}",
                "Unit Price": f"\u20b9{price:,.2f}",
                "Value": f"\u20b9{value:,.2f}",
                "Allocation %": f"{pct:.1f}%",
            }
        )

    st.dataframe(rows, use_container_width=True)

    st.metric("Total Portfolio Value", f"\u20b9{total_value:,.2f}")

    # Allocation pie chart (Plotly)
    st.subheader("Allocation Breakdown")
    if is_plotly_available is not None and is_plotly_available() and allocation_pie is not None:
        st.plotly_chart(allocation_pie(holdings), use_container_width=True)
    else:
        st.info(
            "Plotly is not installed — install with `pip install plotly` for an "
            "interactive allocation pie chart."
        )
        alloc = {
            h.get("name", h.get("asset_id", "—")): h.get("quantity", 0) * h.get("unit_price", 0)
            for h in holdings
        }
        st.bar_chart(alloc)
