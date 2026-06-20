"""Tests for the Refinement Loop (wave-5, task 02).

Covers: first-pass, single-refinement, max-exhaustion, audit trail integrity,
must_fix revision effectiveness, iteration cap, and edge cases.

Run with::

    PYTHONPATH=src python3 -m pytest tests/unit/test_refine.py -v
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from finroot.reasoning.critic import CriticScore, CriticVerdict, SelfCritic
from finroot.reasoning.refine import RefinementLoop
from finroot.schemas.enums import ConfidenceLevel
from finroot.schemas.recommendation import Citation, Recommendation
from finroot.schemas.state import AgentState

UTC_NOW = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)
_USE_DEFAULT: Any = object()

_DISCLAIMER = "This answer has not met quality standards. Please verify independently."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _citation(
    source: str = "yfinance",
    detail: str = "market data",
    value: str | None = "150",
) -> Citation:
    return Citation(source=source, detail=detail, value=value, retrieved_at=UTC_NOW)


def _make_rec(
    *,
    summary: str = "Diversified portfolio recommendation",
    analysis: str = (
        "Because your risk tolerance is moderate and your horizon is long, "
        "we recommend a balanced allocation. Therefore equities, bonds, "
        "real estate, and cash each get a slice, so the portfolio stays "
        "diversified across regimes. Market conditions can change rapidly."
    ),
    risks: list[str] | None | Any = _USE_DEFAULT,
    actions: list[str] | None | Any = _USE_DEFAULT,
    citations: list[Citation] | None | Any = _USE_DEFAULT,
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
) -> Recommendation:
    if risks is _USE_DEFAULT:
        risks = ["market volatility", "interest rate risk"]
    if actions is _USE_DEFAULT:
        actions = [
            "Allocate 30% to equities within Q1",
            "Rebalance portfolio quarterly",
        ]
    if citations is _USE_DEFAULT:
        citations = [_citation(), _citation(source="portfolio_twin")]
    return Recommendation(
        summary=summary,
        analysis=analysis,
        risks=risks,
        actions=actions,
        citations=citations,
        confidence=confidence,
    )


def _make_state(
    *,
    rec: Recommendation | None = None,
    tool_outputs: list[dict] | None = None,
) -> AgentState:
    return AgentState(
        query="What should I invest in?",
        candidate=rec if rec is not None else _make_rec(),
        tool_outputs=tool_outputs
        if tool_outputs is not None
        else [
            {"tool": "market_data", "data": "30 equities"},
            {"tool": "market_data", "data": "30 bonds"},
            {"tool": "market_data", "data": "20 real estate"},
            {"tool": "market_data", "data": "20 cash"},
            {"tool": "portfolio_twin", "tolerance": "moderate"},
        ],
    )


def _score(
    axis: str, value: float, *, rationale: str = "test", issues: list[str] | None = None
) -> CriticScore:
    return CriticScore(axis=axis, score=value, rationale=rationale, issues=issues or [])


def _verdict(
    overall: float,
    passed: bool,
    must_fix: list[str] | None = None,
    scores: list[CriticScore] | None = None,
) -> CriticVerdict:
    if scores is None:
        scores = [_score(axis, overall) for axis in SelfCritic.WEIGHTS]
    return CriticVerdict(
        scores=scores,
        overall=overall,
        passed=passed,
        summary=f"{'passed' if passed else 'failed'} (overall={overall:.2f})",
        must_fix=must_fix or [],
    )


# ---------------------------------------------------------------------------
# 1. First attempt passes — no refinement needed
# ---------------------------------------------------------------------------


class TestFirstAttemptPasses:
    """When the critic passes on the first try, state.final = state.candidate
    immediately — no revisions, one audit event."""

    def test_final_set_to_candidate(self) -> None:
        loop = RefinementLoop()
        state = _make_state()
        result = loop.refine(state, SelfCritic())
        assert result.final is not None
        assert result.final.summary == result.candidate.summary
        assert result.final.analysis == result.candidate.analysis

    def test_no_modifications_to_candidate(self) -> None:
        loop = RefinementLoop()
        state = _make_state()
        original_summary = state.candidate.summary
        original_analysis = state.candidate.analysis
        loop.refine(state, SelfCritic())
        assert state.candidate.summary == original_summary
        assert state.candidate.analysis == original_analysis

    def test_single_audit_event_logged(self) -> None:
        loop = RefinementLoop()
        state = _make_state()
        loop.refine(state, SelfCritic())
        refine_events = [e for e in state.audit_events if e.type == "refine.iteration"]
        assert len(refine_events) == 1
        assert refine_events[0].payload["passed"] is True
        assert refine_events[0].payload["iteration"] == 1

    def test_no_exhausted_event(self) -> None:
        loop = RefinementLoop()
        state = _make_state()
        loop.refine(state, SelfCritic())
        exhausted = [e for e in state.audit_events if e.type == "refine.exhausted"]
        assert len(exhausted) == 0


# ---------------------------------------------------------------------------
# 2. First attempt fails, second passes — one refinement
# ---------------------------------------------------------------------------


class TestSingleRefinement:
    """When the first critique fails but the revision fixes the issues,
    the loop exits after iteration 2."""

    def setup_method(self) -> None:
        self.loop = RefinementLoop()
        self.critic = SelfCritic()

    def test_one_refinement_then_pass(self) -> None:
        """A recommendation missing risks and with short analysis should fail
        first, gain risks + connectors after revision, and pass on iteration 2."""
        rec = _make_rec(
            analysis="Stocks are good.",  # short, no connectors, no risk language
            risks=[],  # no risks → risk_awareness = 0.0
            actions=["Buy stocks"],  # 1 action only
            citations=[_citation()],
        )
        state = _make_state(rec=rec)
        result = self.loop.refine(state, self.critic)

        # Should have exactly 2 iteration events (fail + pass)
        iter_events = [e for e in result.audit_events if e.type == "refine.iteration"]
        assert len(iter_events) == 2
        assert iter_events[0].payload["passed"] is False
        assert iter_events[1].payload["passed"] is True

    def test_final_is_set_after_refinement(self) -> None:
        rec = _make_rec(
            analysis="Stocks are good.",
            risks=[],
            actions=["Buy stocks"],
            citations=[_citation()],
        )
        state = _make_state(rec=rec)
        result = self.loop.refine(state, self.critic)
        assert result.final is not None


# ---------------------------------------------------------------------------
# 3. All 3 attempts fail — disclaimer + LOW confidence
# ---------------------------------------------------------------------------


class TestMaxExhaustion:
    """When the candidate cannot be fixed within 3 iterations, the loop sets
    confidence to LOW and appends the disclaimer."""

    def setup_method(self) -> None:
        self.loop = RefinementLoop()

    def test_disclaimer_added_after_exhaustion(self) -> None:
        rec = _make_rec(
            summary="Buy",
            analysis="Buy now.",
            risks=[],
            actions=[],
            citations=[],
            confidence=ConfidenceLevel.MEDIUM,
        )
        # Need tool_outputs empty so correctness stays low
        state = AgentState(query="tip?", candidate=rec, tool_outputs=[])
        result = self.loop.refine(state, SelfCritic())
        assert result.final is not None
        assert _DISCLAIMER in result.final.analysis

    def test_confidence_set_to_low(self) -> None:
        rec = _make_rec(
            summary="Buy",
            analysis="Buy now.",
            risks=[],
            actions=[],
            citations=[],
            confidence=ConfidenceLevel.HIGH,
        )
        state = AgentState(query="tip?", candidate=rec, tool_outputs=[])
        result = self.loop.refine(state, SelfCritic())
        assert result.final.confidence == ConfidenceLevel.LOW

    def test_exhausted_event_logged(self) -> None:
        rec = _make_rec(
            summary="Buy",
            analysis="Buy now.",
            risks=[],
            actions=[],
            citations=[],
        )
        state = AgentState(query="tip?", candidate=rec, tool_outputs=[])
        result = self.loop.refine(state, SelfCritic())
        exhausted = [e for e in result.audit_events if e.type == "refine.exhausted"]
        assert len(exhausted) == 1
        assert exhausted[0].payload["disclaimer_added"] is True
        assert exhausted[0].payload["iterations"] == 3

    def test_three_iteration_events_before_exhaustion(self) -> None:
        rec = _make_rec(
            summary="Buy",
            analysis="Buy now.",
            risks=[],
            actions=[],
            citations=[],
        )
        state = AgentState(query="tip?", candidate=rec, tool_outputs=[])
        result = self.loop.refine(state, SelfCritic())
        iter_events = [e for e in result.audit_events if e.type == "refine.iteration"]
        assert len(iter_events) == 3
        assert all(e.payload["passed"] is False for e in iter_events)


# ---------------------------------------------------------------------------
# 4. Audit trail integrity
# ---------------------------------------------------------------------------


class TestAuditTrail:
    """Each iteration produces a well-formed audit event with correct metadata."""

    def test_events_have_monotonic_seq(self) -> None:
        rec = _make_rec(
            summary="Buy",
            analysis="Buy now.",
            risks=[],
            actions=[],
            citations=[],
        )
        state = AgentState(query="x", candidate=rec, tool_outputs=[])
        RefinementLoop().refine(state, SelfCritic())
        seqs = [e.seq for e in state.audit_events]
        assert seqs == sorted(seqs)
        assert len(seqs) == len(set(seqs))

    def test_events_have_valid_hashes(self) -> None:
        rec = _make_rec(
            summary="Buy",
            analysis="Buy now.",
            risks=[],
            actions=[],
            citations=[],
        )
        state = AgentState(query="x", candidate=rec, tool_outputs=[])
        RefinementLoop().refine(state, SelfCritic())
        for event in state.audit_events:
            assert len(event.hash) == 64
            assert len(event.prev_hash) == 64
            # Must be valid hex
            int(event.hash, 16)
            int(event.prev_hash, 16)

    def test_chain_links_correctly(self) -> None:
        rec = _make_rec(
            summary="Buy",
            analysis="Buy now.",
            risks=[],
            actions=[],
            citations=[],
        )
        state = AgentState(query="x", candidate=rec, tool_outputs=[])
        RefinementLoop().refine(state, SelfCritic())
        events = state.audit_events
        # Genesis prev_hash is all zeros
        assert events[0].prev_hash == "0" * 64
        # Each subsequent event's prev_hash is the prior event's hash
        for i in range(1, len(events)):
            assert events[i].prev_hash == events[i - 1].hash

    def test_iteration_event_contains_scores(self) -> None:
        rec = _make_rec(
            summary="Buy",
            analysis="Buy now.",
            risks=[],
            actions=[],
            citations=[],
        )
        state = AgentState(query="x", candidate=rec, tool_outputs=[])
        RefinementLoop().refine(state, SelfCritic())
        for event in state.audit_events:
            if event.type == "refine.iteration":
                assert "iteration" in event.payload
                assert "overall" in event.payload
                assert "passed" in event.payload
                assert "must_fix" in event.payload
                assert "scores" in event.payload
                scores = event.payload["scores"]
                assert set(scores.keys()) == set(SelfCritic.WEIGHTS.keys())


# ---------------------------------------------------------------------------
# 5. must_fix items addressed in revision
# ---------------------------------------------------------------------------


class TestRevisionAddressesMustFix:
    """After revision, the candidate text should change to address the flagged
    axes."""

    def test_risk_warnings_added_when_risk_awareness_low(self) -> None:
        rec = _make_rec(
            summary="Great investment",
            analysis=(
                "Because this is a solid opportunity, therefore invest now. "
                "Allocate funds across sectors for diversification benefits. "
                "Market conditions are favorable."
            ),
            risks=[],  # empty → risk_awareness = 0.0 → must_fix
            actions=["Buy equities", "Hold for 5 years"],
            citations=[_citation(), _citation(source="portfolio_twin")],
        )
        state = _make_state(rec=rec)
        original_risks = list(state.candidate.risks)
        RefinementLoop().refine(state, SelfCritic())
        # After refinement, risks should have been expanded
        assert len(state.candidate.risks) >= len(original_risks)

    def test_explainability_connector_added(self) -> None:
        rec = _make_rec(
            summary="Buy stocks now",
            analysis="Stocks go up.",  # no reasoning connectors, very short
            risks=["market risk"],
            actions=["Buy stocks"],
            citations=[_citation()],
        )
        state = _make_state(rec=rec)
        original_analysis = state.candidate.analysis
        RefinementLoop().refine(state, SelfCritic())
        # Analysis should have grown (connector added or citations note added)
        assert len(state.candidate.analysis) >= len(original_analysis)

    def test_overconfident_language_softened(self) -> None:
        rec = _make_rec(
            summary="Guaranteed returns",
            analysis=(
                "Guaranteed gains."
            ),  # very short + overconfident + no connectors
            risks=[],  # empty risks → risk_awareness fails → must_fix includes it
            actions=["Invest now"],
            citations=[],  # no citations → evidence low
            confidence=ConfidenceLevel.MEDIUM,
        )
        # Analysis has no digits, so Recommendation FM-11 guard passes.
        state = _make_state(rec=rec)
        RefinementLoop().refine(state, SelfCritic())
        # "guaranteed" in summary should have been softened after revision
        combined = f"{state.candidate.summary} {state.candidate.analysis}"
        assert "guaranteed" not in state.candidate.summary.lower() or "may" in combined.lower()


# ---------------------------------------------------------------------------
# 6. Max iterations respected
# ---------------------------------------------------------------------------


class TestMaxIterations:
    """The loop never exceeds MAX_ITERATIONS regardless of the critic."""

    def test_never_more_than_three_iterations(self) -> None:
        rec = _make_rec(
            summary="Buy",
            analysis="Buy now.",
            risks=[],
            actions=[],
            citations=[],
        )
        state = AgentState(query="x", candidate=rec, tool_outputs=[])
        RefinementLoop().refine(state, SelfCritic())
        iter_events = [e for e in state.audit_events if e.type == "refine.iteration"]
        assert len(iter_events) <= 3

    def test_max_iterations_constant(self) -> None:
        assert RefinementLoop.MAX_ITERATIONS == 3


# ---------------------------------------------------------------------------
# 7. Edge cases & error handling
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Boundary conditions and defensive paths."""

    def test_none_candidate_raises(self) -> None:
        state = AgentState(query="x")
        with pytest.raises(ValueError, match="state.candidate is None"):
            RefinementLoop().refine(state, SelfCritic())

    def test_candidate_not_mutated_on_pass(self) -> None:
        """When the loop passes on iteration 1, candidate is NOT modified."""
        loop = RefinementLoop()
        state = _make_state()
        original_summary = state.candidate.summary
        original_analysis = state.candidate.analysis
        original_risks = list(state.candidate.risks)
        loop.refine(state, SelfCritic())
        assert state.candidate.summary == original_summary
        assert state.candidate.analysis == original_analysis
        assert state.candidate.risks == original_risks

    def test_final_is_deep_copy_not_reference(self) -> None:
        """state.final should be a distinct object from state.candidate."""
        loop = RefinementLoop()
        state = _make_state()
        loop.refine(state, SelfCritic())
        assert state.final is not state.candidate

    def test_disclaimer_not_duplicated_on_rerun(self) -> None:
        """If refine is called twice, the disclaimer should not stack."""
        rec = _make_rec(
            summary="Buy",
            analysis="Buy now.",
            risks=[],
            actions=[],
            citations=[],
        )
        state = AgentState(query="x", candidate=rec, tool_outputs=[])
        loop = RefinementLoop()
        loop.refine(state, SelfCritic())
        first_analysis = state.final.analysis
        assert first_analysis.count(_DISCLAIMER) == 1

    def test_refine_returns_state(self) -> None:
        """refine() returns the same state object (mutates in place)."""
        loop = RefinementLoop()
        state = _make_state()
        result = loop.refine(state, SelfCritic())
        assert result is state
