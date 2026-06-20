"""Golden eval tests — international / multi-currency reasoning quality.

Runs the full pipeline end-to-end on international, currency, and
cross-border queries, verifying that relevant concepts surface
in the recommendation and tool outputs.
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


def _all_text(state: AgentState) -> str:
    rec = _get_rec(state)
    parts = [rec.summary, rec.analysis, *rec.risks, *rec.actions, *rec.alternatives]
    return " ".join(parts).lower()


def _all_tool_output_text(state: AgentState) -> str:
    return " ".join(str(o) for o in state.tool_outputs).lower()


class TestGoldenInternational:
    """International / multi-currency golden tests — 5+ end-to-end checks."""

    def test_international_query_produces_recommendation(self, run_pipeline):
        """International query must produce a valid Recommendation (never crash)."""
        state = run_pipeline("How do international markets affect my portfolio?")
        rec = _get_rec(state)
        assert isinstance(rec, Recommendation)
        assert rec.summary
        assert rec.analysis

    def test_international_currency_concept_in_context(self, run_pipeline):
        """Currency-related query should contain currency/exchange concepts in tool outputs."""
        state = run_pipeline("What is the exchange rate between USD and INR?")
        tool_text = _all_tool_output_text(state)
        has_currency = any(
            kw in tool_text
            for kw in ("currency", "usd", "inr", "exchange")
        )
        assert has_currency, (
            f"Currency query tool outputs should mention currency concepts. "
            f"Tool output preview: {tool_text[:500]}"
        )

    def test_international_market_comparison(self, run_pipeline):
        """Cross-country market query should be classified as news_impact or portfolio."""
        state = run_pipeline("Compare US and Indian stock market performance")
        assert state.intent is not None
        assert state.intent.value in ("news_impact", "portfolio"), (
            f"Cross-country query intent should be news_impact or portfolio, "
            f"got {state.intent.value}"
        )

    def test_international_has_actions(self, run_pipeline):
        """International query should produce at least one action."""
        state = run_pipeline("How do I invest in US markets from India?")
        rec = _get_rec(state)
        assert len(rec.actions) >= 1, (
            f"International recommendation should have at least 1 action, "
            f"got {len(rec.actions)}"
        )

    def test_international_citations_exist(self, run_pipeline):
        """International query recommendation should cite sources."""
        state = run_pipeline("What is the tax treatment of US stocks for Indian residents?")
        rec = _get_rec(state)
        assert len(rec.citations) >= 1, (
            f"International recommendation should have at least 1 citation, "
            f"got {len(rec.citations)}"
        )

    def test_international_fx_risk_concept(self, run_pipeline):
        """FX risk query should reference currency or FX in tool outputs."""
        state = run_pipeline("What is the FX risk in my foreign holdings?")
        tool_text = _all_tool_output_text(state)
        has_fx = any(
            kw in tool_text
            for kw in ("fx", "currency", "foreign", "exchange")
        )
        assert has_fx, (
            f"FX risk query tool outputs should mention FX or currency. "
            f"Tool output preview: {tool_text[:500]}"
        )
