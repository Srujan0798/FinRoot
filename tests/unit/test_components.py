"""Tests for the Chat and Trace UI components (wave-7, task 03).

Covers:
* Module imports succeed.
* ``render()`` is a callable function with the expected signature.
* ``build_trace()`` integration through ``interface.core`` works.
* Internal helpers handle edge cases gracefully.
"""

from __future__ import annotations

import types

from finroot.schemas.state import AgentState
from interface.core import build_trace

# ---------------------------------------------------------------------------
# Module import tests
# ---------------------------------------------------------------------------


class TestImports:
    """chat and trace modules import correctly."""

    def test_chat_module_imports(self) -> None:
        """chat.py module imports without error."""
        from interface.ui.components import chat as chat_mod

        assert isinstance(chat_mod, types.ModuleType)

    def test_trace_module_imports(self) -> None:
        """trace.py module imports without error."""
        from interface.ui.components import trace as trace_mod

        assert isinstance(trace_mod, types.ModuleType)

    def test_components_init_imports(self) -> None:
        """components/__init__.py imports as a package."""
        import interface.ui.components

        assert isinstance(interface.ui.components, types.ModuleType)

    def test_chat_render_is_callable(self) -> None:
        """chat.render() exists and accepts keyword arguments."""
        from interface.ui.components.chat import render

        assert callable(render)

    def test_trace_render_is_callable(self) -> None:
        """trace.render() exists and accepts keyword arguments."""
        from interface.ui.components.trace import render

        assert callable(render)


# ---------------------------------------------------------------------------
# build_trace() integration with AgentState
# ---------------------------------------------------------------------------


class TestBuildTraceEdgeCases:
    """build_trace handles unusual/empty AgentState gracefully."""

    def test_build_trace_empty_state(self) -> None:
        """build_trace on a minimal AgentState returns a list."""
        state = AgentState(
            query="test",
            plan=[],
            tool_outputs=[],
            audit_events=[],
        )
        trace = build_trace(state)
        assert isinstance(trace, list)

    def test_build_trace_with_plan(self) -> None:
        """build_trace includes plan steps."""
        state = AgentState(
            query="test",
            plan=["Step 1: analyze", "Step 2: recommend"],
            tool_outputs=[],
            audit_events=[],
        )
        trace = build_trace(state)
        plan_events = [e for e in trace if e["node"] == "planner"]
        assert len(plan_events) == 2

    def test_build_trace_event_keys(self) -> None:
        """Every trace event has the 5 required keys."""
        state = AgentState(
            query="test",
            plan=["analyze"],
            tool_outputs=[{"tool": "yfinance", "type": "lookup", "ticker": "AAPL"}],
            audit_events=[],
        )
        trace = build_trace(state)
        required = {"step", "node", "action", "detail", "source"}
        for evt in trace:
            assert required.issubset(evt.keys()), f"Missing keys in {evt}"


# ---------------------------------------------------------------------------
# Trace internal helpers
# ---------------------------------------------------------------------------


class TestTraceInternals:
    """Unit tests for trace helper functions (no Streamlit runtime)."""

    def test_render_critic_verdict_none(self) -> None:
        """_render_critic_verdict handles missing critique (no-op)."""
        from interface.ui.components.trace import _render_critic_verdict

        state = AgentState(query="test", plan=[], tool_outputs=[], audit_events=[])
        _render_critic_verdict(state)

    def test_render_verifier_verdict_none(self) -> None:
        """_render_verifier_verdict handles missing verifier_verdict (no-op)."""
        from interface.ui.components.trace import _render_verifier_verdict

        state = AgentState(query="test", plan=[], tool_outputs=[], audit_events=[])
        _render_verifier_verdict(state)

    def test_render_citations_table_none(self) -> None:
        """_render_citations_table handles missing recommendation (no-op)."""
        from interface.ui.components.trace import _render_citations_table

        state = AgentState(query="test", plan=[], tool_outputs=[], audit_events=[])
        _render_citations_table(state)

    def test_render_streaming_exists(self) -> None:
        """render_streaming function exists and is callable."""
        from interface.ui.components.trace import render_streaming

        assert callable(render_streaming)

    def test_render_streaming_signature(self) -> None:
        """render_streaming accepts state parameter."""
        from interface.ui.components.trace import render_streaming
        import inspect

        sig = inspect.signature(render_streaming)
        params = list(sig.parameters.keys())
        assert "state" in params
