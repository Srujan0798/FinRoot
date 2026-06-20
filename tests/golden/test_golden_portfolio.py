"""Golden eval tests — portfolio reasoning quality (hand-graded).

Runs the full pipeline end-to-end on portfolio queries and verifies
the reasoning quality of the final Recommendation.
"""

from __future__ import annotations

import pytest

from finroot.schemas.enums import ConfidenceLevel
from finroot.schemas.recommendation import Recommendation
from finroot.schemas.state import AgentState

pytestmark = pytest.mark.golden


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_rec(state: AgentState) -> Recommendation:
    """Extract the recommendation from candidate or final."""
    rec = state.candidate or state.final
    assert rec is not None, "Pipeline produced no recommendation (candidate and final are both None)"
    return rec


def _all_text(state: AgentState) -> str:
    """Combine all text fields from the recommendation for searching."""
    rec = _get_rec(state)
    parts = [rec.summary, rec.analysis, *rec.risks, *rec.actions, *rec.alternatives]
    return " ".join(parts).lower()


def _all_tool_output_text(state: AgentState) -> str:
    """Combine all tool outputs into a searchable string."""
    return " ".join(str(o) for o in state.tool_outputs).lower()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGoldenPortfolio:
    """Portfolio query golden tests — 5+ end-to-end reasoning quality checks."""

    def test_portfolio_produces_recommendation(self, run_pipeline):
        """Portfolio query must produce a valid Recommendation."""
        state = run_pipeline("Review my portfolio allocation and diversification")
        rec = _get_rec(state)
        assert isinstance(rec, Recommendation)
        assert rec.summary
        assert rec.analysis

    def test_portfolio_includes_allocation_breakdown(self, run_pipeline):
        """Portfolio query analysis must discuss allocation or diversification."""
        state = run_pipeline("Analyze my portfolio allocation")
        text = _all_text(state)
        allocation_keywords = [
            "allocation", "diversif", "weight", "concentration",
            "equity", "debt", "asset",
        ]
        found = [kw for kw in allocation_keywords if kw in text]
        assert len(found) >= 2, (
            f"Portfolio analysis should mention allocation concepts. "
            f"Found: {found}. Text preview: {text[:300]}"
        )

    def test_portfolio_includes_monte_carlo(self, run_pipeline):
        """Portfolio pipeline should run Monte Carlo simulation via tool outputs."""
        state = run_pipeline("Review my portfolio with simulation")
        tool_text = _all_tool_output_text(state)
        # Check for Monte Carlo or simulation output from agents
        has_simulation = any(
            kw in tool_text
            for kw in ("monte_carlo", "simulation", "portfolio_simulator", "rebalancing_comparison")
        )
        assert has_simulation, (
            "Portfolio pipeline should include Monte Carlo simulation in tool outputs. "
            f"Tool output preview: {tool_text[:500]}"
        )

    def test_portfolio_cites_tools(self, run_pipeline):
        """Portfolio query must cite data sources."""
        state = run_pipeline("What is my current portfolio allocation?")
        rec = _get_rec(state)
        # The recommendation should have citations from the pipeline
        assert len(rec.citations) >= 1, (
            f"Portfolio recommendation should have at least 1 citation, "
            f"got {len(rec.citations)}"
        )

    def test_portfolio_has_actions(self, run_pipeline):
        """Portfolio query must produce actionable recommendations."""
        state = run_pipeline("How should I rebalance my portfolio?")
        rec = _get_rec(state)
        assert len(rec.actions) >= 1, (
            f"Portfolio recommendation should have at least 1 action, "
            f"got {len(rec.actions)}"
        )

    def test_portfolio_confidence_medium_or_high(self, run_pipeline):
        """Portfolio query should have MEDIUM or HIGH confidence (not LOW/INSUFFICIENT)."""
        state = run_pipeline("Review my portfolio allocation")
        rec = _get_rec(state)
        assert rec.confidence in (ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH), (
            f"Portfolio confidence should be MEDIUM or HIGH, got {rec.confidence.value}"
        )

    def test_portfolio_intent_classified(self, run_pipeline):
        """Portfolio query must be classified as PORTFOLIO intent."""
        state = run_pipeline("Review my portfolio holdings and allocation")
        assert state.intent is not None
        assert state.intent.value == "portfolio"

    def test_portfolio_plan_includes_agents(self, run_pipeline):
        """Portfolio pipeline plan should include portfolio_optimizer."""
        state = run_pipeline("Analyze my portfolio diversification")
        assert "portfolio_optimizer" in state.plan, (
            f"Plan should include portfolio_optimizer. Plan: {state.plan}"
        )
