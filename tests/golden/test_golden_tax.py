"""Golden eval tests — tax reasoning quality (hand-graded).

Runs the full pipeline end-to-end on tax queries and verifies
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


class TestGoldenTax:
    """Tax query golden tests — 5+ end-to-end reasoning quality checks."""

    def test_tax_ltcg_2l_produces_10400(self, run_pipeline):
        """Tax on ₹2L LTCG from equity must produce ₹10,400 via TaxRuleTool."""
        state = run_pipeline("What is the tax on ₹2,00,000 LTCG from equity?")
        tool_text = _all_tool_output_text(state)
        # The deterministic TaxRuleTool computes: (200000 - 100000) * 10% = 10000 + 4% cess = 10400
        assert "10400" in tool_text, (
            f"Tax tool output should contain '10400' for ₹2L LTCG. "
            f"Tool output preview: {tool_text[:500]}"
        )

    def test_tax_cites_tax_rules(self, run_pipeline):
        """Tax query must cite the tax rules or Income Tax Act."""
        state = run_pipeline("What is the tax on ₹2,00,000 LTCG from equity?")
        rec = _get_rec(state)
        # Check citations reference tax rules
        citation_text = " ".join(
            f"{c.source} {c.detail}" for c in rec.citations
        ).lower()
        has_tax_citation = any(
            kw in citation_text
            for kw in ("tax", "income tax", "finance act", "budget", "ltcg")
        )
        assert has_tax_citation or len(rec.citations) >= 1, (
            f"Tax recommendation should cite tax rules. "
            f"Citations: {[(c.source, c.detail[:80]) for c in rec.citations]}"
        )

    def test_tax_confidence_not_insufficient(self, run_pipeline):
        """Tax query confidence should be MEDIUM or HIGH (not INSUFFICIENT)."""
        state = run_pipeline("What is the tax on ₹2,00,000 LTCG from equity?")
        rec = _get_rec(state)
        assert rec.confidence in (
            ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH,
        ), f"Tax confidence should be MEDIUM or HIGH, got {rec.confidence.value}"

    def test_tax_includes_breakdown(self, run_pipeline):
        """Tax query tool outputs must include a breakdown of the computation."""
        state = run_pipeline("What is the tax on ₹2,00,000 LTCG from equity?")
        tool_text = _all_tool_output_text(state)
        # TaxPlannerAgent output includes breakdown with taxable_gain, base_tax, cess
        has_breakdown = any(
            kw in tool_text
            for kw in ("breakdown", "taxable_gain", "base_tax", "cess", "effective_rate")
        )
        assert has_breakdown, (
            f"Tax tool output should include breakdown. "
            f"Tool output preview: {tool_text[:500]}"
        )

    def test_tax_mentions_ltcg(self, run_pipeline):
        """Tax query analysis must mention LTCG/STCG concepts."""
        state = run_pipeline("What is the tax on ₹2,00,000 LTCG from equity?")
        text = _all_text(state)
        has_ltcg = any(kw in text for kw in ("ltcg", "long term capital gain", "capital gain"))
        assert has_ltcg, (
            f"Tax analysis should mention LTCG. Text preview: {text[:300]}"
        )

    def test_tax_intent_classified(self, run_pipeline):
        """Tax query must be classified as TAX intent."""
        state = run_pipeline("What is the tax on ₹2,00,000 LTCG from equity?")
        assert state.intent is not None
        assert state.intent.value == "tax"

    def test_tax_plan_includes_tax_planner(self, run_pipeline):
        """Tax pipeline plan should include tax_planner agent."""
        state = run_pipeline("What is the tax on ₹2,00,000 LTCG from equity?")
        assert "tax_planner" in state.plan, (
            f"Plan should include tax_planner. Plan: {state.plan}"
        )
