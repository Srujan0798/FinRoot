"""FinRoot Streamlit application shell.

Entry point for the demo UI.  Provides a dark finance theme, sidebar
controls, and four tabs that gracefully degrade if component tasks
(03 / 04 / 05) have not landed yet.

Writes: ``src/interface/ui/app.py`` (wave-7, task 02).
"""

from __future__ import annotations

import logging

import streamlit as st

from interface.ui.theme import apply_theme

logger = logging.getLogger(__name__)


def main() -> None:
    """Launch the FinRoot Streamlit app."""
    st.set_page_config(
        page_title="FinRoot \u2014 Sovereign Financial Reasoning",
        layout="wide",
        page_icon="\U0001f331",
    )

    # Inject dark theme CSS
    st.markdown(apply_theme(), unsafe_allow_html=True)

    # -- Sidebar ---------------------------------------------------------------
    with st.sidebar:
        st.markdown("## \U0001f331 FinRoot")
        mock_mode = st.toggle("Mock Mode (offline)", value=True)
        user_id = st.text_input("User ID", value="demo")
        st.markdown(
            "_Sovereign, reasoning-first AI financial reasoning_ \u2014 "
            "shows its work, flags risk, cites evidence."
        )

    # -- Header ----------------------------------------------------------------
    st.markdown("# FinRoot \u2014 Sovereign Financial Reasoning")
    st.caption(
        "Institutional-grade, explainable financial reasoning \u2014 "
        "locally and on your own terms."
    )

    # -- Tabs ------------------------------------------------------------------
    tab_chat, tab_trace, tab_twin, tab_harness = st.tabs(
        ["\U0001f4ac Chat", "\U0001f9e0 Reasoning Trace", "\U0001f464 Digital Twin", "\U0001f4ca Harness"]
    )

    with tab_chat:
        _render_tab_chat(user_id=user_id, mock=mock_mode)

    with tab_trace:
        _render_tab_trace()

    with tab_twin:
        _render_tab_twin(user_id=user_id)

    with tab_harness:
        _render_tab_harness()


# -- Tab renderers (component imports deferred / guarded) ---------------------


def _render_tab_chat(*, user_id: str, mock: bool) -> None:  # noqa: ARG001
    """Render the Chat tab."""
    try:
        from interface.ui.components.chat import render

        render(user_id=user_id, mock=mock)
    except Exception as exc:
        st.info(f"Chat component loading\u2026 ({exc})")


def _render_tab_trace() -> None:
    """Render the Reasoning Trace tab."""
    try:
        from interface.ui.components.trace import render

        render()
    except Exception as exc:
        st.info(f"Reasoning Trace component loading\u2026 ({exc})")


def _render_tab_twin(*, user_id: str) -> None:
    """Render the Digital Twin tab."""
    try:
        from interface.ui.components.twin import render

        render(user_id=user_id)
    except Exception as exc:
        st.info(f"Digital Twin component loading\u2026 ({exc})")


def _render_tab_harness() -> None:
    """Render the Harness (eval / metrics) tab."""
    try:
        from interface.ui.components.harness import render

        render()
    except Exception as exc:
        st.info(f"Harness component loading\u2026 ({exc})")


if __name__ == "__main__":
    main()
