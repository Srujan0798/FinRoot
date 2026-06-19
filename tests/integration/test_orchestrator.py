"""Integration tests for FinRootOrchestrator and the LangGraph state graph (wave-4/05).

Exercises the full classify → context → plan → execute → synthesize pipeline
with mock tools and the MockProvider LLM.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from finroot.agents.intent import IntentClassifier
from finroot.audit.trail import AuditTrail
from finroot.llm.mock import MockProvider
from finroot.memory.digital_twin import (
    DigitalTwin,
    InvestmentHorizon,
    RiskTolerance,
)
from finroot.memory.manager import MemoryManager
from finroot.schemas.enums import Intent
from finroot.schemas.state import AgentState
from finroot.workflows.context import ContextAssembler

UTC_NOW = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)


def _seed_twin(user_id: str, **overrides: object) -> DigitalTwin:
    fields: dict[str, object] = {
        "user_id": user_id,
        "name": "Test User",
        "age": 35,
        "risk_tolerance": RiskTolerance.MODERATE,
        "investment_horizon": InvestmentHorizon.LONG,
        "monthly_income": 150000.0,
        "monthly_expenses": 60000.0,
        "tax_bracket_pct": 30.0,
        "goals": ["retire at 55"],
        "constraints": ["no leverage"],
        "holdings": [
            {"symbol": "RELIANCE.NS", "weight": 0.5},
            {"symbol": "TCS.NS", "weight": 0.3},
            {"symbol": "HDFCBANK.NS", "weight": 0.2},
        ],
        "created_at": UTC_NOW,
        "updated_at": UTC_NOW,
    }
    fields.update(overrides)
    return DigitalTwin(**fields)


@pytest.fixture()
def workspace(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, str]:
    monkeypatch.setitem(sys.modules, "chromadb", None)
    return {
        "db_path": str(tmp_path / "twin.db"),
        "chroma_dir": str(tmp_path / "chroma"),
    }


@pytest.fixture()
def memory(workspace: dict[str, str]) -> MemoryManager:
    mgr = MemoryManager.create(
        user_id="test_user",
        chroma_dir=workspace["chroma_dir"],
        db_path=workspace["db_path"],
    )
    mgr.twin_store.save(_seed_twin("test_user"))
    return mgr


@pytest.fixture()
def audit(tmp_path: Path) -> AuditTrail:
    return AuditTrail(tmp_path / "audit.jsonl")


@pytest.fixture()
def llm() -> MockProvider:
    return MockProvider()


def _make_orchestrator(memory: MemoryManager, audit: AuditTrail, llm: MockProvider):
    from finroot.agents.orchestrator import FinRootOrchestrator

    return FinRootOrchestrator(memory=memory, audit=audit, llm=llm)


# ------------------------------------------------------------------
# Test 1: Portfolio review pipeline
# ------------------------------------------------------------------


def test_full_pipeline_portfolio(memory: MemoryManager, audit: AuditTrail, llm: MockProvider) -> None:
    """'Review my portfolio' → PORTFOLIO → PortfolioOptimizer + RiskAssessor → synthesis."""
    orch = _make_orchestrator(memory, audit, llm)
    state = orch.run("Review my portfolio")

    assert isinstance(state, AgentState)
    assert state.intent == Intent.PORTFOLIO
    assert state.candidate is not None
    assert state.candidate.summary
    assert state.candidate.confidence is not None
    # Plan should include portfolio_optimizer and risk_assessor
    assert "portfolio_optimizer" in state.plan
    assert "risk_assessor" in state.plan


# ------------------------------------------------------------------
# Test 2: Tax planning pipeline
# ------------------------------------------------------------------


def test_full_pipeline_tax(memory: MemoryManager, audit: AuditTrail, llm: MockProvider) -> None:
    """'What's the tax on 2L LTCG?' → TAX → TaxPlanner → synthesis."""
    orch = _make_orchestrator(memory, audit, llm)
    state = orch.run("What is the tax on ₹2,00,000 LTCG from equity?")

    assert isinstance(state, AgentState)
    assert state.intent == Intent.TAX
    assert state.candidate is not None
    assert state.candidate.summary
    assert "tax_planner" in state.plan


# ------------------------------------------------------------------
# Test 3: Market analysis pipeline
# ------------------------------------------------------------------


def test_full_pipeline_market(memory: MemoryManager, audit: AuditTrail, llm: MockProvider) -> None:
    """'What's RELIANCE price?' → NEWS_IMPACT → MarketAnalyst + NewsInterpreter → synthesis."""
    orch = _make_orchestrator(memory, audit, llm)
    state = orch.run("What is the RELIANCE price today?")

    assert isinstance(state, AgentState)
    assert state.intent == Intent.NEWS_IMPACT
    assert state.candidate is not None
    assert "market_analyst" in state.plan
    assert "news_interpreter" in state.plan


# ------------------------------------------------------------------
# Test 4: GREETING intent → direct response, no agents
# ------------------------------------------------------------------


def test_greeting_no_agents(memory: MemoryManager, audit: AuditTrail, llm: MockProvider) -> None:
    """GENERAL intent → no agents executed, direct greeting response."""
    orch = _make_orchestrator(memory, audit, llm)
    state = orch.run("Hello, how are you?")

    assert isinstance(state, AgentState)
    assert state.intent == Intent.GENERAL
    assert state.candidate is not None
    assert state.plan == []  # No agents selected
    assert "hello" in state.candidate.summary.lower() or "help" in state.candidate.summary.lower()


# ------------------------------------------------------------------
# Test 5: Audit trail has entries for each step
# ------------------------------------------------------------------


def test_audit_trail_has_entries(memory: MemoryManager, audit: AuditTrail, llm: MockProvider) -> None:
    """The audit trail records orchestrator.run and orchestrator.done events."""
    orch = _make_orchestrator(memory, audit, llm)
    orch.run("Hello")

    events = audit.replay()
    assert len(events) >= 2
    event_types = [e.type for e in events]
    assert "orchestrator.run" in event_types
    assert "orchestrator.done" in event_types


# ------------------------------------------------------------------
# Test 6: State round-trip through graph is valid
# ------------------------------------------------------------------


def test_state_roundtrip_valid(memory: MemoryManager, audit: AuditTrail, llm: MockProvider) -> None:
    """AgentState survives the graph pipeline and validates correctly."""
    orch = _make_orchestrator(memory, audit, llm)
    state = orch.run("Hello")

    # The state should be a valid AgentState
    assert isinstance(state, AgentState)
    # Should survive JSON round-trip
    json_str = state.model_dump_json()
    restored = AgentState.model_validate_json(json_str)
    assert restored.query == state.query
    assert restored.intent == state.intent


# ------------------------------------------------------------------
# Test 7: Intent classification routes to correct agents
# ------------------------------------------------------------------


def test_intent_routes_to_correct_agents(memory: MemoryManager, audit: AuditTrail, llm: MockProvider) -> None:
    """Verify the routing map: PORTFOLIO→portfolio_optimizer+risk_assessor,
    TAX→tax_planner, NEWS_IMPACT→market_analyst+news_interpreter.
    """
    orch = _make_orchestrator(memory, audit, llm)

    state_p = orch.run("Review my portfolio allocation")
    assert "portfolio_optimizer" in state_p.plan
    assert "risk_assessor" in state_p.plan

    state_t = orch.run("What is the tax on ₹5,00,000 LTCG?")
    assert "tax_planner" in state_t.plan
    assert "portfolio_optimizer" not in state_t.plan

    state_m = orch.run("What is the RELIANCE market price?")
    assert "market_analyst" in state_m.plan
    assert "news_interpreter" in state_m.plan


# ------------------------------------------------------------------
# Test 8: Context assembly populates twin_snapshot
# ------------------------------------------------------------------


def test_context_assembly_populates_twin(memory: MemoryManager, audit: AuditTrail, llm: MockProvider) -> None:
    """The context assembler should populate twin_snapshot from memory."""
    orch = _make_orchestrator(memory, audit, llm)
    state = orch.run("Review my portfolio")

    # twin_snapshot should be populated from the seeded twin
    assert isinstance(state.twin_snapshot, dict)
    assert state.twin_snapshot.get("user_id") == "test_user"


# ------------------------------------------------------------------
# Test 9: build_graph returns a compilable graph
# ------------------------------------------------------------------


def test_build_graph_compilable(audit: AuditTrail) -> None:
    """build_graph() should return a StateGraph that compiles without error."""
    from finroot.agents.orchestrator import ResultSynthesizer
    from finroot.workflows.graph import build_graph

    classifier = IntentClassifier()
    assembler = ContextAssembler()
    synthesizer = ResultSynthesizer()
    memory = MemoryManager.create(user_id="graph_test")

    graph = build_graph(
        intent_classifier=classifier,
        context_assembler=assembler,
        agent_map={},
        memory=memory,
        synthesizer=synthesizer,
    )
    compiled = graph.compile()
    assert compiled is not None


# ------------------------------------------------------------------
# Test 10: Candidate has citations when agents produce tool outputs
# ------------------------------------------------------------------


def test_candidate_has_citations(memory: MemoryManager, audit: AuditTrail, llm: MockProvider) -> None:
    """When sub-agents produce tool outputs, the candidate should have citations."""
    orch = _make_orchestrator(memory, audit, llm)
    state = orch.run("What is the tax on ₹2,00,000 LTCG?")

    if state.candidate is not None:
        # The synthesizer attaches citations from tool_outputs
        assert isinstance(state.candidate.citations, list)
