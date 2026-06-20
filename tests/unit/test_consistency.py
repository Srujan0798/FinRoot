"""Tests for SelfConsistency (wave-5, task 04).

Covers:
* Consensus computation with 0, 1, or 2 dissenting candidates.
* Mock generator determinism and error handling.
* ConsistencyResult model constraints.
* Minimum 10 test cases across all branches.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from finroot.reasoning.consistency import ConsistencyResult, SelfConsistency
from finroot.schemas.enums import ConfidenceLevel
from finroot.schemas.recommendation import Citation, Recommendation
from finroot.schemas.state import AgentState

UTC_NOW = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)


def _citation(value: str = "150.0") -> Citation:
    return Citation(
        source="yfinance",
        detail="AAPL last close",
        value=value,
        retrieved_at=UTC_NOW,
    )


def _rec(summary: str, **overrides: object) -> Recommendation:
    return Recommendation(
        summary=summary,
        analysis=overrides.pop("analysis", f"Analysis of {summary}."),
        confidence=overrides.pop("confidence", ConfidenceLevel.HIGH),
        citations=overrides.pop("citations", [_citation()]),
        **overrides,  # type: ignore[arg-type]
    )


class TestConsensusComputation:
    """Consensus logic: computing agreement from candidate lists."""

    def setup_method(self) -> None:
        self.sc = SelfConsistency()

    def test_three_identical(self) -> None:
        cand = _rec("Invest in a diversified index fund")
        candidates = [cand, cand, cand]
        result = self.sc.compute_consensus(candidates)
        assert result.agreement_score == 1.0
        assert result.winner.summary == "Invest in a diversified index fund"
        assert result.dissenting_view is None
        assert len(result.candidates) == 3

    def test_two_agree_one_differs(self) -> None:
        majority = _rec("Hold cash")
        minority = _rec("Buy stocks")
        candidates = [majority, majority, minority]
        result = self.sc.compute_consensus(candidates)
        assert result.agreement_score == pytest.approx(0.67, abs=0.01)
        assert result.winner.summary == "Hold cash"
        assert result.dissenting_view == "Low consensus — verify independently"
        assert len(result.candidates) == 3

    def test_all_three_disagree(self) -> None:
        a = _rec("Buy bonds")
        b = _rec("Buy stocks")
        c = _rec("Hold cash")
        candidates = [a, b, c]
        result = self.sc.compute_consensus(candidates)
        assert result.agreement_score == 0.0
        assert result.winner.summary in ("Buy bonds", "Buy stocks", "Hold cash")
        assert result.dissenting_view == "Low consensus — verify independently"
        assert len(result.candidates) == 3

    def test_candidates_list_length(self) -> None:
        cand = _rec("Rebalance quarterly")
        candidates = [cand, cand, cand]
        result = self.sc.compute_consensus(candidates)
        assert len(result.candidates) == 3

    def test_winner_is_majority_copy(self) -> None:
        majority = _rec("Diversify", risks=["Market risk"])
        minority = _rec("Concentrate")
        candidates = [majority, majority, minority]
        result = self.sc.compute_consensus(candidates)
        assert result.winner.risks == ["Market risk"]
        assert result.winner.summary == "Diversify"

    def test_single_candidate(self) -> None:
        cand = _rec("Do nothing")
        result = self.sc.compute_consensus([cand])
        assert result.agreement_score == 1.0
        assert result.dissenting_view is None
        assert len(result.candidates) == 1
        assert result.winner.summary == "Do nothing"

    def test_two_out_of_four_agree(self) -> None:
        a = _rec("Buy bonds")
        b = _rec("Buy bonds")
        c = _rec("Buy stocks")
        d = _rec("Hold cash")
        candidates = [a, b, c, d]
        result = self.sc.compute_consensus(candidates)
        assert result.agreement_score == 0.5
        assert result.winner.summary == "Buy bonds"
        assert result.dissenting_view == "Low consensus — verify independently"


class TestCheckMethod:
    """Integration: check() with mock generator from AgentState."""

    def setup_method(self) -> None:
        self.sc = SelfConsistency()
        self.base_rec = _rec("Invest in index funds")
        self.state = AgentState(
            query="investment advice",
            candidate=self.base_rec,
        )

    def test_check_returns_consistency_result(self) -> None:
        result = self.sc.check(self.state)
        assert isinstance(result, ConsistencyResult)
        assert len(result.candidates) == 3

    def test_mock_mode_deterministic(self) -> None:
        r1 = self.sc.check(self.state)
        r2 = self.sc.check(self.state)
        assert r1.winner.summary == r2.winner.summary
        assert r1.agreement_score == r2.agreement_score

    def test_check_candidates_have_n_items(self) -> None:
        result = self.sc.check(self.state)
        assert len(result.candidates) == self.sc.N_CANDIDATES

    def test_check_raises_on_missing_candidate(self) -> None:
        empty_state = AgentState(query="no candidate")
        with pytest.raises(ValueError, match="state.candidate is None"):
            self.sc.check(empty_state)


class TestConsistencyResultModel:
    """Pydantic model constraints for ConsistencyResult."""

    def test_negative_agreement_rejected(self) -> None:
        with pytest.raises(ValueError, match="agreement_score"):
            ConsistencyResult(
                candidates=[_rec("A")],
                winner=_rec("A"),
                agreement_score=-0.1,
            )

    def test_above_one_agreement_rejected(self) -> None:
        with pytest.raises(ValueError, match="agreement_score"):
            ConsistencyResult(
                candidates=[_rec("A")],
                winner=_rec("A"),
                agreement_score=1.1,
            )
