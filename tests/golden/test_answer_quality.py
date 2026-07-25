"""Golden answer quality tests — verify reasoning quality of the system.

Runs the full pipeline in mock mode and checks structural properties of the
output: citations, confidence calibration, section structure, domain-specific
reasoning, absence of hallucinated data, and uncertainty handling.
"""

from __future__ import annotations

import re

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
    assert rec is not None, (
        "Pipeline produced no recommendation (candidate and final are both None)"
    )
    return rec


def _all_text(state: AgentState) -> str:
    """Combine all text fields from the recommendation for searching."""
    rec = _get_rec(state)
    parts = [rec.summary, rec.analysis, *rec.risks, *rec.actions, *rec.alternatives]
    return "\n".join(parts)


def _all_text_lower(state: AgentState) -> str:
    return _all_text(state).lower()


# Negative stock prices and other obviously wrong data patterns.
_HALLUCINATION_PATTERNS = [
    re.compile(r"(?:stock|price|share|nav)\s*(?:is|was|=|:)\s*-\s*\₹", re.I),
    re.compile(r"(?:price|value)\s*-\s*\d+", re.I),
    re.compile(r"(?:negative|less than zero)\s*(?:stock|price|return|value)", re.I),
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAnswerQuality:
    """Structural reasoning-quality tests for mock-mode pipeline output."""

    def test_basic_question_answerable(self, run_pipeline):
        """A simple financial question returns a non-empty answer."""
        state = run_pipeline("What is a reasonable asset allocation for a conservative investor?")
        rec = _get_rec(state)
        assert rec.summary.strip(), "Answer summary is empty"
        assert rec.analysis.strip(), "Answer analysis is empty"
        assert len(_all_text(state)) > 50, (
            f"Answer is too short ({len(_all_text(state))} chars). "
            "A financial answer should contain substantive content."
        )

    def test_answer_has_reasoning(self, run_pipeline):
        """Verify the answer includes chain-of-thought reasoning in analysis."""
        state = run_pipeline(
            "I have ₹2.5L in FDs and ₹1L in a liquid fund. "
            "Should I move the FDs into short-duration debt funds to save tax?"
        )
        rec = _get_rec(state)
        # Analysis should be substantially longer than summary, indicating
        # step-by-step reasoning rather than a one-liner.
        assert len(rec.analysis) > len(rec.summary) * 1.5, (
            f"Analysis ({len(rec.analysis)} chars) is not substantially longer "
            f"than summary ({len(rec.summary)} chars). "
            "The answer should contain chain-of-thought reasoning."
        )
        # The analysis should contain connective reasoning words.
        reasoning_markers = [
            "because",
            "therefore",
            "however",
            "consider",
            "since",
            "given",
            "if ",
            "should",
            "will",
            "would",
            "could",
            "first",
            "next",
            "also",
            "additionally",
            "further",
        ]
        text_lower = _all_text_lower(state)
        found = [m for m in reasoning_markers if m in text_lower]
        assert len(found) >= 2, (
            f"Answer lacks reasoning markers. Found only {found}. "
            "Expected connective words (because, therefore, consider, etc.)."
        )

    def test_answer_cites_sources(self, run_pipeline):
        """Verify citations are present and non-empty."""
        state = run_pipeline(
            "What is the tax on ₹2,00,000 of long-term capital gain "
            "from listed equity held for 18 months?"
        )
        rec = _get_rec(state)
        assert len(rec.citations) >= 1, (
            "Answer has zero citations. Every financial answer should cite at least one source."
        )
        for cite in rec.citations:
            assert cite.source.strip(), "Citation has empty source"
            assert cite.detail.strip(), "Citation has empty detail"

    def test_answer_confidence_calibrated(self, run_pipeline):
        """Confidence is a valid ConfidenceLevel enum value."""
        state = run_pipeline(
            "My portfolio is 80% in one large-cap stock and 20% in a liquid fund. "
            "Should I rebalance before FY-end?"
        )
        rec = _get_rec(state)
        assert rec.confidence is not None, "Confidence is None"
        assert isinstance(rec.confidence, ConfidenceLevel), (
            f"Confidence is not a ConfidenceLevel: {type(rec.confidence)}"
        )
        # Confidence should be between 0 and 1 (enum maps to valid values).
        assert rec.confidence in (
            ConfidenceLevel.HIGH,
            ConfidenceLevel.MEDIUM,
            ConfidenceLevel.LOW,
            ConfidenceLevel.INSUFFICIENT,
        ), f"Unexpected confidence value: {rec.confidence}"

    def test_answer_sections_structure(self, run_pipeline):
        """Answer has proper section structure: summary, analysis, risks, actions."""
        state = run_pipeline(
            "I am 35 with a moderate risk profile. I have 70% in equity, "
            "20% in debt and 10% in gold. Is this allocation balanced?"
        )
        rec = _get_rec(state)
        assert rec.summary, "Missing summary section"
        assert rec.analysis, "Missing analysis section"
        assert isinstance(rec.risks, list), "Risks should be a list"
        assert isinstance(rec.actions, list), "Actions should be a list"
        # At least one of risks or actions should be non-empty.
        assert len(rec.risks) > 0 or len(rec.actions) > 0, (
            "Answer should include at least one risk or action item"
        )

    def test_risk_question_mentions_risk_metrics(self, run_pipeline):
        """Risk questions mention VaR, Sharpe, drawdown, or volatility."""
        state = run_pipeline(
            "What is the Value-at-Risk (95%, 1-month) on my current equity portfolio?"
        )
        text = _all_text_lower(state)
        risk_metrics = [
            "var",
            "value-at-risk",
            "value at risk",
            "sharpe",
            "sortino",
            "drawdown",
            "volatility",
            "standard deviation",
            "risk",
            "confidence interval",
            "confidence level",
            "historical",
            "parametric",
            "monte carlo",
        ]
        found = [m for m in risk_metrics if m in text]
        assert len(found) >= 2, (
            f"Risk question answer lacks risk metrics. Found only {found}. "
            f"Expected mentions of VaR, Sharpe, drawdown, volatility, etc."
        )

    def test_tax_question_mentions_tax_concepts(self, run_pipeline):
        """Tax questions mention deductions, income, LTCG, STCG, etc."""
        state = run_pipeline(
            "What is the tax on ₹2,00,000 of long-term capital gain "
            "from listed equity held for 18 months? My total income is ₹18 lakh."
        )
        text = _all_text_lower(state)
        tax_concepts = [
            "ltcg",
            "long-term capital gain",
            "long term capital gain",
            "stcg",
            "short-term capital gain",
            "exemption",
            "cess",
            "tax slab",
            "income tax",
            "finance act",
            "budget",
            "10%",
            "15%",
            "20%",
            "30%",
            "taxable",
            "tax rate",
            "capital gain",
        ]
        found = [m for m in tax_concepts if m in text]
        assert len(found) >= 2, (
            f"Tax answer lacks tax concepts. Found only {found}. "
            "Expected mentions of LTCG/STCG, exemption, cess, slab, etc."
        )

    def test_portfolio_question_mentions_optimization(self, run_pipeline):
        """Portfolio questions mention diversification, rebalancing, allocation."""
        state = run_pipeline(
            "My portfolio is 80% in one large-cap stock and 20% in a liquid fund. "
            "Should I rebalance before FY-end?"
        )
        text = _all_text_lower(state)
        portfolio_concepts = [
            "diversif",
            "rebalanc",
            "allocation",
            "concentration",
            "single-stock",
            "single stock",
            "risk",
            "correlation",
            "asset class",
            "glide path",
            "glide-path",
        ]
        found = [m for m in portfolio_concepts if m in text]
        assert len(found) >= 2, (
            f"Portfolio answer lacks optimization concepts. Found only {found}. "
            "Expected mentions of diversification, rebalancing, allocation, etc."
        )

    def test_answer_no_hallucinated_data(self, run_pipeline):
        """Verify no obviously wrong financial data (e.g., negative stock prices)."""
        state = run_pipeline(
            "What is the tax on ₹50,000 of short-term capital gain "
            "from listed equity held for 6 months?"
        )
        text = _all_text(state)
        for pattern in _HALLUCINATION_PATTERNS:
            matches = pattern.findall(text)
            assert not matches, f"Answer contains potentially hallucinated data: {matches}"
        # Also verify no absurdly large numbers (e.g., tax > gain by 100x).
        numbers = re.findall(r"[\d,]+(?:\.\d+)?", text.replace("₹", ""))
        for num_str in numbers:
            clean = num_str.replace(",", "")
            try:
                val = float(clean)
                # Flag numbers > 10 billion as potentially hallucinated.
                if val > 1e10:
                    pytest.fail(
                        f"Suspiciously large number in answer: {val}. "
                        "This may be hallucinated financial data."
                    )
            except ValueError:
                continue

    def test_answer_handles_uncertainty(self, run_pipeline):
        """When uncertain, answer says so rather than guessing."""
        state = run_pipeline(
            "My cousin says ABC Pharma will 10x in 2 years based on a "
            "WhatsApp tip. Should I put my entire PF balance into it?"
        )
        rec = _get_rec(state)
        text = _all_text_lower(state)
        # Uncertainty should be expressed via low confidence or hedging language.
        has_uncertainty_signal = rec.confidence in (
            ConfidenceLevel.LOW,
            ConfidenceLevel.INSUFFICIENT,
        ) or any(
            kw in text
            for kw in [
                "uncertain",
                "not guaranteed",
                "not confirmed",
                "risk",
                "caution",
                "do not act yet",
                "do not invest",
                "should not",
                "unverified",
                "insufficient evidence",
                "untested",
                "tip",
                "rumor",
                "herd",
            ]
        )
        assert has_uncertainty_signal, (
            f"Answer does not express uncertainty for an unverified tip. "
            f"Confidence={rec.confidence.value}. "
            f"Answer should contain hedging language (risk, caution, uncertain, etc.)."
        )
        # Must NOT give a confident "yes" to a speculative tip.
        confident_yes_patterns = [
            "yes, invest",
            "definitely invest",
            "go ahead",
            "you will profit",
            "certain to",
            "guaranteed",
            "you will definitely",
            "10x is certain",
        ]
        for pat in confident_yes_patterns:
            assert pat not in text, (
                f"Answer confidently endorses a speculative tip: '{pat}' found. "
                "A responsible answer must express uncertainty."
            )
