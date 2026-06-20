"""Tests for the Rooted Prudence Principles verifier (wave-5, task 03).

Minimum 14 tests covering all 7 checks plus edge cases.
"""

from __future__ import annotations

from datetime import UTC, datetime

from finroot.reasoning.principles import PrudentialVerdict, PrudentialVerifier
from finroot.schemas.enums import ConfidenceLevel
from finroot.schemas.recommendation import Citation, Recommendation
from finroot.schemas.state import AgentState

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

UTC_NOW = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)


def _citat() -> Citation:
    return Citation(
        source="yfinance",
        detail="market data",
        value="150.00",
        retrieved_at=UTC_NOW,
    )


def _make_rec(summary: str, analysis: str, citations: list[Citation] | None = None) -> Recommendation:
    return Recommendation(
        summary=summary,
        analysis=analysis,
        citations=citations or [_citat()],
        confidence=ConfidenceLevel.MEDIUM,
    )


def _make_state(
    summary: str = "Diversified portfolio recommendation",
    analysis: str = "Consider a balanced allocation across sectors.",
    twin: dict | None = None,
    tool_outputs: list[dict] | None = None,
    citations: list[Citation] | None = None,
) -> AgentState:
    rec = _make_rec(summary, analysis, citations)
    return AgentState(
        query="What should I invest in?",
        candidate=rec,
        twin_snapshot=twin or {"risk_tolerance": "moderate", "horizon": "long"},
        tool_outputs=tool_outputs or [{"tool": "market_data"}, {"tool": "portfolio_twin"}],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPrudentialVerifier:
    """Tests for PrudentialVerifier.verify()."""

    def setup_method(self) -> None:
        self.verifier = PrudentialVerifier()

    # -- 1. Emergency fund ------------------------------------------------

    def test_emergency_fund_invest_fail(self) -> None:
        """Investing emergency fund must FAIL."""
        state = _make_state(
            summary="Invest your emergency fund in stocks",
            analysis="Move your emergency savings into equity for better returns.",
        )
        verdict = self.verifier.verify(state)
        assert not verdict.compliant
        ef_check = next(c for c in verdict.checks if c["principle"] == "Emergency fund first")
        assert not ef_check["pass"]

    def test_emergency_fund_mention_only_pass(self) -> None:
        """Mentioning emergency fund without investing it should PASS."""
        state = _make_state(
            summary="Keep your emergency fund intact",
            analysis="Before investing, ensure you have 6 months of expenses in your emergency fund.",
        )
        verdict = self.verifier.verify(state)
        ef_check = next(c for c in verdict.checks if c["principle"] == "Emergency fund first")
        assert ef_check["pass"]

    # -- 2. Diversification ------------------------------------------------

    def test_concentration_above_40_fail(self) -> None:
        """Recommending >40% in single asset must FAIL."""
        state = _make_state(
            summary="Allocate 80% to RELIANCE",
            analysis="Put 80% of your portfolio in RELIANCE stock for growth.",
        )
        verdict = self.verifier.verify(state)
        assert not verdict.compliant
        div_check = next(c for c in verdict.checks if c["principle"] == "Diversification")
        assert not div_check["pass"]

    def test_diversified_allocation_pass(self) -> None:
        """Balanced allocation should PASS."""
        state = _make_state(
            summary="Diversified portfolio",
            analysis="Allocate 30% equities, 30% bonds, 20% real estate, 20% cash.",
        )
        verdict = self.verifier.verify(state)
        div_check = next(c for c in verdict.checks if c["principle"] == "Diversification")
        assert div_check["pass"]

    # -- 3. Risk match -----------------------------------------------------

    def test_conservative_investor_aggressive_advice_fail(self) -> None:
        """Conservative investor getting aggressive advice must FAIL."""
        state = _make_state(
            summary="Aggressive growth strategy",
            analysis="Go all-in on volatile penny stocks for maximum returns.",
            twin={"risk_tolerance": "conservative", "horizon": "long"},
        )
        verdict = self.verifier.verify(state)
        assert not verdict.compliant
        risk_check = next(c for c in verdict.checks if c["principle"] == "Risk match")
        assert not risk_check["pass"]

    def test_moderate_investor_conservative_advice_pass(self) -> None:
        """Moderate investor with conservative advice should PASS."""
        state = _make_state(
            summary="Conservative allocation",
            analysis="A stable bond-heavy portfolio suits your moderate risk profile.",
            twin={"risk_tolerance": "moderate", "horizon": "long"},
        )
        verdict = self.verifier.verify(state)
        risk_check = next(c for c in verdict.checks if c["principle"] == "Risk match")
        assert risk_check["pass"]

    # -- 4. No guarantees --------------------------------------------------

    def test_guaranteed_returns_fail(self) -> None:
        """'Guaranteed 20% returns' must FAIL."""
        state = _make_state(
            summary="Guaranteed 20% returns",
            analysis="This fund is guaranteed to give you 20% annual returns.",
        )
        verdict = self.verifier.verify(state)
        assert not verdict.compliant
        ng_check = next(c for c in verdict.checks if c["principle"] == "No guarantees")
        assert not ng_check["pass"]

    def test_will_definitely_lose_fail(self) -> None:
        """'Will definitely' guarantee language must FAIL."""
        state = _make_state(
            summary="This will definitely work",
            analysis="You will definitely profit from this strategy.",
        )
        verdict = self.verifier.verify(state)
        ng_check = next(c for c in verdict.checks if c["principle"] == "No guarantees")
        assert not ng_check["pass"]

    def test_no_guarantee_language_pass(self) -> None:
        """No guarantee language should PASS."""
        state = _make_state(
            summary="Potential for growth",
            analysis="Historical data suggests moderate returns, but past performance does not guarantee future results.",
        )
        verdict = self.verifier.verify(state)
        ng_check = next(c for c in verdict.checks if c["principle"] == "No guarantees")
        assert ng_check["pass"]

    # -- 5. Tax awareness --------------------------------------------------

    def test_sell_without_tax_warn(self) -> None:
        """Sell recommendation without tax mention must be flagged."""
        state = _make_state(
            summary="Sell your position",
            analysis="Sell your AAPL holdings now to lock in gains.",
        )
        verdict = self.verifier.verify(state)
        tax_check = next(c for c in verdict.checks if c["principle"] == "Tax awareness")
        assert not tax_check["pass"]

    def test_sell_with_tax_mention_pass(self) -> None:
        """Sell recommendation with tax consideration should PASS."""
        state = _make_state(
            summary="Tax-efficient exit strategy",
            analysis="Sell your AAPL position after considering capital gains tax implications.",
        )
        verdict = self.verifier.verify(state)
        tax_check = next(c for c in verdict.checks if c["principle"] == "Tax awareness")
        assert tax_check["pass"]

    # -- 6. Horizon match --------------------------------------------------

    def test_long_horizon_short_term_fail(self) -> None:
        """Short-term trade for long-horizon investor must FAIL."""
        state = _make_state(
            summary="Quick swing trade opportunity",
            analysis="Execute a swing trade on NIFTY for quick profit within days.",
            twin={"risk_tolerance": "moderate", "horizon": "long"},
        )
        verdict = self.verifier.verify(state)
        h_check = next(c for c in verdict.checks if c["principle"] == "Horizon match")
        assert not h_check["pass"]

    def test_short_horizon_short_term_pass(self) -> None:
        """Short-term advice for short-horizon user should PASS."""
        state = _make_state(
            summary="Short-term opportunity",
            analysis="A day trading strategy fits your short-term horizon.",
            twin={"risk_tolerance": "high", "horizon": "short"},
        )
        verdict = self.verifier.verify(state)
        h_check = next(c for c in verdict.checks if c["principle"] == "Horizon match")
        assert h_check["pass"]

    # -- 7. Insufficient evidence ------------------------------------------

    def test_low_evidence_specific_claim_fail(self) -> None:
        """Fewer than 2 tool outputs with specific claims must FAIL."""
        state = _make_state(
            summary="Buy RELIANCE at 2500",
            analysis="RELIANCE is trading at 2500, buy now for 15% upside.",
            tool_outputs=[{"tool": "market_data"}],
        )
        verdict = self.verifier.verify(state)
        assert not verdict.compliant
        ev_check = next(c for c in verdict.checks if c["principle"] == "Insufficient evidence")
        assert not ev_check["pass"]

    def test_sufficient_evidence_pass(self) -> None:
        """At least 2 tool outputs should PASS."""
        state = _make_state(
            summary="Balanced recommendation",
            analysis="Based on market data and twin analysis, allocate 30% to equities.",
            tool_outputs=[{"tool": "market_data"}, {"tool": "portfolio_twin"}],
        )
        verdict = self.verifier.verify(state)
        ev_check = next(c for c in verdict.checks if c["principle"] == "Insufficient evidence")
        assert ev_check["pass"]

    # -- Integration / verdict shape ---------------------------------------

    def test_good_advice_all_pass(self) -> None:
        """Well-cited, appropriate advice must be compliant."""
        state = _make_state(
            summary="Balanced portfolio for your profile",
            analysis="Allocate 30% equities, 30% bonds, 20% real estate, 20% cash. "
            "Past performance does not guarantee future results.",
            twin={"risk_tolerance": "moderate", "horizon": "long"},
            tool_outputs=[{"tool": "market_data"}, {"tool": "portfolio_twin"}, {"tool": "tax_tables"}],
            citations=[_citat()],
        )
        verdict = self.verifier.verify(state)
        assert verdict.compliant
        assert verdict.warning is None
        assert all(c["pass"] for c in verdict.checks)

    def test_non_compliant_has_warning(self) -> None:
        """Non-compliant verdict must include the standard warning."""
        state = _make_state(
            summary="Guaranteed 50% returns",
            analysis="Invest your emergency fund, guaranteed 50% returns. All-in on one stock.",
        )
        verdict = self.verifier.verify(state)
        assert not verdict.compliant
        assert verdict.warning == "This advice may not be suitable for your profile"

    def test_verdict_is_pydantic_model(self) -> None:
        """Verdict must be a proper Pydantic model."""
        state = _make_state()
        verdict = self.verifier.verify(state)
        assert isinstance(verdict, PrudentialVerdict)
        assert isinstance(verdict.compliant, bool)
        assert isinstance(verdict.checks, list)
        assert len(verdict.checks) == 7

    def test_all_principles_represented(self) -> None:
        """All 7 principles must appear in the verdict."""
        expected = {
            "Emergency fund first",
            "Diversification",
            "Risk match",
            "No guarantees",
            "Tax awareness",
            "Horizon match",
            "Insufficient evidence",
        }
        state = _make_state()
        verdict = self.verifier.verify(state)
        actual = {c["principle"] for c in verdict.checks}
        assert actual == expected

    def test_empty_twin_snapshot_pass(self) -> None:
        """Missing twin fields should not crash; conservative default."""
        state = _make_state(
            summary="Balanced advice",
            analysis="Diversify across asset classes.",
            twin={},
        )
        verdict = self.verifier.verify(state)
        risk_check = next(c for c in verdict.checks if c["principle"] == "Risk match")
        horizon_check = next(c for c in verdict.checks if c["principle"] == "Horizon match")
        assert risk_check["pass"]
        assert horizon_check["pass"]
