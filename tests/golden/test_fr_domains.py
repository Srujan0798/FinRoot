"""PRD domain coverage golden tests (cashflow / insurance / behavioral)."""

from __future__ import annotations

import pytest

from finroot.agents.intent import IntentClassifier
from finroot.schemas.enums import Intent
from finroot.workflows.synthesize import detect_domain
from interface.core import answer

pytestmark = [pytest.mark.golden]


class TestFRDomainCoverage:
    def test_cashflow_first_salary(self) -> None:
        q = "I just got my first salary of ₹80k — how should I split SIP and emergency fund?"
        r = IntentClassifier().classify(q)
        assert r.intent == Intent.CASHFLOW
        assert detect_domain(q, r.intent) == "cashflow"
        s = answer(q, mock=True)
        rec = s.final or s.candidate
        assert rec is not None
        text = (rec.summary or "").lower()
        assert "cashflow" in text or "emergency" in text or "sip" in text

    def test_insurance_cover(self) -> None:
        q = "How much health insurance cover does a family of 4 need in a metro?"
        d = detect_domain(q, Intent.GENERAL)
        assert d == "insurance"
        s = answer(q, mock=True)
        rec = s.final or s.candidate
        assert rec is not None
        text = (rec.summary or "").lower()
        assert "insurance" in text or "cover" in text or "sum insured" in text
        assert "market news impact" not in text

    def test_behavioral_checking(self) -> None:
        q = "I keep checking my portfolio every hour and want to sell after a 2% dip"
        d = detect_domain(q, Intent.PORTFOLIO)
        assert d == "behavioral"
        s = answer(q, mock=True)
        rec = s.final or s.candidate
        assert rec is not None
        text = (rec.summary or "").lower()
        assert "behavioral" in text or "bias" in text or "loss aversion" in text
