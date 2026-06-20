"""Reasoning-trace panel — renders the step-by-step reasoning timeline.

Shows the plan, tool calls, self-critic verdict (5-axis scores), principles
verifier verdict, and a citations table.  Reads ``AgentState`` from the
argument or from ``st.session_state["last_state"]``.
"""

from __future__ import annotations

from typing import Any

try:
    import streamlit as st
except ImportError:
    st = None  # type: ignore[assignment]

from finroot.schemas.recommendation import Recommendation
from interface.core import build_trace


def _render_trace_events(trace: list[dict[str, Any]]) -> None:
    """Render the step-by-step timeline as expanders."""
    if not trace:
        st.info("No trace events available.")
        return

    for event in trace:
        node = event.get("node", "?")
        action = event.get("action", "?")
        detail = event.get("detail", "")
        source = event.get("source")

        label = f"**{node}** — {action}"
        if source:
            label += f"  `{source}`"

        with st.expander(label, icon="🔍"):
            st.markdown(detail or "*no detail*")


def _render_critic_verdict(state: Any) -> None:
    """Render the self-critic 5-axis scores + pass/fail + must_fix."""
    critique: dict | None = getattr(state, "critique", None)
    if critique is None:
        return

    st.markdown("### Self-Critic Verdict")
    scores = critique.get("scores", [])
    overall = critique.get("overall", 0.0)
    passed = critique.get("passed", False)
    must_fix = critique.get("must_fix", [])

    # Overall pass/fail badge
    status = "✅ PASSED" if passed else "❌ FAILED"
    st.markdown(
        f"**Overall:** {overall:.2f} — {status}"
        f"{'  ⚠️ Must fix: ' + ', '.join(must_fix) if must_fix else ''}"
    )

    # Per-axis score bars
    if scores:
        st.markdown("**Axis Scores**")
        for axis_score in scores:
            axis = axis_score.get("axis", "?")
            score = axis_score.get("score", 0.0)
            rationale = axis_score.get("rationale", "")
            issues = axis_score.get("issues", [])

            pct = int(score * 100)
            bar_color = "#3FB950" if score >= 0.6 else "#F85149"
            bar_html = (
                f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0;">'
                f'<span style="width:130px;font-size:0.85rem;"><b>{axis}</b></span>'
                f'<div style="flex:1;height:14px;background:#30363D;border-radius:7px;overflow:hidden;">'
                f'<div style="width:{pct}%;height:100%;background:{bar_color};border-radius:7px;"></div>'
                f'</div>'
                f'<span style="width:36px;text-align:right;font-family:monospace;">{score:.2f}</span>'
                f'</div>'
            )
            st.markdown(bar_html, unsafe_allow_html=True)

            if rationale:
                st.caption(rationale)
            if issues:
                for issue in issues:
                    st.markdown(f"  - ⚠️ {issue}")


def _render_verifier_verdict(state: Any) -> None:
    """Render the principles verifier verdict."""
    verifier_verdict: dict | None = getattr(state, "verifier_verdict", None)
    if verifier_verdict is None:
        return

    st.markdown("### Prudential Principles Verifier")
    compliant = verifier_verdict.get("compliant", True)
    status = "✅ Compliant" if compliant else "❌ Non-compliant"
    st.markdown(f"**Status:** {status}")

    warning = verifier_verdict.get("warning")
    if warning:
        st.warning(warning)

    checks = verifier_verdict.get("checks", [])
    for check in checks:
        principle = check.get("principle", "?")
        check_pass = check.get("pass", True)
        detail = check.get("detail", "")
        icon = "✅" if check_pass else "❌"
        st.markdown(f"{icon} **{principle}** — {detail}")


def _render_citations_table(state: Any) -> None:
    """Render the citations table from the recommendation."""
    rec: Recommendation | None = getattr(state, "candidate", None) or getattr(
        state, "final", None
    )
    if rec is None or not rec.citations:
        return

    st.markdown("### Citations")
    rows = []
    for cit in rec.citations:
        rows.append(
            {
                "Source": cit.source,
                "Detail": cit.detail,
                "Value": cit.value or "—",
            }
        )
    st.dataframe(rows, use_container_width=True)


def render(state: Any = None) -> None:
    """Render the Reasoning Trace tab.

    Parameters
    ----------
    state:
        An ``AgentState`` (or any object with ``critique``, ``verifier_verdict``
        and the fields expected by ``build_trace()``).  When ``None``, reads
        from ``st.session_state.get("last_state")``.
    """
    if st is None:
        msg = "Streamlit is required. Install it with: pip install streamlit"
        raise ImportError(msg)

    if state is None:
        state = st.session_state.get("last_state")

    if state is None:
        st.info("Ask a question in the Chat tab to see the reasoning trace.")
        return

    # 1. Step-by-step trace timeline
    st.markdown("### Reasoning Trace")
    trace = build_trace(state)
    _render_trace_events(trace)

    # 2. Self-critic verdict
    _render_critic_verdict(state)

    # 3. Prudential principles verifier
    _render_verifier_verdict(state)

    # 4. Citations table
    _render_citations_table(state)
