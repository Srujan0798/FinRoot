"""Golden eval tests — news reasoning quality (hand-graded).

Runs the full pipeline end-to-end on news/impact queries and verifies
the reasoning quality of the final Recommendation.
"""

from __future__ import annotations

import pytest

from finroot.schemas.recommendation import Recommendation
from finroot.schemas.state import AgentState

pytestmark = pytest.mark.golden


def _get_rec(state: AgentState) -> Recommendation:
    rec = state.candidate or state.final
    assert rec is not None, "Pipeline produced no recommendation (candidate and final are both None)"
    return rec


def _all_tool_output_text(state: AgentState) -> str:
    return " ".join(str(o) for o in state.tool_outputs).lower()


class TestGoldenNews:
    """News/impact query golden tests — 5+ end-to-end reasoning quality checks."""

    def test_news_produces_recommendation(self, run_pipeline):
        """News query must produce a valid Recommendation."""
        state = run_pipeline("What is the latest news about Indian markets?")
        rec = _get_rec(state)
        assert isinstance(rec, Recommendation)
        assert rec.summary
        assert rec.analysis

    def test_news_retrieval_in_tool_outputs(self, run_pipeline):
        """News pipeline should invoke news_search tool."""
        state = run_pipeline("Latest news on Indian stock market")
        tool_text = _all_tool_output_text(state)
        assert "news_search" in tool_text, (
            f"News tool outputs should contain news_search. "
            f"Tool output preview: {tool_text[:500]}"
        )

    def test_news_sentiment_analysis_in_tool_outputs(self, run_pipeline):
        """News pipeline should invoke sentiment_analysis tool."""
        state = run_pipeline("What is the market news today?")
        tool_text = _all_tool_output_text(state)
        assert "sentiment_analysis" in tool_text or "sentiment" in tool_text, (
            f"News tool outputs should contain sentiment analysis. "
            f"Tool output preview: {tool_text[:500]}"
        )

    def test_news_has_citations(self, run_pipeline):
        """News query recommendation should cite sources."""
        state = run_pipeline("What is the latest news about Indian markets?")
        rec = _get_rec(state)
        assert len(rec.citations) >= 1, (
            f"News recommendation should have at least 1 citation, "
            f"got {len(rec.citations)}"
        )

    def test_news_has_actions(self, run_pipeline):
        """News query should produce actionable recommendations."""
        state = run_pipeline("How does the budget news affect my portfolio?")
        rec = _get_rec(state)
        assert len(rec.actions) >= 1, (
            f"News recommendation should have at least 1 action, "
            f"got {len(rec.actions)}"
        )

    def test_news_intent_classified(self, run_pipeline):
        """News query must be classified as NEWS_IMPACT intent."""
        state = run_pipeline("Latest news on Indian stock market")
        assert state.intent is not None
        assert state.intent.value == "news_impact"

    def test_news_plan_includes_agents(self, run_pipeline):
        """News pipeline plan should include news_interpreter and market_analyst."""
        state = run_pipeline("What is the latest news about Indian markets?")
        has_agents = "news_interpreter" in state.plan and "market_analyst" in state.plan
        assert has_agents, (
            f"Plan should include news_interpreter and market_analyst. Plan: {state.plan}"
        )
