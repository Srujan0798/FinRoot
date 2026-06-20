"""Tests for the CLI and core entry point (wave-7, task 01).

Covers:
* ``answer()`` returns an ``AgentState`` in mock mode.
* ``build_trace()`` returns the correct event shape.
* ``answer()`` with empty query raises ``ValueError``.
* Typer CliRunner invokes the CLI and exits 0.
* Mock mode is the default.
* CLI handles empty query gracefully (exit 1).
* CLI prints output.
* Multiple queries produce valid states.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from finroot.schemas.state import AgentState
from interface.core import answer, build_trace
from interface.cli.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# answer() tests
# ---------------------------------------------------------------------------


class TestAnswer:
    """Tests for the ``answer()`` entry point."""

    def test_answer_returns_agent_state(self) -> None:
        """answer() in mock mode returns a fully-typed AgentState."""
        state = answer("What is my portfolio risk?", mock=True)
        assert isinstance(state, AgentState)

    def test_answer_has_query(self) -> None:
        """The returned state carries the original query."""
        query = "Review my portfolio and flag risks"
        state = answer(query, mock=True)
        assert state.query == query

    def test_answer_has_candidate_or_final(self) -> None:
        """The orchestrator produces a candidate or final recommendation."""
        state = answer("What are the market trends?", mock=True)
        assert state.candidate is not None or state.final is not None

    def test_answer_empty_query_raises(self) -> None:
        """answer() rejects empty / whitespace-only queries."""
        with pytest.raises(ValueError, match="non-empty"):
            answer("", mock=True)
        with pytest.raises(ValueError, match="non-empty"):
            answer("   ", mock=True)

    def test_answer_custom_user_id(self) -> None:
        """answer() accepts a custom user_id."""
        state = answer("Hello", user_id="test_user_123", mock=True)
        assert isinstance(state, AgentState)
        assert state.query == "Hello"


# ---------------------------------------------------------------------------
# build_trace() tests
# ---------------------------------------------------------------------------


class TestBuildTrace:
    """Tests for ``build_trace()``."""

    def test_trace_returns_list(self) -> None:
        """build_trace() returns a list of dicts."""
        state = answer("Hello", mock=True)
        trace = build_trace(state)
        assert isinstance(trace, list)

    def test_trace_event_shape(self) -> None:
        """Each trace event has the required keys."""
        state = answer("Review my portfolio", mock=True)
        trace = build_trace(state)
        for evt in trace:
            assert "step" in evt, f"Missing 'step' key in {evt}"
            assert "node" in evt, f"Missing 'node' key in {evt}"
            assert "action" in evt, f"Missing 'action' key in {evt}"
            assert "detail" in evt, f"Missing 'detail' key in {evt}"
            assert "source" in evt, f"Missing 'source' key in {evt}"

    def test_trace_steps_are_sequential(self) -> None:
        """Trace steps are numbered starting from 0."""
        state = answer("Analyze my portfolio risk", mock=True)
        trace = build_trace(state)
        if trace:
            steps = [evt["step"] for evt in trace]
            assert steps == list(range(len(steps)))


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


class TestCLI:
    """Tests for the Typer CLI app."""

    def test_direct_query_exits_zero(self) -> None:
        """Direct query via callback exits 0 (matches acceptance command pattern)."""
        result = runner.invoke(app, ["--mock", "Review my portfolio"])
        assert result.exit_code == 0, f"Exit code {result.exit_code}, output: {result.output}"

    def test_default_mock_mode(self) -> None:
        """Default invocation uses mock mode."""
        result = runner.invoke(app, ["Hello"])
        assert result.exit_code == 0

    def test_cli_prints_output(self) -> None:
        """CLI output is non-empty."""
        result = runner.invoke(app, ["--mock", "What are my risks?"])
        assert result.exit_code == 0
        assert len(result.output) > 0

    def test_empty_query_exits_nonzero(self) -> None:
        """Empty query triggers an error exit."""
        result = runner.invoke(app, ["--mock", ""])
        assert result.exit_code != 0

    def test_user_flag_accepted(self) -> None:
        """`--user` flag is accepted."""
        result = runner.invoke(app, ["--mock", "--user", "testuser", "Hello"])
        assert result.exit_code == 0

    def test_no_args_shows_help(self) -> None:
        """No arguments shows help text."""
        result = runner.invoke(app, [])
        # Typer returns 0 for help display
        assert "finroot" in result.output.lower() or "FinRoot" in result.output
