"""Sacred golden paths GP-1..GP-5 for SCALE PS-1 (wave-ultra).

These tests lock the demo queries a hostile judge will try first.
Fail closed — do not weaken asserts to greenwash.
"""

from __future__ import annotations

import pytest

from finroot.agents.intent import IntentClassifier
from finroot.agents.tax_agent import _parse_gain_from_query, _parse_indian_amount
from finroot.schemas.enums import Intent
from finroot.workflows.synthesize import detect_domain
from interface.core import answer

pytestmark = [pytest.mark.golden]


class TestIntentMatrixGP:
    def setup_method(self) -> None:
        self.clf = IntentClassifier()

    def test_gp1_portfolio_intent(self) -> None:
        r = self.clf.classify(
            "Should I rebalance my 70/30 equity portfolio before FY-end?"
        )
        assert r.intent == Intent.PORTFOLIO

    def test_gp2_tax_intent(self) -> None:
        r = self.clf.classify(
            "What is LTCG tax on ₹1,00,000 equity gains held 2 years in India?"
        )
        assert r.intent == Intent.TAX
        assert "LTCG" not in r.entities.get("symbols", [])

    def test_gp4_loan_stocks_is_risk(self) -> None:
        r = self.clf.classify(
            "Should I take a personal loan to buy more stocks for higher returns?"
        )
        assert r.intent == Intent.RISK

    def test_gp5_var_portfolio_is_risk(self) -> None:
        r = self.clf.classify("Calculate VaR and max drawdown for my portfolio")
        assert r.intent == Intent.RISK

    def test_gp3_emergency_smallcap_is_risk(self) -> None:
        r = self.clf.classify(
            "I have ₹2 lakh emergency fund. Should I put it all in a small-cap stock?"
        )
        assert r.intent == Intent.RISK


class TestTaxParse:
    def test_parse_1l(self) -> None:
        assert _parse_indian_amount("tax on 1L gains") == 100_000.0

    def test_parse_rupee_grouped(self) -> None:
        assert _parse_indian_amount("₹1,00,000 LTCG") == 100_000.0

    def test_parse_lakh_word(self) -> None:
        assert _parse_indian_amount("2 lakh LTCG from equity") == 200_000.0

    def test_parse_gain_type_and_amount(self) -> None:
        info = _parse_gain_from_query(
            "What is my LTCG tax on 1L gains from equity held 2 years in India?"
        )
        assert info.get("gain") == 100_000.0
        assert info.get("gain_type") == "LTCG"


class TestDomainRespectsIntent:
    def test_tax_intent_not_news(self) -> None:
        q = "What is my LTCG tax on 1L gains from equity held 2 years in India?"
        assert detect_domain(q, Intent.TAX) == "tax"

    def test_portfolio_var_upgrades_to_risk(self) -> None:
        q = "What is the VaR on my equity portfolio?"
        assert detect_domain(q, Intent.PORTFOLIO) == "risk"

    def test_risk_intent_stays_risk(self) -> None:
        q = "Calculate VaR and max drawdown for my portfolio"
        assert detect_domain(q, Intent.RISK) == "risk"


class TestAnswerGoldenPaths:
    """End-to-end answer() checks (mock)."""

    def test_gp2_tax_summary_not_news(self) -> None:
        s = answer(
            "What is LTCG tax on ₹1,00,000 equity gains held 2 years in India?",
            user_id="demo",
            mock=True,
        )
        rec = s.final or s.candidate
        assert rec is not None
        text = (rec.summary or "").lower()
        assert "market news impact" not in text
        assert any(k in text for k in ("ltcg", "tax", "cess", "exemption", "10%"))
        # tax engine should have run
        msgs = [str(o) for o in (s.tool_outputs or [])]
        assert not any("missing required input" in m.lower() for m in msgs)

    def test_gp4_not_news_summary(self) -> None:
        s = answer(
            "Should I take a personal loan to buy more stocks for higher returns?",
            user_id="demo",
            mock=True,
        )
        rec = s.final or s.candidate
        assert rec is not None
        text = (rec.summary or "").lower()
        assert "market news impact" not in text
        assert s.intent == Intent.RISK

    def test_gp1_portfolio_runs(self) -> None:
        s = answer(
            "Should I rebalance my 70/30 equity portfolio before FY-end?",
            user_id="demo",
            mock=True,
        )
        rec = s.final or s.candidate
        assert rec is not None
        assert s.intent == Intent.PORTFOLIO
        text = (rec.summary or "").lower()
        assert "market news impact" not in text
