"""Unit tests for baseline systems (wave-6/03).

Covers NaiveRAGBaseline and SingleAgentBaseline: each returns
AgentState with a final Recommendation, is deterministic in mock,
and handles twin=None.
"""

from __future__ import annotations

from finroot.evaluation.baselines import NaiveRAGBaseline, SingleAgentBaseline
from finroot.llm.mock import MockProvider
from finroot.schemas.enums import ConfidenceLevel
from finroot.schemas.recommendation import Recommendation
from finroot.schemas.state import AgentState

# ---------------------------------------------------------------------------
# NaiveRAGBaseline
# ---------------------------------------------------------------------------


class TestNaiveRAGBaseline:
    def test_returns_agent_state(self) -> None:
        b = NaiveRAGBaseline()
        state = b.answer("What is the S&P 500 PE ratio?")
        assert isinstance(state, AgentState)
        assert isinstance(state.final, Recommendation)

    def test_final_has_analysis(self) -> None:
        b = NaiveRAGBaseline()
        state = b.answer("Is my portfolio diversified?")
        assert len(state.final.analysis) > 0
        assert len(state.final.summary) > 0

    def test_plan_is_populated(self) -> None:
        b = NaiveRAGBaseline()
        state = b.answer("What are the tax implications of selling?")
        assert len(state.plan) > 0

    def test_deterministic(self) -> None:
        b = NaiveRAGBaseline()
        a = b.answer("Should I buy bonds?")
        b_state = b.answer("Should I buy bonds?")
        assert a.final.analysis == b_state.final.analysis
        assert a.final.confidence == b_state.final.confidence

    def test_twin_none_ok(self) -> None:
        b = NaiveRAGBaseline()
        state = b.answer("How is inflation trending?", twin=None)
        assert isinstance(state, AgentState)
        assert isinstance(state.final, Recommendation)

    def test_twin_provided_ok(self) -> None:
        b = NaiveRAGBaseline()
        twin = {"risk_tolerance": "moderate", "age": 35}
        state = b.answer("What is good asset allocation?", twin=twin)
        assert state.twin_snapshot == twin

    def test_no_citations_by_default(self) -> None:
        b = NaiveRAGBaseline()
        state = b.answer("hello")
        # RAG baseline has 1 minimal citation (FM-11 requires citations when analysis has digits)
        assert len(state.final.citations) <= 1

    def test_confidence_is_set(self) -> None:
        b = NaiveRAGBaseline()
        state = b.answer("hello")
        assert state.final.confidence in (
            ConfidenceLevel.HIGH,
            ConfidenceLevel.MEDIUM,
            ConfidenceLevel.LOW,
        )

    def test_created_at_is_set(self) -> None:
        b = NaiveRAGBaseline()
        state = b.answer("hello")
        assert state.created_at is not None

    def test_no_tool_outputs(self) -> None:
        b = NaiveRAGBaseline()
        state = b.answer("hello")
        assert len(state.tool_outputs) == 0

    def test_no_risk_framing(self) -> None:
        b = NaiveRAGBaseline()
        state = b.answer("hello")
        assert len(state.final.risks) == 0


# ---------------------------------------------------------------------------
# SingleAgentBaseline
# ---------------------------------------------------------------------------


class TestSingleAgentBaseline:
    def test_returns_agent_state(self) -> None:
        b = SingleAgentBaseline()
        state = b.answer("What is the PE ratio of AAPL?")
        assert isinstance(state, AgentState)
        assert isinstance(state.final, Recommendation)

    def test_final_has_analysis(self) -> None:
        b = SingleAgentBaseline()
        state = b.answer("Is my portfolio diversified?")
        assert len(state.final.analysis) > 0
        assert len(state.final.summary) > 0

    def test_plan_is_populated(self) -> None:
        b = SingleAgentBaseline()
        state = b.answer("How do I optimize taxes?")
        assert len(state.plan) > 0

    def test_deterministic(self) -> None:
        b = SingleAgentBaseline()
        a = b.answer("Should I buy bonds?")
        b_state = b.answer("Should I buy bonds?")
        assert a.final.analysis == b_state.final.analysis
        assert a.final.confidence == b_state.final.confidence

    def test_twin_none_ok(self) -> None:
        b = SingleAgentBaseline()
        state = b.answer("How is inflation trending?", twin=None)
        assert isinstance(state, AgentState)
        assert isinstance(state.final, Recommendation)

    def test_twin_provided_ok(self) -> None:
        b = SingleAgentBaseline()
        twin = {"risk_tolerance": "high", "age": 28}
        state = b.answer("What is good asset allocation?", twin=twin)
        assert state.twin_snapshot == twin

    def test_has_tool_outputs(self) -> None:
        b = SingleAgentBaseline()
        state = b.answer("What are the best tech stocks?")
        assert len(state.tool_outputs) > 0
        assert state.tool_outputs[0]["tool"] == "mock_tool"

    def test_has_citations(self) -> None:
        b = SingleAgentBaseline()
        state = b.answer("hello")
        assert len(state.final.citations) >= 1
        assert state.final.citations[0].source == "mock_tool"

    def test_confidence_is_set(self) -> None:
        b = SingleAgentBaseline()
        state = b.answer("hello")
        assert state.final.confidence in (
            ConfidenceLevel.HIGH,
            ConfidenceLevel.MEDIUM,
            ConfidenceLevel.LOW,
        )

    def test_created_at_is_set(self) -> None:
        b = SingleAgentBaseline()
        state = b.answer("hello")
        assert state.created_at is not None


# ---------------------------------------------------------------------------
# Cross-baseline comparisons
# ---------------------------------------------------------------------------


class TestBaselineComparison:
    def test_rag_has_fewer_citations_than_single_agent(self) -> None:
        rag = NaiveRAGBaseline().answer("help me invest")
        agent = SingleAgentBaseline().answer("help me invest")
        assert len(rag.final.citations) <= len(agent.final.citations)

    def test_single_agent_has_tool_outputs_rag_does_not(self) -> None:
        rag = NaiveRAGBaseline().answer("help me invest")
        agent = SingleAgentBaseline().answer("help me invest")
        assert len(agent.tool_outputs) > 0
        assert len(rag.tool_outputs) == 0

    def test_both_return_same_state_shape(self) -> None:
        q = "help me invest"
        rag = NaiveRAGBaseline().answer(q)
        agent = SingleAgentBaseline().answer(q)
        assert type(rag) is type(agent)  # both are AgentState
        assert rag.query == agent.query == q


# ---------------------------------------------------------------------------
# Determinism via shared MockProvider
# ---------------------------------------------------------------------------


class TestSharedMockProvider:
    def test_same_provider_consistent_across_calls(self) -> None:
        llm = MockProvider()
        q = "Should I buy bonds?"
        r1 = NaiveRAGBaseline(llm=llm).answer(q)
        r2 = NaiveRAGBaseline(llm=llm).answer(q)
        assert r1.final.analysis == r2.final.analysis
        assert r1.final.confidence == r2.final.confidence
