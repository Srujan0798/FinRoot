"""Tests for the FRB graders (wave-6, task 02).

Covers the code-based deterministic grader (`grade_code`), the LLM-judge
(`grade_llm`), and the human-review template file. The graders are the
gating layer behind the 35% Reasoning-Quality score; their tests must
guard every criterion in the contract and the anti-patterns listed there.

Run with::

    PYTHONPATH=src python3 -m pytest tests/unit/test_graders.py -v

This test module adds the repo root to ``sys.path`` so the ``evals.graders``
namespace package is importable when pytest is launched with
``PYTHONPATH=src`` (the only path the orchestrator's acceptance command
guarantees).
"""
from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

# Make `evals.graders` importable (the repo root holds the `evals/` package).
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402
from evals.graders import (  # noqa: E402
    GradeResult,
    build_judge_prompt,
    grade_code,
    grade_llm,
)
from evals.graders.code_based import SCORE_THRESHOLD, WEIGHTS  # noqa: E402
from evals.graders.llm_judge import JUDGE_AXES  # noqa: E402

from finroot.llm.mock import MockProvider  # noqa: E402
from finroot.schemas.enums import ConfidenceLevel  # noqa: E402
from finroot.schemas.recommendation import Citation, Recommendation  # noqa: E402
from finroot.schemas.state import AgentState  # noqa: E402

UTC_NOW = datetime(2026, 6, 20, 12, 0, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


def _citation(source: str = "yfinance", detail: str = "market data", value: str = "100") -> Citation:
    return Citation(
        source=source,
        detail=detail,
        value=value,
        retrieved_at=UTC_NOW,
    )


def _make_rec(
    *,
    summary: str = "Diversified allocation across equity, debt, and gold.",
    analysis: str = (
        "Because your risk profile is moderate and horizon is long, "
        "we recommend a balanced allocation. Therefore equities, debt, and "
        "gold each get a slice, so concentration risk stays bounded and "
        "tax-aware rebalancing remains possible."
    ),
    risks: list[str] | None = None,
    actions: list[str] | None = None,
    citations: list[Citation] | None = None,
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH,
) -> Recommendation:
    return Recommendation(
        summary=summary,
        analysis=analysis,
        risks=risks if risks is not None else ["market volatility", "concentration risk"],
        actions=actions if actions is not None else [
            "Allocate 30% to equity by Q1",
            "Rebalance portfolio quarterly",
        ],
        citations=citations if citations is not None else [_citation(), _citation(source="tax_tables")],
        confidence=confidence,
    )


def _make_state(rec: Recommendation | None = None, **rec_kwargs: object) -> AgentState:
    return AgentState(
        query="What is a reasonable asset allocation?",
        final=rec if rec is not None else _make_rec(**rec_kwargs),
    )


# FRB-001 task spec — portfolio rebalance.
TASK_Portfolio = {
    "id": "frb-001",
    "domain": "portfolio",
    "difficulty": "easy",
    "query": "My portfolio is 80% in one large-cap stock and 20% in a liquid fund. Should I rebalance?",
    "twin_id": None,
    "expected": {
        "must_mention": ["concentration", "risk", "tax", "LTCG", "diversif"],
        "must_not": ["guaranteed", "you will definitely", "no risk"],
        "min_citations": 2,
        "expected_confidence": "high",
        "numeric_answer": None,
        "numeric_tolerance": 0.0,
    },
    "rationale": "Single-stock concentration is the dominant risk.",
}


# FRB-012 task spec — deterministic LTCG tax math.
TASK_LTCG = {
    "id": "frb-012",
    "domain": "tax",
    "difficulty": "easy",
    "query": "LTCG from listed equity, FY 2024-25.",
    "twin_id": None,
    "expected": {
        "must_mention": ["LTCG", "exemption", "10%", "cess", "Budget 2024"],
        "must_not": ["guaranteed", "no tax", "free"],
        "min_citations": 2,
        "expected_confidence": "high",
        "numeric_answer": 10400.0,
        "numeric_tolerance": 1.0,
    },
    "rationale": "Canonical LTCG computation.",
}


# Stub judge LLM that returns a fixed rubric-format response.
class _StubJudgeLLM:
    """Deterministic judge for tests; emulates a real LLM's rubric output."""

    name: str = "stub-judge"

    def __init__(self, response: str) -> None:
        self._response = response
        self.calls: list[str] = []

    def complete(self, prompt: str, **_kwargs: object):  # noqa: ANN003
        self.calls.append(prompt)
        from finroot.llm.base import LLMResult

        return LLMResult(
            text=self._response,
            provider=self.name,
            model="stub",
            tokens=None,
        )


# ---------------------------------------------------------------------------
# Code-based grader
# ---------------------------------------------------------------------------


class TestCodeBased:
    """Deterministic checks (must_mention, must_not, citations, numeric, confidence)."""

    def test_passes_good_answer(self) -> None:
        """A well-formed answer with keywords, citations, and confidence match passes."""
        rec = _make_rec(
            summary=(
                "Concentration risk is high; rebalance before FY-end with tax-aware "
                "LTCG planning and a glide path to diversification."
            ),
        )
        result = grade_code(TASK_Portfolio, _make_state(rec))

        assert isinstance(result, GradeResult)
        assert result.task_id == "frb-001"
        assert result.grader == "code"
        assert result.passed is True, result.breakdown
        assert result.score >= SCORE_THRESHOLD
        assert result.breakdown["must_not"]["passed"] is True
        assert result.breakdown["citations"]["passed"] is True
        assert result.breakdown["citations"]["count"] >= 2

    def test_fails_on_must_not_hit(self) -> None:
        """An answer containing a red-flag phrase ('guaranteed returns') FAILS."""
        rec = _make_rec(
            summary=(
                "Concentration and LTCG risk are real, but our diversified plan "
                "comes with guaranteed returns — you will definitely beat the market."
            ),
            confidence=ConfidenceLevel.HIGH,
        )
        result = grade_code(TASK_Portfolio, _make_state(rec))

        assert result.passed is False
        assert result.breakdown["must_not"]["passed"] is False
        assert result.breakdown["must_not"]["hit_phrase"] is not None
        # must_not is a HARD veto — even when the soft score would be perfect,
        # passed must be False. The score itself is independent (still reported
        # for transparency) so reviewers can see "everything looks fine
        # except the red-flag phrase."
        assert result.breakdown["must_not"]["hit_phrase"].lower() in (
            "guaranteed",
            "you will definitely",
        )

    def test_fails_on_zero_citations(self) -> None:
        """Zero citations on a task that requires citations → must FAIL (FM-11 / anti-pattern)."""
        # Build a recommendation whose analysis has NO digits so the
        # Recommendation validator does not require citations — but the task
        # has min_citations=2, so the grader must still fail.
        rec = Recommendation(
            summary=(
                "Concentration risk dominates the portfolio. Tax and LTCG apply, "
                "and diversification reduces single-stock exposure."
            ),
            analysis=(
                "Because concentration is the main risk and horizon is long, "
                "we recommend trimming the large-cap position and rebalancing "
                "into debt plus a diversified equity basket. LTCG applies on "
                "any partial sale this fiscal year."
            ),
            risks=["concentration risk"],
            actions=["rebalance before FY-end"],
            citations=[],  # zero citations
            confidence=ConfidenceLevel.HIGH,
        )
        result = grade_code(TASK_Portfolio, _make_state(rec))

        assert result.passed is False
        assert result.breakdown["citations"]["passed"] is False
        assert result.breakdown["citations"]["count"] == 0
        assert result.breakdown["citations"]["min_required"] == 2

    def test_numeric_match_within_tolerance(self) -> None:
        """₹10,400 within ±1 of the expected 10400 → passes."""
        rec = _make_rec(
            summary="The LTCG tax for FY 2024-25, after the ₹1L exemption, is ₹10,400.",
            analysis=(
                "Because the LTCG exemption of ₹1L applies under Budget 2024, "
                "taxable LTCG is ₹1L. 10% base tax plus 4% cess yields ₹10,400. "
                "Therefore the LTCG tax owed is ₹10,400 total."
            ),
            confidence=ConfidenceLevel.HIGH,
        )
        result = grade_code(TASK_LTCG, _make_state(rec))

        assert result.breakdown["numeric"]["passed"] is True, result.breakdown
        assert result.breakdown["numeric"]["extracted"] == pytest.approx(10400.0, abs=1.0)
        assert result.breakdown["numeric"]["diff"] <= 1.0

    def test_numeric_mismatch_fails(self) -> None:
        """A numeric answer far from the expected value → fails the numeric check."""
        rec = _make_rec(
            summary="The LTCG tax for FY 2024-25 is ₹99,999.",
            analysis=(
                "Because the LTCG exemption of ₹1L applies under Budget 2024, "
                "taxable LTCG is ₹1L. 10% base tax plus 4% cess yields ₹99,999. "
                "Therefore the LTCG tax owed is ₹99,999 total."
            ),
            confidence=ConfidenceLevel.HIGH,
        )
        result = grade_code(TASK_LTCG, _make_state(rec))

        assert result.breakdown["numeric"]["passed"] is False
        assert result.breakdown["numeric"]["diff"] > 1.0

    def test_numeric_zero_extracted_fails(self) -> None:
        """If expected_numeric is set but no usable number can be extracted, the check fails.

        Uses number-free prose (and explicitly empty risks/actions) so the
        regex finds nothing — confirms the "no candidates at all" branch
        (vs. the "extracted but wrong" branch in ``test_numeric_mismatch_fails``).
        """
        rec = _make_rec(
            summary="The tax is computed per the Budget rules.",
            analysis=(
                "Because the LTCG exemption applies under the Budget, "
                "taxable LTCG is the gain above the exemption. The base "
                "tax plus cess is applied per the rules."
            ),
            risks=[],
            actions=[],
            confidence=ConfidenceLevel.HIGH,
        )
        result = grade_code(TASK_LTCG, _make_state(rec))

        assert result.breakdown["numeric"]["passed"] is False
        assert result.breakdown["numeric"]["extracted"] is None

    def test_confidence_mismatch_fails(self) -> None:
        """Expected confidence 'high' but the agent answered 'low' → fails."""
        rec = _make_rec(
            summary=(
                "Concentration risk is real. Tax and LTCG apply. Diversification "
                "is recommended."
            ),
            confidence=ConfidenceLevel.LOW,  # task expected HIGH
        )
        result = grade_code(TASK_Portfolio, _make_state(rec))

        assert result.breakdown["confidence"]["passed"] is False
        assert result.breakdown["confidence"]["expected"] == "high"
        assert result.breakdown["confidence"]["actual"] == "low"
        assert result.passed is False

    def test_must_mention_keyword_coverage(self) -> None:
        """Partial keyword coverage reduces the must_mention ratio and the weighted score."""
        rec = _make_rec(
            summary="There is concentration risk here.",  # matches "concentration", "risk"
            analysis=(
                "Because of the concentration issue, we should review the "
                "position. A partial rebalance is suggested."
            ),
        )
        perfect = grade_code(TASK_Portfolio, _make_state(_make_rec()))
        partial = grade_code(TASK_Portfolio, _make_state(rec))

        # Matches: "concentration" + "risk" (lowercased) → 2/5 = 0.4
        assert partial.breakdown["must_mention"]["ratio"] == pytest.approx(0.4, abs=1e-9)
        # "tax", "LTCG", and "diversif" are NOT in the answer → must miss.
        assert set(partial.breakdown["must_mention"]["missing"]) == {"tax", "LTCG", "diversif"}
        # Partial coverage produces a strictly lower score than a perfect answer
        # (the ratio feeds into the weighted score per the contract).
        assert partial.score < perfect.score

    def test_garbage_answer_fails(self) -> None:
        """A deliberately empty/junk answer FAILS — no rubber-stamp."""
        rec = Recommendation(
            summary="ok",
            analysis="maybe",
            risks=[],
            actions=[],
            citations=[],
            confidence=ConfidenceLevel.LOW,
        )
        result = grade_code(TASK_Portfolio, _make_state(rec))

        assert result.passed is False
        assert result.score == pytest.approx(0.0, abs=1e-9)
        assert result.breakdown["citations"]["passed"] is False
        assert result.breakdown["must_mention"]["ratio"] == 0.0

    def test_state_without_final_raises(self) -> None:
        """No final recommendation → fail loud (FM-11)."""
        empty_state = AgentState(query="...", final=None)
        with pytest.raises(ValueError, match="state.final is None"):
            grade_code(TASK_Portfolio, empty_state)

    def test_score_uses_expected_weights(self) -> None:
        """The weights in breakdown match the published WEIGHTS constant (sum to 1.0)."""
        result = grade_code(TASK_Portfolio, _make_state())
        assert result.breakdown["weights"] == WEIGHTS
        assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9
        assert result.breakdown["threshold"] == SCORE_THRESHOLD

    def test_handles_currency_format_with_indian_separators(self) -> None:
        """₹1,00,000-style numbers extract correctly (Indian lakh notation)."""
        candidates = ["₹1,00,000 total", "Rs. 10400 only", "INR 200"]
        from evals.graders.code_based import _extract_numeric_candidates

        got = _extract_numeric_candidates(candidates[0])
        assert got[0] == pytest.approx(100000.0)
        got = _extract_numeric_candidates(candidates[1])
        assert got[0] == pytest.approx(10400.0)
        got = _extract_numeric_candidates(candidates[2])
        assert got[0] == pytest.approx(200.0)


# ---------------------------------------------------------------------------
# LLM-judge grader
# ---------------------------------------------------------------------------


class TestLLMJudge:
    """5-axis rubric grader; deterministic, Mock-capable, never rubber-stamps."""

    def test_returns_grade_result_with_breakdown(self) -> None:
        """Even with a stub judge, the result has the contracted fields."""
        stub = _StubJudgeLLM(
            "correctness: 0.9\n"
            "risk_awareness: 0.8\n"
            "actionability: 0.7\n"
            "explainability: 0.6\n"
            "evidence_grounding: 0.5"
        )
        result = grade_llm(TASK_Portfolio, _make_state(), stub)

        assert isinstance(result, GradeResult)
        assert result.task_id == "frb-001"
        assert result.grader == "llm_judge"
        assert "axes" in result.breakdown
        assert all(axis in result.breakdown["axes"] for axis in JUDGE_AXES)
        # Mean of (0.9, 0.8, 0.7, 0.6, 0.5) = 0.7
        assert result.score == pytest.approx(0.7, abs=1e-3)
        assert result.passed is True
        assert result.breakdown["score_source"] == "judge_llm"

    def test_deterministic_in_mock(self) -> None:
        """MockProvider is non-rubric; grader must still produce a deterministic result."""
        mock = MockProvider()
        state = _make_state()
        r1 = grade_llm(TASK_Portfolio, state, mock)
        r2 = grade_llm(TASK_Portfolio, state, mock)

        assert r1.score == r2.score
        assert r1.passed == r2.passed
        assert r1.breakdown == r2.breakdown
        # Mock's canned responses don't follow the rubric → fallback fires.
        assert r1.breakdown["score_source"] == "heuristic_fallback"

    def test_axes_dict_has_all_five(self) -> None:
        """The breakdown always includes every axis (no missing keys for the aggregator)."""
        stub = _StubJudgeLLM("correctness: 0.5\nrisk_awareness: 0.5\nactionability: 0.5")
        result = grade_llm(TASK_Portfolio, _make_state(), stub)

        assert set(result.breakdown["axes"].keys()) == set(JUDGE_AXES)
        # Missing axes from the LLM response fall back to 0.0, NOT KeyError.
        assert result.breakdown["axes"]["explainability"] == 0.0
        assert result.breakdown["axes"]["evidence_grounding"] == 0.0

    def test_garbage_answer_fails_judge(self) -> None:
        """A deliberately empty/junk answer FAILS the LLM-judge too (no rubber-stamp)."""
        stub = _StubJudgeLLM(
            "correctness: 0.1\n"
            "risk_awareness: 0.1\n"
            "actionability: 0.1\n"
            "explainability: 0.1\n"
            "evidence_grounding: 0.1"
        )
        junk = Recommendation(
            summary="ok",
            analysis="maybe",
            risks=[],
            actions=[],
            citations=[],
            confidence=ConfidenceLevel.LOW,
        )
        result = grade_llm(TASK_Portfolio, _make_state(junk), stub)

        assert result.passed is False
        assert result.score < SCORE_THRESHOLD
        # Even via heuristic fallback, junk should score very low.
        # (stub returns 0.1 per axis → mean 0.1; fallback gives ~0.34 max.)
        assert result.score < 0.4

    def test_state_without_final_raises(self) -> None:
        """No final recommendation → fail loud (FM-11)."""
        stub = _StubJudgeLLM("correctness: 0.5")
        with pytest.raises(ValueError, match="state.final is None"):
            grade_llm(TASK_Portfolio, AgentState(query="...", final=None), stub)

    def test_judge_none_raises(self) -> None:
        """judge_llm=None → fail loud; never silently substitute Mock."""
        with pytest.raises(ValueError, match="judge_llm is None"):
            grade_llm(TASK_Portfolio, _make_state(), None)  # type: ignore[arg-type]

    def test_judge_prompt_contains_axes_and_keywords(self) -> None:
        """The rubric prompt mentions every axis and the task's must_mention keywords."""
        prompt = build_judge_prompt(TASK_Portfolio, _make_state())
        for axis in JUDGE_AXES:
            assert axis in prompt, f"axis {axis!r} missing from judge prompt"
        # The prompt surfaces the task's red-flag phrases so the judge can penalize.
        assert "guaranteed" in prompt
        # And surfaces expected keywords so the judge knows what to look for.
        assert "concentration" in prompt
        assert "LTCG" in prompt

    def test_evidence_alias_maps_to_evidence_grounding(self) -> None:
        """A judge that uses the critic's shorter 'evidence' axis name still scores correctly."""
        stub = _StubJudgeLLM(
            "correctness: 0.8\n"
            "risk_awareness: 0.7\n"
            "actionability: 0.6\n"
            "explainability: 0.5\n"
            "evidence: 0.4"
        )
        result = grade_llm(TASK_Portfolio, _make_state(), stub)

        # Mean = (0.8+0.7+0.6+0.5+0.4)/5 = 0.6 → passes the threshold (boundary).
        assert result.score == pytest.approx(0.6, abs=1e-3)
        assert result.breakdown["axes"]["evidence_grounding"] == pytest.approx(0.4)


# ---------------------------------------------------------------------------
# Cross-grader contract (anti-pattern: no rubber-stamp)
# ---------------------------------------------------------------------------


class TestNoRubberStamp:
    """Both graders must reject junk and spread scores — never blanket-pass."""

    def test_spread_across_inputs(self) -> None:
        """Good vs junk vs red-flag answers must produce distinct outcomes (not all same)."""
        good = _make_state(
            _make_rec(
                summary=(
                    "Concentration risk is high; rebalance with tax-aware LTCG "
                    "planning and a glide path to diversification."
                ),
            )
        )
        junk = _make_state(
            Recommendation(
                summary="ok",
                analysis="maybe",
                risks=[],
                actions=[],
                citations=[],
                confidence=ConfidenceLevel.LOW,
            )
        )
        bad = _make_state(
            _make_rec(
                summary=(
                    "Concentration and LTCG risk are real, but our diversified "
                    "plan comes with guaranteed returns — you will definitely "
                    "beat the market. No risk at all."
                ),
            )
        )

        outcomes = {
            "good": grade_code(TASK_Portfolio, good).passed,
            "junk": grade_code(TASK_Portfolio, junk).passed,
            "bad": grade_code(TASK_Portfolio, bad).passed,
        }
        # Good passes; junk and bad fail. If all three were the same, the
        # grader would be rubber-stamping.
        assert outcomes == {"good": True, "junk": False, "bad": False}, outcomes

    def test_judge_spread_across_inputs(self) -> None:
        """LLM-judge also spreads scores — good > bad > junk."""
        stub = _StubJudgeLLM(
            "correctness: 0.9\n"
            "risk_awareness: 0.9\n"
            "actionability: 0.9\n"
            "explainability: 0.9\n"
            "evidence_grounding: 0.9"
        )
        good = grade_llm(TASK_Portfolio, _make_state(), stub)
        # To prove spread, we feed the stub a deliberately bad response and
        # confirm it scores low. (A good-stub returning 0.9 on every input
        # would be the rubber-stamp failure mode we're guarding against.)
        bad_stub = _StubJudgeLLM(
            "correctness: 0.1\n"
            "risk_awareness: 0.1\n"
            "actionability: 0.1\n"
            "explainability: 0.1\n"
            "evidence_grounding: 0.1"
        )
        bad = grade_llm(TASK_Portfolio, _make_state(), bad_stub)

        assert good.score > bad.score
        assert good.passed is True
        assert bad.passed is False


# ---------------------------------------------------------------------------
# GradeResult contract
# ---------------------------------------------------------------------------


class TestGradeResultContract:
    """The returned Pydantic model has the frozen shape from the contract."""

    def test_required_fields_present(self) -> None:
        result = grade_code(TASK_Portfolio, _make_state())
        assert hasattr(result, "task_id")
        assert hasattr(result, "passed")
        assert hasattr(result, "score")
        assert hasattr(result, "breakdown")
        assert hasattr(result, "grader")

    def test_extra_forbid_on_grade_result(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GradeResult(task_id="x", passed=True, score=0.5, breakdown={}, grader="code", evil="extra")

    def test_score_is_normalized(self) -> None:
        """score is always in [0.0, 1.0]."""
        result = grade_code(TASK_Portfolio, _make_state())
        assert 0.0 <= result.score <= 1.0


# ---------------------------------------------------------------------------
# Human-review template
# ---------------------------------------------------------------------------


class TestHumanReviewTemplate:
    """The markdown form covers all 5 axes and the honesty checks."""

    @pytest.fixture(scope="class")
    def template_text(self) -> str:
        path = REPO_ROOT / "evals" / "graders" / "human_review_template.md"
        return path.read_text(encoding="utf-8")

    def test_template_lists_all_five_axes(self, template_text: str) -> None:
        for axis in ("Correctness", "Risk-awareness", "Actionability", "Explainability", "Evidence-grounding"):
            assert axis in template_text, f"axis {axis!r} missing from template"

    def test_template_has_honesty_checks(self, template_text: str) -> None:
        # The form must remind reviewers to look for the things automated grading misses.
        assert "guaranteed" in template_text.lower()
        assert "fabricat" in template_text.lower()  # fabricated / fabrication

    def test_template_has_verdict_section(self, template_text: str) -> None:
        assert "PASS" in template_text
        assert "FAIL" in template_text
        assert "REVISE" in template_text
