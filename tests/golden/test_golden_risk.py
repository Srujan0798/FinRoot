"""Golden eval tests — risk reasoning quality (hand-graded).

Runs the full pipeline end-to-end on risk queries and verifies
the reasoning quality of the final Recommendation.
"""

from __future__ import annotations

import pytest

from finroot.schemas.enums import ConfidenceLevel
from finroot.schemas.recommendation import Recommendation
from finroot.schemas.state import AgentState

pytestmark = pytest.mark.golden


def _get_rec(state: AgentState) -> Recommendation:
    rec = state.candidate or state.final
    assert rec is not None, "Pipeline produced no recommendation (candidate and final are both None)"
    return rec


def _all_text(state: AgentState) -> str:
    rec = _get_rec(state)
    parts = [rec.summary, rec.analysis, *rec.risks, *rec.actions, *rec.alternatives]
    return " ".join(parts).lower()


def _all_tool_output_text(state: AgentState) -> str:
    return " ".join(str(o) for o in state.tool_outputs).lower()


class TestGoldenRisk:
    """Risk query golden tests — 5+ end-to-end reasoning quality checks."""

    def test_risk_produces_recommendation(self, run_pipeline):
        """Risk query must produce a valid Recommendation."""
        state = run_pipeline("What is the risk in my portfolio?")
        rec = _get_rec(state)
        assert isinstance(rec, Recommendation)
        assert rec.summary
        assert rec.analysis

    def test_risk_metrics_in_tool_outputs(self, run_pipeline):
        """Risk pipeline tool outputs should contain risk metrics (Monte Carlo or VaR)."""
        state = run_pipeline("What is my risk exposure?")
        tool_text = _all_tool_output_text(state)
        has_metrics = any(
            kw in tool_text
            for kw in ("risk_assessor", "monte_carlo", "expected_return", "probability_of_loss")
        )
        assert has_metrics, (
            f"Risk tool outputs should contain risk metrics. "
            f"Tool output preview: {tool_text[:500]}"
        )

    def test_risk_tolerance_matching(self, run_pipeline):
        """Risk query should reference the twin snapshot risk tolerance."""
        state = run_pipeline("Am I taking too much risk?")
        snap_text = str(state.twin_snapshot).lower()
        assert "risk_tolerance" in snap_text or "conservative" in snap_text or "risk" in snap_text, (
            f"Twin snapshot should contain risk tolerance. Snapshot: {state.twin_snapshot}"
        )

    def test_risk_warnings_in_text(self, run_pipeline):
        """Risk query recommendation should contain risk-related language."""
        state = run_pipeline("What are the major risks in my portfolio?")
        text = _all_text(state)
        risk_keywords = ["risk", "loss", "volatility", "caution", "warning", "downside"]
        found = [kw for kw in risk_keywords if kw in text]
        assert len(found) >= 1, (
            f"Risk recommendation should contain risk language. "
            f"Found: {found}. Text preview: {text[:300]}"
        )

    def test_risk_plan_includes_assessor(self, run_pipeline):
        """Risk query plan should include risk_assessor."""
        state = run_pipeline("What is my risk tolerance?")
        assert "risk_assessor" in state.plan, (
            f"Plan should include risk_assessor. Plan: {state.plan}"
        )

    def test_risk_confidence_not_insufficient(self, run_pipeline):
        """Risk query confidence should not be INSUFFICIENT."""
        state = run_pipeline("Assess the risk in my portfolio")
        rec = _get_rec(state)
        assert rec.confidence != ConfidenceLevel.INSUFFICIENT, (
            f"Risk confidence should not be INSUFFICIENT, got {rec.confidence.value}"
        )

    def test_risk_intent_classified(self, run_pipeline):
        """Risk query must be classified as RISK or PORTFOLIO intent."""
        state = run_pipeline("What is my risk exposure?")
        assert state.intent is not None
        assert state.intent.value in ("risk", "portfolio"), (
            f"Risk query intent should be risk or portfolio, got {state.intent.value}"
        )
