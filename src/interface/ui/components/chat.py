"""Chat component — query input + answer card for FinRoot Streamlit UI.

Renders a ``st.chat_input`` bar, calls ``interface.core.answer()`` on submit,
and displays the response as a structured finance card: summary, confidence
badge, risk badge, action items, and citations.  Stores the full ``AgentState``
in ``st.session_state["last_state"]`` for the Trace tab.
"""

from __future__ import annotations

from typing import Any

try:
    import streamlit as st
except ImportError:
    st = None  # type: ignore[assignment]

from finroot.schemas.recommendation import Recommendation
from interface.core import answer
from interface.ui.theme import confidence_badge, risk_badge


def _render_citations(citations: list[Any]) -> None:
    """Render a compact citations section."""
    if not citations:
        return
    st.markdown("#### Citations")
    for cit in citations:
        src = getattr(cit, "source", cit.get("source", "—"))
        detail = getattr(cit, "detail", cit.get("detail", ""))
        val = getattr(cit, "value", cit.get("value"))
        parts = [f"**{src}**"]
        if detail:
            parts.append(detail)
        if val:
            parts.append(f"`{val}`")
        st.markdown("  - " + " · ".join(parts))


def _render_answer_card(state: Any) -> None:
    """Render the answer as a finance card with structured fields."""
    rec: Recommendation | None = getattr(state, "candidate", None) or getattr(
        state, "final", None
    )
    if rec is None:
        st.warning("The agent produced no recommendation.")
        return

    # --- Summary + badges ---
    st.markdown(f"### {rec.summary}")

    badge_cols = st.columns([1, 1, 4])
    badge_cols[0].markdown(
        f"**Confidence**  \n{confidence_badge(rec.confidence.value)}",
        unsafe_allow_html=True,
    )

    # Risk band — derive from the twin snapshot if available, or just show the raw risks count
    twin = getattr(state, "twin_snapshot", {})
    risk_label = twin.get("risk_tolerance", "moderate")
    badge_cols[1].markdown(
        f"**Risk Profile**  \n{risk_badge(risk_label)}",
        unsafe_allow_html=True,
    )

    # --- Analysis ---
    st.markdown("**Analysis**")
    st.markdown(rec.analysis)

    # --- Action items ---
    if rec.actions:
        st.markdown("**Actions**")
        for a in rec.actions:
            st.markdown(f"- {a}")

    # --- Risks ---
    if rec.risks:
        st.markdown("**Risks**")
        for r in rec.risks:
            st.markdown(f"- {r}")

    # --- Alternatives ---
    if rec.alternatives:
        st.markdown("**Alternatives**")
        for alt in rec.alternatives:
            st.markdown(f"- {alt}")

    # --- Assumptions ---
    if rec.assumptions:
        st.markdown("**Assumptions**")
        for a in rec.assumptions:
            st.markdown(f"- {a}")

    # --- Citations ---
    _render_citations(rec.citations)


def render(*, user_id: str = "demo", mock: bool = True) -> None:
    """Render the Chat tab in Streamlit.

    Parameters
    ----------
    user_id:
        Stable user identifier for memory / twin lookup.
        Passed through to ``interface.core.answer()``.
    mock:
        If ``True`` (default), use the offline ``MockProvider``.
    """
    if st is None:
        msg = "Streamlit is required. Install it with: pip install streamlit"
        raise ImportError(msg)

    # Initialise session state
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Render previous messages
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    query: str | None = st.chat_input("Ask a financial question…")
    if not query:
        return

    # Add user message to history
    st.session_state["chat_history"].append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Call the pipeline
    with st.chat_message("assistant"):
        with st.spinner("Reasoning…"):
            try:
                state = answer(query, user_id=user_id, mock=mock)
            except Exception as exc:
                st.error(f"Failed to get answer: {exc}")
                return

        # Store full state for the Trace tab
        st.session_state["last_state"] = state

        # Render the answer card
        _render_answer_card(state)

        # Also store a concise assistant message for the history
        rec: Recommendation | None = getattr(state, "candidate", None) or getattr(
            state, "final", None
        )
        summary = rec.summary if rec is not None else "[No recommendation produced]"
        st.session_state["chat_history"].append(
            {"role": "assistant", "content": summary}
        )

        # Render the trace with streaming effect
        from interface.ui.components.trace import render_streaming

        render_streaming(state)
