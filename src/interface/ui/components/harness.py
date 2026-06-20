"""Harness tab — live FRB benchmark display with run capability.

Renders results/metrics.json (fast path) or runs the harness live.
Numbers come exclusively from metrics.json / harness output (FM-05/12).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

try:
    import streamlit as st

    _HAS_ST = True
except ImportError:
    _HAS_ST = False

if TYPE_CHECKING:  # pragma: no cover
    pass

_METRICS_PATH = Path("results/metrics.json")


def _load_metrics() -> dict[str, Any] | None:
    """Load metrics.json if it exists, return None otherwise."""
    if _METRICS_PATH.exists():
        return json.loads(_METRICS_PATH.read_text())
    return None


def _render_comparison_table(st: Any, metrics: dict[str, Any]) -> None:
    """Render the system comparison table."""
    systems = metrics.get("systems", {})
    if not systems:
        st.warning("No system results in metrics.json.")
        return

    rows = []
    for name in ["finroot", "rag", "single_agent"]:
        s = systems.get(name, {})
        if not s:
            continue
        rows.append(
            {
                "System": name,
                "Pass@1": f"{s.get('pass_at_1', 0):.1%}",
                "Pass@k": f"{s.get('pass_at_k', 0):.1%}",
                "Pass^k": f"{s.get('pass_hat_k', 0):.1%}",
                "Mean Score": f"{s.get('mean_score', 0):.3f}",
            }
        )

    if rows:
        st.table(rows)


def _render_domain_chart(st: Any, metrics: dict[str, Any]) -> None:
    """Render per-domain bar chart of finroot mean scores."""
    systems = metrics.get("systems", {})
    finroot = systems.get("finroot", {})
    per_domain = finroot.get("per_domain", {})

    if not per_domain:
        st.info("No per-domain data available.")
        return

    st.subheader("FinRoot Mean Score by Domain")
    st.bar_chart(per_domain)


def render() -> None:
    """Render the Harness tab in Streamlit."""
    if not _HAS_ST:
        return

    st.header("FRB Benchmark Harness")

    metrics = _load_metrics()

    # --- Run button ---
    if st.button("Run benchmark", key="run_benchmark"):
        with st.spinner("Running FRB benchmark (mock mode)..."):
            try:
                from finroot.evaluation.harness import HarnessConfig, run_harness  # noqa: PLC0415

                run_harness(HarnessConfig(k=3, mock=True))
                metrics = _load_metrics()
                st.success("Benchmark complete.")
            except ImportError:
                st.info(
                    "Harness module not importable. "
                    "Run `scripts/run_evals.py --mock` to generate results/metrics.json manually."
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"Benchmark failed: {exc}")

    if metrics is None:
        st.info(
            "No results/metrics.json found. Click 'Run benchmark' above or "
            "run `scripts/run_evals.py --mock` to generate it."
        )
        return

    # --- Headline metric ---
    lift = metrics.get("composite_lift_vs_rag_pct", 0.0)
    k = metrics.get("k", 0)
    n_tasks = metrics.get("n_tasks", 0)

    st.metric(
        "Composite Lift vs RAG",
        f"+{lift:.1f}%",
        delta=f"{k} trials, {n_tasks} tasks",
        delta_color="normal",
    )

    # --- System comparison table ---
    st.subheader("System Comparison")
    _render_comparison_table(st, metrics)

    # --- Per-domain chart ---
    _render_domain_chart(st, metrics)

    # --- Caption ---
    mock_label = "Mock mode" if metrics.get("mock", True) else "Live mode"
    st.caption(f"{k} trials, {n_tasks} tasks, {mock_label} \u2014 reproducible offline.")
