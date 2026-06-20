"""Tests for the Self-Critic (wave-5, task 01).

Covers all 5 axes (correctness, risk-awareness, actionability, explainability,
evidence) plus the threshold boundary, the must_fix rule, the weight invariant,
and the HALL_OF_SHAME seed cases from the reasoning contract.

Run with::

    PYTHONPATH=src python3 -m pytest tests/unit/test_critic.py -v
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from finroot.reasoning.critic import (
    AXES,
    CriticScore,
    CriticVerdict,
    SelfCritic,
)
from finroot.schemas.enums import ConfidenceLevel
from finroot.schemas.recommendation import Citation, Recommendation
from finroot.schemas.state import AgentState

UTC_NOW = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)

# Sentinel distinguishing "use default" from "explicitly empty list".
_USE_DEFAULT: Any = object()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _citation(
    source: str = "yfinance",
    detail: str = "market data",
    value: str | None = "150",
) -> Citation:
    return Citation(
        source=source,
        detail=detail,
        value=value,
        retrieved_at=UTC_NOW,
    )


def _make_rec(
    *,
    summary: str = "Diversified portfolio recommendation",
    analysis: str = (
        "Because your risk tolerance is moderate and your horizon is long, "
        "we recommend a balanced allocation. Therefore equities, bonds, "
        "real estate, and cash each get a slice, so the portfolio stays "
        "diversified across regimes."
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
    return CriticScore(
        axis=axis, score=value, rationale=rationale, issues=issues or []
    )


# ---------------------------------------------------------------------------
# 1. Class-level invariants
# ---------------------------------------------------------------------------


class TestSelfCriticConstants:
    """Class-level constants define the contract — they must not drift."""

    def test_weights_sum_to_one(self) -> None:
        assert sum(SelfCritic.WEIGHTS.values()) == pytest.approx(1.0, abs=1e-9)

    def test_weights_match_axes(self) -> None:
        assert set(SelfCritic.WEIGHTS.keys()) == set(AXES)

    def test_threshold_is_six_tenths(self) -> None:
        assert SelfCritic.THRESHOLD == 0.6

    def test_must_fix_threshold_is_half(self) -> None:
        assert SelfCritic.MUST_FIX_THRESHOLD == 0.5

    def test_axes_order(self) -> None:
        assert AXES == (
            "correctness",
            "risk_awareness",
            "actionability",
            "explainability",
            "evidence",
        )

    def test_weights_have_correct_values(self) -> None:
        """The contract specifies the exact weights — they are a contract."""
        assert SelfCritic.WEIGHTS == {
            "correctness": 0.30,
            "risk_awareness": 0.25,
            "actionability": 0.20,
            "explainability": 0.15,
            "evidence": 0.10,
        }


# ---------------------------------------------------------------------------
# 2. Good recommendation — should pass with high overall
# ---------------------------------------------------------------------------


class TestGoodRecommendation:
    """A well-formed recommendation with risks, actions, citations, and tool
    outputs that back its numeric claims should pass the gate with high
    overall."""

    def setup_method(self) -> None:
        self.critic = SelfCritic()
        self.state = _make_state()

    def test_good_rec_passes(self) -> None:
        verdict = self.critic.evaluate(self.state)
        assert verdict.passed is True

    def test_good_rec_overall_above_threshold(self) -> None:
        verdict = self.critic.evaluate(self.state)
        assert verdict.overall > 0.7

    def test_good_rec_has_five_scores(self) -> None:
        verdict = self.critic.evaluate(self.state)
        assert len(verdict.scores) == 5
        assert [s.axis for s in verdict.scores] == list(AXES)

    def test_good_rec_must_fix_empty(self) -> None:
        verdict = self.critic.evaluate(self.state)
        assert verdict.must_fix == []

    def test_good_rec_summary_says_passed(self) -> None:
        verdict = self.critic.evaluate(self.state)
        assert "passed" in verdict.summary.lower()


# ---------------------------------------------------------------------------
# 3. Bad recommendation — "Buy RELIANCE" with no reasoning
# ---------------------------------------------------------------------------


class TestBadRecommendation:
    """HALL_OF_SHAME seed case: 'Buy RELIANCE' with no reasoning, no risks,
    no actions, no citations. Should fail every axis except correctness
    (which defaults to 0.8 when no numbers are present)."""

    def setup_method(self) -> None:
        self.critic = SelfCritic()
        self.rec = _make_rec(
            summary="Buy RELIANCE",
            analysis="Buy RELIANCE stock.",
            risks=[],
            actions=[],
            citations=[],
        )
        self.state = AgentState(
            query="What should I buy?",
            candidate=self.rec,
            tool_outputs=[],
        )

    def test_bad_rec_fails(self) -> None:
        verdict = self.critic.evaluate(self.state)
        assert verdict.passed is False

    def test_bad_rec_explainability_below_threshold(self) -> None:
        verdict = self.critic.evaluate(self.state)
        explain = next(s for s in verdict.scores if s.axis == "explainability")
        assert explain.score < 0.3

    def test_bad_rec_evidence_below_threshold(self) -> None:
        verdict = self.critic.evaluate(self.state)
        evidence = next(s for s in verdict.scores if s.axis == "evidence")
        assert evidence.score < 0.3

    def test_bad_rec_actionability_below_threshold(self) -> None:
        verdict = self.critic.evaluate(self.state)
        action = next(s for s in verdict.scores if s.axis == "actionability")
        assert action.score < 0.3

    def test_bad_rec_risk_awareness_below_threshold(self) -> None:
        verdict = self.critic.evaluate(self.state)
        risk = next(s for s in verdict.scores if s.axis == "risk_awareness")
        assert risk.score < 0.3

    def test_bad_rec_must_fix_populated(self) -> None:
        verdict = self.critic.evaluate(self.state)
        assert len(verdict.must_fix) >= 3
        assert "risk_awareness" in verdict.must_fix
        assert "actionability" in verdict.must_fix
        assert "explainability" in verdict.must_fix
        assert "evidence" in verdict.must_fix


# ---------------------------------------------------------------------------
# 4. Risky recommendation — no risk warnings
# ---------------------------------------------------------------------------


class TestRiskyRecommendation:
    """A recommendation that is structured but ignores risks entirely."""

    def setup_method(self) -> None:
        self.critic = SelfCritic()
        self.rec = _make_rec(
            summary="Diversified portfolio recommendation",
            analysis=(
                "Allocate 30% to equities, 30% to bonds, 20% to real estate, "
                "20% to cash."
            ),
            risks=[],
            actions=[
                "Allocate 30% to equities within Q1",
                "Rebalance portfolio quarterly",
            ],
            citations=[_citation(), _citation(source="portfolio_twin")],
        )
        self.state = AgentState(
            query="x",
            candidate=self.rec,
            tool_outputs=[
                {"tool": "market_data", "data": "30"},
                {"tool": "portfolio_twin", "tolerance": "moderate"},
            ],
        )

    def test_risk_awareness_below_four_tenths(self) -> None:
        verdict = self.critic.evaluate(self.state)
        risk = next(s for s in verdict.scores if s.axis == "risk_awareness")
        assert risk.score < 0.4

    def test_risk_awareness_in_must_fix(self) -> None:
        verdict = self.critic.evaluate(self.state)
        assert "risk_awareness" in verdict.must_fix


# ---------------------------------------------------------------------------
# 5. Hallucinated numbers — numbers not backed by tool outputs
# ---------------------------------------------------------------------------


class TestHallucinatedNumbers:
    """Numbers in the answer must be findable in tool_outputs."""

    def setup_method(self) -> None:
        self.critic = SelfCritic()
        self.rec = _make_rec(
            summary="Stock pick",
            analysis="AAPL at 250 is a strong buy at 280.",
            citations=[_citation(source="news", value="unknown")],
        )
        self.state = AgentState(
            query="What about AAPL?",
            candidate=self.rec,
            tool_outputs=[{"tool": "different", "data": "200"}],
        )

    def test_correctness_below_four_tenths(self) -> None:
        verdict = self.critic.evaluate(self.state)
        correct = next(s for s in verdict.scores if s.axis == "correctness")
        assert correct.score < 0.4

    def test_correctness_lists_missing_numbers_as_issues(self) -> None:
        verdict = self.critic.evaluate(self.state)
        correct = next(s for s in verdict.scores if s.axis == "correctness")
        assert any("250" in issue for issue in correct.issues)
        assert any("280" in issue for issue in correct.issues)

    def test_uncertainty_drops_correctness_below_three_tenths(self) -> None:
        """The HALL_OF_SHAME 'I don't know but here's a stock tip' case."""
        rec = _make_rec(
            summary="Stock tip",
            analysis="I don't know but here's a stock tip, AAPL at 250.",
            citations=[_citation(source="news", value="unknown")],
        )
        state = AgentState(query="tip?", candidate=rec, tool_outputs=[])
        verdict = self.critic.evaluate(state)
        correct = next(s for s in verdict.scores if s.axis == "correctness")
        assert correct.score < 0.3


# ---------------------------------------------------------------------------
# 6. Missing citations — evidence should be low
# ---------------------------------------------------------------------------


class TestMissingCitations:
    """No citations attached. Analysis must not contain digits (otherwise the
    Recommendation's structural FM-11 guard would block construction)."""

    def setup_method(self) -> None:
        self.critic = SelfCritic()
        self.rec = _make_rec(
            summary="Recommendation",
            analysis="Buy stocks now.",  # no digits → no citation required
            risks=["market risk"],
            actions=["Buy stocks"],
            citations=[],
        )
        self.state = AgentState(
            query="What should I do?",
            candidate=self.rec,
            tool_outputs=[{"tool": "market_data"}],
        )

    def test_evidence_below_four_tenths(self) -> None:
        verdict = self.critic.evaluate(self.state)
        evidence = next(s for s in verdict.scores if s.axis == "evidence")
        assert evidence.score < 0.4

    def test_evidence_in_must_fix(self) -> None:
        verdict = self.critic.evaluate(self.state)
        assert "evidence" in verdict.must_fix


# ---------------------------------------------------------------------------
# 7. Threshold boundary — 0.59 fails, 0.60 passes
# ---------------------------------------------------------------------------


class TestThresholdBoundary:
    """The contract says ``passed = overall >= THRESHOLD``. We verify both the
    constant math and the integration path via monkeypatched scorer."""

    def setup_method(self) -> None:
        self.critic = SelfCritic()
        self.state = AgentState(query="x", candidate=_make_rec())

    @staticmethod
    def _uniform_axes(target: float) -> list[CriticScore]:
        return [
            _score(axis, target, rationale="forced for test") for axis in AXES
        ]

    def test_threshold_math_059_is_below(self) -> None:
        assert SelfCritic.THRESHOLD > 0.59

    def test_threshold_math_060_is_at_or_above(self) -> None:
        assert SelfCritic.THRESHOLD <= 0.60

    def test_overall_059_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            self.critic, "_score_axes", lambda state, rec: self._uniform_axes(0.59)
        )
        verdict = self.critic.evaluate(self.state)
        assert verdict.overall == pytest.approx(0.59, abs=1e-9)
        assert verdict.passed is False

    def test_overall_060_passes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            self.critic, "_score_axes", lambda state, rec: self._uniform_axes(0.60)
        )
        verdict = self.critic.evaluate(self.state)
        assert verdict.overall == pytest.approx(0.60, abs=1e-9)
        assert verdict.passed is True

    def test_overall_computation_uses_weights(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Mix weights and verify the overall math directly."""
        per_axis = {
            "correctness": 1.0,
            "risk_awareness": 0.0,
            "actionability": 1.0,
            "explainability": 0.0,
            "evidence": 1.0,
        }
        scores = [
            _score(axis, value, rationale="weighted-sum test")
            for axis, value in per_axis.items()
        ]
        monkeypatch.setattr(self.critic, "_score_axes", lambda state, rec: scores)
        verdict = self.critic.evaluate(self.state)
        expected = 0.30 * 1.0 + 0.25 * 0.0 + 0.20 * 1.0 + 0.15 * 0.0 + 0.10 * 1.0
        assert verdict.overall == pytest.approx(expected, abs=1e-9)
        assert verdict.passed is True  # 0.60 exactly

    def test_overall_just_below_threshold_fails(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """0.5999 must fail."""
        scores = self._uniform_axes(0.5999)
        monkeypatch.setattr(self.critic, "_score_axes", lambda state, rec: scores)
        verdict = self.critic.evaluate(self.state)
        assert verdict.overall < 0.6
        assert verdict.passed is False


# ---------------------------------------------------------------------------
# 8. must_fix population
# ---------------------------------------------------------------------------


class TestMustFix:
    """must_fix must list every axis whose score dropped below MUST_FIX_THRESHOLD."""

    def test_must_fix_lists_all_sub_half_axes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        critic = SelfCritic()
        scores = [
            _score("correctness", 0.9),
            _score("risk_awareness", 0.4),
            _score("actionability", 0.49),
            _score("explainability", 0.5),
            _score("evidence", 0.2),
        ]
        monkeypatch.setattr(critic, "_score_axes", lambda state, rec: scores)
        state = AgentState(query="x", candidate=_make_rec())
        verdict = critic.evaluate(state)
        assert set(verdict.must_fix) == {
            "risk_awareness",
            "actionability",
            "evidence",
        }

    def test_must_fix_excludes_axes_at_threshold(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """0.5 exactly is the threshold — must_fix excludes it (strict <)."""
        critic = SelfCritic()
        scores = [_score(axis, 0.5) for axis in AXES]
        monkeypatch.setattr(critic, "_score_axes", lambda state, rec: scores)
        state = AgentState(query="x", candidate=_make_rec())
        verdict = critic.evaluate(state)
        assert verdict.must_fix == []

    def test_must_fix_excludes_axes_above_threshold(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        critic = SelfCritic()
        scores = [_score(axis, 0.6) for axis in AXES]
        monkeypatch.setattr(critic, "_score_axes", lambda state, rec: scores)
        state = AgentState(query="x", candidate=_make_rec())
        verdict = critic.evaluate(state)
        assert verdict.must_fix == []


# ---------------------------------------------------------------------------
# 9. Pydantic model constraints
# ---------------------------------------------------------------------------


class TestCriticModels:
    """Pydantic structural guards on the output models."""

    def test_critic_score_score_must_be_in_unit_interval(self) -> None:
        with pytest.raises(ValueError):
            CriticScore(axis="correctness", score=1.5, rationale="x", issues=[])
        with pytest.raises(ValueError):
            CriticScore(axis="correctness", score=-0.1, rationale="x", issues=[])

    def test_critic_score_rationale_min_length(self) -> None:
        with pytest.raises(ValueError):
            CriticScore(axis="correctness", score=0.5, rationale="", issues=[])

    def test_critic_verdict_overall_must_be_in_unit_interval(self) -> None:
        with pytest.raises(ValueError):
            CriticVerdict(
                scores=[
                    _score("correctness", 0.5),
                    _score("risk_awareness", 0.5),
                    _score("actionability", 0.5),
                    _score("explainability", 0.5),
                    _score("evidence", 0.5),
                ],
                overall=1.5,
                passed=True,
                summary="x",
                must_fix=[],
            )

    def test_critic_verdict_extra_forbidden(self) -> None:
        with pytest.raises(ValueError):
            CriticVerdict.model_validate(
                {
                    "scores": [
                        {
                            "axis": "correctness",
                            "score": 0.5,
                            "rationale": "x",
                            "issues": [],
                        }
                    ],
                    "overall": 0.5,
                    "passed": True,
                    "summary": "x",
                    "must_fix": [],
                    "extra_field": "nope",
                }
            )


# ---------------------------------------------------------------------------
# 10. Failure modes — fail loud, never silent
# ---------------------------------------------------------------------------


class TestFailureModes:
    """Defensive paths: missing candidate, empty tools, forbidden patterns."""

    def test_no_candidate_no_final_raises(self) -> None:
        critic = SelfCritic()
        state = AgentState(query="x")
        with pytest.raises(ValueError, match="no candidate or final"):
            critic.evaluate(state)

    def test_uses_final_when_candidate_missing(self) -> None:
        """If `candidate` is None but `final` is set, evaluate `final`."""
        critic = SelfCritic()
        rec = _make_rec(
            summary="Final recommendation",
            analysis=(
                "Because your situation is unique, this is the final answer."
            ),
            risks=["loss of principal"],
            actions=["Hold for 6 months"],
            citations=[_citation()],
        )
        state = AgentState(query="x", final=rec, tool_outputs=[])
        verdict = critic.evaluate(state)
        assert len(verdict.scores) == 5
        # Some axes will be low (no tool_outputs), so verify verdict is valid:
        assert isinstance(verdict.passed, bool)
        assert isinstance(verdict.overall, float)

    def test_forbidden_risk_pattern_caps_score(self) -> None:
        """A forbidden pattern caps the score — even with risks listed."""
        critic = SelfCritic()
        rec = _make_rec(
            summary="Put 100% in penny stocks",
            analysis=(
                "Put 100% of your savings into penny stocks for huge upside. "
                "Buy penny stocks today and you can't lose."
            ),
            risks=["you could lose money"],
            actions=["Buy penny stocks today"],
            citations=[_citation(value="100")],
        )
        state = AgentState(
            query="x",
            candidate=rec,
            tool_outputs=[{"data": "100"}],
        )
        verdict = critic.evaluate(state)
        risk = next(s for s in verdict.scores if s.axis == "risk_awareness")
        # The forbidden "penny stocks" pattern must cap the score at 0.3.
        assert risk.score <= 0.3
        assert any("penny" in issue.lower() for issue in risk.issues)

    def test_no_tool_outputs_with_numbers_lowers_correctness(self) -> None:
        critic = SelfCritic()
        rec = _make_rec(
            summary="Allocation",
            analysis="Allocate 30% to equities and 70% to bonds.",
            citations=[_citation(value="30")],
        )
        state = AgentState(query="x", candidate=rec, tool_outputs=[])
        verdict = critic.evaluate(state)
        correct = next(s for s in verdict.scores if s.axis == "correctness")
        assert correct.score == pytest.approx(0.1, abs=1e-9)


# ---------------------------------------------------------------------------
# 11. Public axis-scorer API (used by refine.py)
# ---------------------------------------------------------------------------


class TestPublicScorers:
    """The ``score_<axis>`` methods are public so refine.py can re-score a
    single axis after revising the candidate."""

    def test_each_axis_has_public_scorer(self) -> None:
        critic = SelfCritic()
        state = _make_state()
        rec = state.candidate
        assert rec is not None
        for axis in AXES:
            method = getattr(critic, f"score_{axis}", None)
            assert callable(method), f"score_{axis} must be callable"
            score = method(state, rec)
            assert isinstance(score, CriticScore)
            assert score.axis == axis
            assert 0.0 <= score.score <= 1.0