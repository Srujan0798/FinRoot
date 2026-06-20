"""Tests for new features: streaming, counterfactual, goal planner, FX, tracing.

Covers:
- stream_answer() yields status updates and result
- CounterfactualGenerator produces counterfactuals from assumptions/risks
- GoalPlannerTool calculates SIP, corpus, and allocation
- FxAwareAnalyzer assesses multi-currency risk
- Tracer creates and exports spans
- PDFIngestionTool parses mock PDF text
"""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from finroot.schemas.enums import ConfidenceLevel, Intent
from finroot.schemas.recommendation import Citation, Recommendation
from finroot.schemas.state import AgentState

# ---------------------------------------------------------------------------
# Streaming tests
# ---------------------------------------------------------------------------


class TestStreamAnswer:
    """Test stream_answer() generator."""

    def test_stream_yields_status_updates(self) -> None:
        """stream_answer should yield status dicts during pipeline execution."""
        from interface.core import stream_answer

        updates = list(stream_answer("What is my portfolio risk?", mock=True))

        # Should have at least status updates and a result
        status_updates = [u for u in updates if u["type"] == "status"]
        result_updates = [u for u in updates if u["type"] == "result"]

        assert len(status_updates) >= 3, f"Expected >=3 status updates, got {len(status_updates)}"
        assert len(result_updates) == 1, f"Expected 1 result, got {len(result_updates)}"

    def test_stream_result_is_agent_state(self) -> None:
        """stream_answer result should contain a valid AgentState."""
        from interface.core import stream_answer

        updates = list(stream_answer("What is my portfolio risk?", mock=True))
        result = next(u for u in updates if u["type"] == "result")

        assert isinstance(result["state"], AgentState)
        assert result["state"].query == "What is my portfolio risk?"

    def test_stream_empty_query_raises(self) -> None:
        """stream_answer with empty query should raise ValueError."""
        from interface.core import stream_answer

        with pytest.raises(ValueError, match="non-empty string"):
            list(stream_answer("", mock=True))


# ---------------------------------------------------------------------------
# Counterfactual tests
# ---------------------------------------------------------------------------


class TestCounterfactualGenerator:
    """Test CounterfactualGenerator."""

    def _make_state(self, assumptions: list[str] = None, risks: list[str] = None) -> AgentState:
        """Create a test AgentState with a recommendation."""
        rec = Recommendation(
            summary="Test recommendation",
            analysis="Test analysis with 12% expected return",
            risks=risks or [],
            actions=["Rebalance portfolio"],
            confidence=ConfidenceLevel.MEDIUM,
            citations=[Citation(
                source="test",
                detail="test citation",
                retrieved_at=datetime.now(UTC),
            )],
            assumptions=assumptions or [],
        )
        return AgentState(
            query="Test query",
            intent=Intent.PORTFOLIO,
            candidate=rec,
        )

    def test_from_assumptions_risk(self) -> None:
        """Should generate counterfactual from risk tolerance assumption."""
        from finroot.reasoning.counterfactual import CounterfactualGenerator

        state = self._make_state(assumptions=["Risk tolerance is moderate"])
        cfs = CounterfactualGenerator().generate(state)

        assert len(cfs) > 0
        assert any("risk" in cf.lower() for cf in cfs)

    def test_from_assumptions_horizon(self) -> None:
        """Should generate counterfactual from investment horizon assumption."""
        from finroot.reasoning.counterfactual import CounterfactualGenerator

        state = self._make_state(assumptions=["Investment horizon is 10 years"])
        cfs = CounterfactualGenerator().generate(state)

        assert len(cfs) > 0
        assert any("horizon" in cf.lower() for cf in cfs)

    def test_from_risks_concentration(self) -> None:
        """Should generate counterfactual from concentration risk."""
        from finroot.reasoning.counterfactual import CounterfactualGenerator

        state = self._make_state(risks=["High concentration in single stock"])
        cfs = CounterfactualGenerator().generate(state)

        assert len(cfs) > 0
        assert any("diversif" in cf.lower() for cf in cfs)

    def test_from_low_confidence(self) -> None:
        """Should generate counterfactual for low confidence recommendations."""
        from finroot.reasoning.counterfactual import CounterfactualGenerator

        rec = Recommendation(
            summary="Test",
            analysis="Test analysis",
            confidence=ConfidenceLevel.LOW,
            citations=[Citation(source="test", detail="test", retrieved_at=datetime.now(UTC))],
        )
        state = AgentState(query="Test", candidate=rec)
        cfs = CounterfactualGenerator().generate(state)

        assert len(cfs) > 0
        assert any("information" in cf.lower() or "confidence" in cf.lower() for cf in cfs)

    def test_no_recommendation_returns_empty(self) -> None:
        """Should return empty list when no recommendation exists."""
        from finroot.reasoning.counterfactual import CounterfactualGenerator

        state = AgentState(query="Test")
        cfs = CounterfactualGenerator().generate(state)

        assert cfs == []

    def test_deduplication(self) -> None:
        """Should deduplicate counterfactuals."""
        from finroot.reasoning.counterfactual import CounterfactualGenerator

        state = self._make_state(
            assumptions=["Risk tolerance is moderate", "Risk profile is moderate"]
        )
        cfs = CounterfactualGenerator().generate(state)

        # Should not have exact duplicates
        assert len(cfs) == len({cf.strip().lower() for cf in cfs})


# ---------------------------------------------------------------------------
# Goal Planner tests
# ---------------------------------------------------------------------------


class TestGoalPlannerTool:
    """Test GoalPlannerTool calculations."""

    def test_basic_goal_calculation(self) -> None:
        """Should calculate required SIP for a basic goal."""
        from finroot.tools.goal_planner import GoalInput, GoalPlannerTool

        tool = GoalPlannerTool(mock=True)
        inp = GoalInput(
            goal_name="Retirement",
            target_amount=5000000,  # ₹50L
            years_to_goal=20,
            expected_return=0.12,
            inflation_rate=0.06,
        )
        result = tool._run(inp)

        assert result.goal_name == "Retirement"
        assert result.required_monthly_sip > 0
        assert result.target_amount_future > result.target_amount_today
        assert result.inflation_adjusted is True

    def test_existing_corpus_reduces_sip(self) -> None:
        """Existing corpus should reduce required SIP."""
        from finroot.tools.goal_planner import GoalInput, GoalPlannerTool

        tool = GoalPlannerTool(mock=True)

        # Without existing corpus
        inp1 = GoalInput(
            goal_name="Education",
            target_amount=2000000,
            years_to_goal=15,
        )
        result1 = tool._run(inp1)

        # With existing corpus
        inp2 = GoalInput(
            goal_name="Education",
            target_amount=2000000,
            years_to_goal=15,
            existing_corpus=500000,
        )
        result2 = tool._run(inp2)

        assert result2.required_monthly_sip < result1.required_monthly_sip

    def test_allocation_by_risk_profile(self) -> None:
        """Allocation should differ by risk profile."""
        from finroot.tools.goal_planner import GoalInput, GoalPlannerTool

        tool = GoalPlannerTool(mock=True)

        conservative = tool._run(GoalInput(
            goal_name="Test", target_amount=1000000, years_to_goal=10,
            risk_profile="conservative",
        ))
        aggressive = tool._run(GoalInput(
            goal_name="Test", target_amount=1000000, years_to_goal=10,
            risk_profile="aggressive",
        ))

        assert conservative.recommended_allocation["equity"] < aggressive.recommended_allocation["equity"]

    def test_short_horizon_more_conservative(self) -> None:
        """Short time horizon should result in more conservative allocation."""
        from finroot.tools.goal_planner import GoalInput, GoalPlannerTool

        tool = GoalPlannerTool(mock=True)

        short = tool._run(GoalInput(
            goal_name="Test", target_amount=1000000, years_to_goal=3,
        ))
        long = tool._run(GoalInput(
            goal_name="Test", target_amount=1000000, years_to_goal=20,
        ))

        assert short.recommended_allocation["equity"] < long.recommended_allocation["equity"]


# ---------------------------------------------------------------------------
# FX Aware tests
# ---------------------------------------------------------------------------


class TestFxAwareAnalyzer:
    """Test FxAwareAnalyzer."""

    def test_single_currency_no_fx_risk(self) -> None:
        """INR-only portfolio should have zero FX risk."""
        from finroot.reasoning.fx_aware import FxAwareAnalyzer

        analyzer = FxAwareAnalyzer()
        holdings = [
            {"currency": "INR", "amount": 1000000, "symbol": "HDFC"},
        ]
        result = analyzer.analyze(holdings)

        assert result.fx_risk_score == 0.0
        assert result.hedging_recommended is False

    def test_multi_currency_has_fx_risk(self) -> None:
        """Multi-currency portfolio should have non-zero FX risk."""
        from finroot.reasoning.fx_aware import FxAwareAnalyzer

        analyzer = FxAwareAnalyzer()
        holdings = [
            {"currency": "INR", "amount": 500000},
            {"currency": "USD", "amount": 5000},
            {"currency": "EUR", "amount": 3000},
        ]
        result = analyzer.analyze(holdings)

        assert result.fx_risk_score > 0.0
        assert len(result.currency_exposures) == 3

    def test_usd_heavy_portfolio_warning(self) -> None:
        """USD-heavy portfolio should generate appropriate warning."""
        from finroot.reasoning.fx_aware import FxAwareAnalyzer

        analyzer = FxAwareAnalyzer()
        holdings = [
            {"currency": "USD", "amount": 10000},
            {"currency": "INR", "amount": 100000},
        ]
        result = analyzer.analyze(holdings)

        # USD should be dominant
        usd_exp = next(e for e in result.currency_exposures if e.currency == "USD")
        assert usd_exp.percentage > 50

    def test_empty_portfolio(self) -> None:
        """Empty portfolio should return empty analysis."""
        from finroot.reasoning.fx_aware import FxAwareAnalyzer

        analyzer = FxAwareAnalyzer()
        result = analyzer.analyze([])

        assert result.total_inr_value == 0.0
        assert result.fx_risk_score == 0.0


# ---------------------------------------------------------------------------
# Tracing tests
# ---------------------------------------------------------------------------


class TestTracer:
    """Test Tracer and Span."""

    def test_create_span(self) -> None:
        """Should create and manage spans."""
        from finroot.audit.tracing import Tracer

        tracer = Tracer("test")
        with tracer.start_span("test_span") as span:
            span.set_attribute("key", "value")

        assert len(tracer.spans) == 1
        assert tracer.spans[0].name == "test_span"
        assert tracer.spans[0].attributes["key"] == "value"
        assert tracer.spans[0].duration_ms is not None

    def test_nested_spans(self) -> None:
        """Should support nested spans with parent references."""
        from finroot.audit.tracing import Tracer

        tracer = Tracer("test")
        with tracer.start_span("parent") as parent, tracer.start_span("child") as child:
            child.set_attribute("level", 2)

        assert len(tracer.spans) == 2
        child_span = tracer.spans[1]
        assert child_span.parent_id == parent.span_id

    def test_exception_recording(self) -> None:
        """Should record exceptions on spans."""
        from finroot.audit.tracing import SpanStatus, Tracer

        tracer = Tracer("test")
        with pytest.raises(ValueError), tracer.start_span("failing") as span:
            raise ValueError("test error")

        assert span.status == SpanStatus.ERROR
        assert any(e["name"] == "exception" for e in span.events)

    def test_export_jsonl(self) -> None:
        """Should export spans to JSONL file."""
        from finroot.audit.tracing import Tracer

        tracer = Tracer("test")
        with tracer.start_span("span1"):
            pass
        with tracer.start_span("span2"):
            pass

        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name

        tracer.export_jsonl(path)

        lines = Path(path).read_text().strip().split("\n")
        assert len(lines) == 2
        for line in lines:
            data = json.loads(line)
            assert "span_id" in data
            assert "trace_id" in data

    def test_get_summary(self) -> None:
        """Should return trace summary."""
        from finroot.audit.tracing import Tracer

        tracer = Tracer("test")
        with tracer.start_span("span1"):
            pass

        summary = tracer.get_summary()
        assert summary["span_count"] == 1
        assert summary["total_duration_ms"] >= 0


# ---------------------------------------------------------------------------
# PDF Ingestion tests
# ---------------------------------------------------------------------------


class TestPDFIngestion:
    """Test PDFIngestionTool."""

    def test_mock_pdf_parsing(self) -> None:
        """Should parse mock PDF text and extract holdings."""
        from finroot.tools.pdf_ingestion import PDFIngestionTool

        tool = PDFIngestionTool(mock=True)

        # Test the mock text parsing directly
        mock_text = tool._mock_pdf_text()
        holdings, account_info = tool._parse_cdsl_cas(mock_text)

        assert len(holdings) > 0
        assert all(h.market_value >= 0 for h in holdings)

    def test_holding_model(self) -> None:
        """Holding model should validate correctly."""
        from finroot.tools.pdf_ingestion import Holding

        h = Holding(
            symbol="RELIANCE",
            name="Reliance Industries",
            asset_class="equity",
            quantity=100,
            unit_price=2500.0,
            market_value=250000.0,
            confidence=0.9,
        )

        assert h.symbol == "RELIANCE"
        assert h.confidence == 0.9

    def test_build_twin_from_ingestion(self) -> None:
        """Should build Digital Twin dict from ingestion output."""
        from finroot.tools.pdf_ingestion import (
            Holding,
            PDFIngestionOutput,
            build_twin_from_ingestion,
        )

        output = PDFIngestionOutput(
            holdings=[
                Holding(
                    symbol="TEST",
                    name="Test Fund",
                    asset_class="mutual_fund",
                    quantity=100,
                    unit_price=100.0,
                    market_value=10000.0,
                    confidence=0.8,
                ),
            ],
            account_info={},
            total_value=10000.0,
            statement_type="amc",
            extraction_confidence=0.8,
            warnings=[],
            raw_text_preview="test",
            citation="test",
        )

        twin = build_twin_from_ingestion(output, user_id="test_user", name="Test User")

        assert twin["user_id"] == "test_user"
        assert len(twin["holdings"]) == 1
        assert twin["holdings"][0]["symbol"] == "TEST"


# ---------------------------------------------------------------------------
# Agreement study tests
# ---------------------------------------------------------------------------


class TestAgreementStudy:
    """Test grader agreement calculations."""

    def test_perfect_agreement(self) -> None:
        """Perfect agreement should give kappa = 1.0."""
        from evals.graders.agreement_study import calculate_cohens_kappa

        passes = [True, True, False, False, True]
        kappa = calculate_cohens_kappa(passes, passes)

        assert kappa == 1.0

    def test_no_agreement(self) -> None:
        """No agreement should give low kappa."""
        from evals.graders.agreement_study import calculate_cohens_kappa

        a = [True, True, True, True]
        b = [False, False, False, False]
        kappa = calculate_cohens_kappa(a, b)

        # When there's complete disagreement, kappa should be <= 0
        assert kappa <= 0

    def test_score_correlation(self) -> None:
        """Identical scores should give correlation = 1.0."""
        from evals.graders.agreement_study import calculate_score_correlation

        scores = [0.1, 0.3, 0.5, 0.7, 0.9]
        corr = calculate_score_correlation(scores, scores)

        assert abs(corr - 1.0) < 0.001

    def test_report_generation(self) -> None:
        """Should generate a valid calibration report."""
        from evals.graders.agreement_study import (
            AgreementMetrics,
            generate_report,
        )

        metrics = AgreementMetrics(
            grader_a="code",
            grader_b="llm_judge",
            total_tasks=10,
            agreement_count=8,
            agreement_pct=0.8,
            cohens_kappa=0.6,
            score_correlation=0.75,
            disagreements=[],
        )

        report = generate_report(metrics)

        assert "title" in report
        assert "agreements" in report
        assert "recommendations" in report
        assert report["summary"]["total_tasks"] == 10
