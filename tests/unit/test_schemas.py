"""Tests for the core schemas (wave-1, task 02).

Covers:
* Round-trip serialize/deserialize for every public model.
* FM-11: numeric content in `Recommendation.analysis` requires citations.
* `extra="forbid"` rejects unknown fields on every public model.
* UTC-aware datetime enforcement on every datetime field.
* Re-exports from `finroot.schemas` package.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from finroot.schemas import (  # re-exports sanity
    AgentState,
    AuditEvent,
    Citation,
    ConfidenceLevel,
    Domain,
    Holding,
    Horizon,
    Intent,
    Money,
    Portfolio,
    Provider,
    Recommendation,
    RiskBand,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

UTC_NOW = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)
ZERO_HASH = "0" * 64
SAMPLE_HASH = "a" * 64


def _citat(value: str | None = None) -> Citation:
    return Citation(
        source="yfinance",
        detail="AAPL last close",
        value=value,
        retrieved_at=UTC_NOW,
    )


# ---------------------------------------------------------------------------
# Enum sanity
# ---------------------------------------------------------------------------


class TestEnums:
    def test_intent_values(self) -> None:
        assert Intent.PORTFOLIO.value == "portfolio"
        assert Intent.RISK.value == "risk"
        assert Intent.TAX.value == "tax"
        assert Intent.NEWS_IMPACT.value == "news_impact"
        assert Intent.CASHFLOW.value == "cashflow"
        assert Intent.CREDIT.value == "credit"
        assert Intent.GENERAL.value == "general"

    def test_confidence_levels(self) -> None:
        assert {c.value for c in ConfidenceLevel} == {
            "high",
            "medium",
            "low",
            "insufficient",
        }

    def test_risk_bands(self) -> None:
        assert {r.value for r in RiskBand} == {"low", "moderate", "high", "severe"}

    def test_providers(self) -> None:
        assert {p.value for p in Provider} == {"mock", "ollama", "groq", "openai"}

    def test_domain_values(self) -> None:
        assert Domain.EQUITY.value == "equity"
        assert Domain.FIXED_INCOME.value == "fixed_income"
        assert Domain.OTHER.value == "other"

    def test_enums_are_strings(self) -> None:
        # str-Enum interop (JSON serialization, Pydantic discriminator use)
        assert Intent.PORTFOLIO == "portfolio"
        assert isinstance(Intent.PORTFOLIO, str)


# ---------------------------------------------------------------------------
# Citation
# ---------------------------------------------------------------------------


class TestCitation:
    def test_round_trip(self) -> None:
        c = _citat("123.45")
        json = c.model_dump_json()
        c2 = Citation.model_validate_json(json)
        assert c2 == c
        assert c2.value == "123.45"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            Citation(
                source="x",
                detail="y",
                retrieved_at=UTC_NOW,
                bogus="nope",  # type: ignore[call-arg]
            )

    def test_rejects_naive_datetime(self) -> None:
        with pytest.raises(ValidationError):
            Citation(
                source="x",
                detail="y",
                retrieved_at=datetime(2026, 1, 1),  # naive
            )

    def test_rejects_blank_source_or_detail(self) -> None:
        with pytest.raises(ValidationError):
            Citation(source="", detail="x", retrieved_at=UTC_NOW)
        with pytest.raises(ValidationError):
            Citation(source="x", detail="   ", retrieved_at=UTC_NOW)


# ---------------------------------------------------------------------------
# Recommendation — the FM-11 guard
# ---------------------------------------------------------------------------


class TestRecommendation:
    def test_qualitative_analysis_passes_without_citations(self) -> None:
        r = Recommendation(
            summary="Diversify",
            analysis="Concentrated positions carry idiosyncratic risk.",
            confidence=ConfidenceLevel.MEDIUM,
        )
        assert r.citations == []
        assert r.confidence is ConfidenceLevel.MEDIUM

    def test_numeric_analysis_without_citations_is_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc:
            Recommendation(
                summary="Buy more",
                analysis="Price moved 5.2% in the last session.",
                confidence=ConfidenceLevel.HIGH,
            )
        assert "numeric content" in str(exc.value)
        assert "FM-11" in str(exc.value)

    def test_numeric_analysis_with_citations_passes(self) -> None:
        r = Recommendation(
            summary="Buy more",
            analysis="Price moved 5.2% in the last session.",
            confidence=ConfidenceLevel.HIGH,
            citations=[_citat("+5.2%")],
        )
        assert len(r.citations) == 1

    def test_digit_in_word_still_triggers_guard(self) -> None:
        # The contract uses a literal digit check. A digit anywhere in analysis
        # requires citations — this is the structural guard, not a parser.
        with pytest.raises(ValidationError):
            Recommendation(
                summary="x",
                analysis="v1 release notes",
                confidence=ConfidenceLevel.LOW,
            )

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            Recommendation(
                summary="x",
                analysis="Qualitative.",
                confidence=ConfidenceLevel.LOW,
                hidden=True,  # type: ignore[call-arg]
            )

    def test_rejects_blank_summary_or_analysis(self) -> None:
        with pytest.raises(ValidationError):
            Recommendation(summary="", analysis="x", confidence=ConfidenceLevel.LOW)
        with pytest.raises(ValidationError):
            Recommendation(summary="x", analysis="   ", confidence=ConfidenceLevel.LOW)

    def test_rejects_blank_list_items(self) -> None:
        with pytest.raises(ValidationError):
            Recommendation(
                summary="x",
                analysis="Qualitative.",
                confidence=ConfidenceLevel.LOW,
                risks=["ok", ""],
            )

    def test_round_trip_with_citation(self) -> None:
        r = Recommendation(
            summary="Hold",
            analysis="Sharpe ratio 0.8 over 3y.",
            confidence=ConfidenceLevel.MEDIUM,
            citations=[_citat("0.8")],
            risks=["volatility"],
            actions=["rebalance quarterly"],
            alternatives=["reduce exposure"],
            assumptions=["normal vol regime"],
            invalidation_conditions=["drawdown > 20%"],
        )
        r2 = Recommendation.model_validate_json(r.model_dump_json())
        assert r2 == r


# ---------------------------------------------------------------------------
# Finance value objects
# ---------------------------------------------------------------------------


class TestMoney:
    def test_valid_decimal(self) -> None:
        m = Money(amount="1234.56", currency="usd")
        assert m.amount == "1234.56"
        assert m.currency == "USD"  # upper-cased

    def test_rejects_invalid_decimal(self) -> None:
        with pytest.raises(ValidationError):
            Money(amount="not-a-number", currency="USD")

    def test_rejects_short_currency(self) -> None:
        with pytest.raises(ValidationError):
            Money(amount="1.00", currency="US")

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            Money(amount="1.00", currency="USD", extra="x")  # type: ignore[call-arg]

    def test_round_trip(self) -> None:
        m = Money(amount="0.01", currency="EUR")
        assert Money.model_validate_json(m.model_dump_json()) == m


class TestHolding:
    def test_minimal(self) -> None:
        h = Holding(symbol="AAPL", name="Apple Inc")
        assert h.domain is Domain.EQUITY
        assert h.horizon is Horizon.MEDIUM
        assert h.currency == "USD"
        assert h.market_value is None
        assert h.unrealized_pnl is None

    def test_market_value_and_pnl(self) -> None:
        h = Holding(
            symbol="AAPL",
            name="Apple",
            quantity=10,
            cost_basis=100.0,
            market_price=150.0,
            market_price_as_of=UTC_NOW,
        )
        assert h.market_value == 1500.0
        assert h.unrealized_pnl == 500.0

    def test_market_price_requires_as_of(self) -> None:
        with pytest.raises(ValidationError):
            Holding(symbol="AAPL", name="Apple", market_price=150.0)

    def test_rejects_naive_market_price_as_of(self) -> None:
        with pytest.raises(ValidationError):
            Holding(
                symbol="AAPL",
                name="Apple",
                market_price=150.0,
                market_price_as_of=datetime(2026, 1, 1),
            )

    def test_accepts_non_utc_aware_aware_datetime(self) -> None:
        # New York tz is converted to UTC.
        from datetime import timezone

        ny = timezone(timedelta(hours=-5))
        h = Holding(
            symbol="AAPL",
            name="Apple",
            market_price=150.0,
            market_price_as_of=datetime(2026, 1, 1, 9, 30, tzinfo=ny),
        )
        assert h.market_price_as_of.tzinfo is UTC

    def test_negative_quantity_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Holding(symbol="AAPL", name="Apple", quantity=-1)

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            Holding(symbol="AAPL", name="Apple", extra="x")  # type: ignore[call-arg]

    def test_round_trip(self) -> None:
        h = Holding(
            symbol="AAPL",
            name="Apple",
            quantity=2.5,
            market_price=200.0,
            market_price_as_of=UTC_NOW,
        )
        h2 = Holding.model_validate_json(h.model_dump_json())
        assert h2 == h


class TestPortfolio:
    def test_default_as_of_is_utc(self) -> None:
        p = Portfolio()
        assert p.as_of.tzinfo is UTC
        assert p.base_currency == "USD"

    def test_rejects_naive_as_of(self) -> None:
        with pytest.raises(ValidationError):
            Portfolio(as_of=datetime(2026, 1, 1))

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            Portfolio(bogus=1)  # type: ignore[call-arg]

    def test_round_trip(self) -> None:
        p = Portfolio(
            holdings=[Holding(symbol="AAPL", name="Apple", quantity=1)],
            base_currency="eur",
            as_of=UTC_NOW,
            notes="test",
        )
        p2 = Portfolio.model_validate_json(p.model_dump_json())
        assert p2 == p
        assert p2.base_currency == "EUR"


# ---------------------------------------------------------------------------
# AuditEvent
# ---------------------------------------------------------------------------


class TestAuditEvent:
    def test_minimal_valid(self) -> None:
        e = AuditEvent(
            ts=UTC_NOW,
            seq=0,
            type="task.dispatched",
            prev_hash=ZERO_HASH,
            hash=SAMPLE_HASH,
        )
        assert e.payload == {}
        assert e.seq == 0
        assert e.hash == SAMPLE_HASH  # normalized to lowercase

    def test_uppercase_hash_normalized(self) -> None:
        upper = ("A" * 32) + ("F" * 32)
        e = AuditEvent(
            ts=UTC_NOW,
            seq=1,
            type="tool.called",
            prev_hash=ZERO_HASH,
            hash=upper,
        )
        assert e.hash == upper.lower()

    def test_rejects_non_hex_hash(self) -> None:
        with pytest.raises(ValidationError):
            AuditEvent(
                ts=UTC_NOW,
                seq=0,
                type="x",
                prev_hash=ZERO_HASH,
                hash="z" * 64,  # not hex
            )

    def test_rejects_short_hash(self) -> None:
        with pytest.raises(ValidationError):
            AuditEvent(
                ts=UTC_NOW,
                seq=0,
                type="x",
                prev_hash=ZERO_HASH,
                hash="abc",
            )

    def test_rejects_naive_ts(self) -> None:
        with pytest.raises(ValidationError):
            AuditEvent(
                ts=datetime(2026, 1, 1),  # naive
                seq=0,
                type="x",
                prev_hash=ZERO_HASH,
                hash=SAMPLE_HASH,
            )

    def test_rejects_negative_seq(self) -> None:
        with pytest.raises(ValidationError):
            AuditEvent(
                ts=UTC_NOW,
                seq=-1,
                type="x",
                prev_hash=ZERO_HASH,
                hash=SAMPLE_HASH,
            )

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            AuditEvent(
                ts=UTC_NOW,
                seq=0,
                type="x",
                prev_hash=ZERO_HASH,
                hash=SAMPLE_HASH,
                tampered=True,  # type: ignore[call-arg]
            )

    def test_round_trip(self) -> None:
        e = AuditEvent(
            ts=UTC_NOW,
            seq=2,
            type="step.done",
            payload={"step": "router", "ok": True},
            prev_hash=SAMPLE_HASH,
            hash=ZERO_HASH,
        )
        e2 = AuditEvent.model_validate_json(e.model_dump_json())
        assert e2 == e


# ---------------------------------------------------------------------------
# AgentState
# ---------------------------------------------------------------------------


class TestAgentState:
    def test_minimal(self) -> None:
        s = AgentState(query="hi")
        assert s.query == "hi"
        assert s.intent is None
        assert s.twin_snapshot == {}
        assert s.plan == []
        assert s.tool_outputs == []
        assert s.candidate is None
        assert s.critique is None
        assert s.verifier_verdict is None
        assert s.final is None
        assert s.audit_events == []

    def test_round_trip(self) -> None:
        s = AgentState(
            query="what is my portfolio risk?",
            intent=Intent.RISK,
            plan=["twin.snapshot", "risk.compute"],
            tool_outputs=[{"name": "twin.snapshot", "ok": True}],
        )
        json = s.model_dump_json()
        s2 = AgentState.model_validate_json(json)
        assert s2.query == s.query
        assert s2.intent is Intent.RISK
        assert s2.plan == ["twin.snapshot", "risk.compute"]
        assert s2.tool_outputs == [{"name": "twin.snapshot", "ok": True}]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            AgentState(query="hi", unknown_field="x")  # type: ignore[call-arg]

    def test_carries_candidate_recommendation(self) -> None:
        r = Recommendation(
            summary="Hold",
            analysis="Qualitative note.",
            confidence=ConfidenceLevel.MEDIUM,
        )
        s = AgentState(query="hi", candidate=r)
        assert s.candidate == r
        s2 = AgentState.model_validate_json(s.model_dump_json())
        assert s2.candidate == r

    def test_carries_audit_events(self) -> None:
        e = AuditEvent(
            ts=UTC_NOW,
            seq=0,
            type="task.dispatched",
            prev_hash=ZERO_HASH,
            hash=SAMPLE_HASH,
        )
        s = AgentState(query="hi", audit_events=[e])
        s2 = AgentState.model_validate_json(s.model_dump_json())
        assert len(s2.audit_events) == 1
        assert s2.audit_events[0] == e


# ---------------------------------------------------------------------------
# Re-exports from the package root
# ---------------------------------------------------------------------------


class TestReExports:
    def test_all_public_names_importable_from_package(self) -> None:
        for name in [
            "AgentState",
            "AuditEvent",
            "Citation",
            "ConfidenceLevel",
            "Domain",
            "Holding",
            "Horizon",
            "Intent",
            "Money",
            "Portfolio",
            "Provider",
            "Recommendation",
            "RiskBand",
        ]:
            assert name in dir(__import__("finroot.schemas", fromlist=[name]))


# ---------------------------------------------------------------------------
# Acceptance one-liner: the exact string the task brief uses
# ---------------------------------------------------------------------------


class TestAcceptanceOneLiner:
    def test_task_brief_acceptance(self) -> None:
        # Mirrors the command in the task brief, tested in-process.
        s = AgentState(query="hi")
        out = AgentState.model_validate_json(s.model_dump_json())
        assert out.query == "hi"


# timezone import kept here so the file references the module (avoid lint
# complaints and document intent for future readers)
_ = timezone
