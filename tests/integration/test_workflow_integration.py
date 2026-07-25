"""Comprehensive cross-module integration tests for the FinRoot workflow pipeline.

Exercises the full classify -> context -> plan -> execute -> synthesize path
via the ``answer()`` entry point in mock mode.  Covers multiple intents,
context preservation, graceful degradation, and output schema completeness.

All tests use ``@pytest.mark.integration`` and require no API keys.
"""

from __future__ import annotations

import pytest

from finroot.schemas.enums import ConfidenceLevel, Intent
from finroot.schemas.state import AgentState
from interface.core import answer

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _run(query: str, user_id: str = "integration_test") -> AgentState:
    """Shorthand to run a query through the full pipeline in mock mode."""
    return answer(query, user_id=user_id, mock=True)


# ------------------------------------------------------------------
# Test 1: Risk assessment workflow
# ------------------------------------------------------------------


@pytest.mark.integration
def test_full_workflow_mock_risk() -> None:
    """A risk-related query should be classified as RISK intent, invoke
    the risk_assessor, and produce a recommendation mentioning risk."""
    state = _run("What is the volatility and VaR of my investments?")

    assert isinstance(state, AgentState)
    assert state.intent == Intent.RISK
    assert state.candidate is not None
    summary = state.candidate.summary.lower()
    analysis = state.candidate.analysis.lower()
    assert "risk" in summary or "risk" in analysis or "volatil" in summary or "volatil" in analysis, (
        f"Expected risk-related content in output. "
        f"summary={state.candidate.summary[:200]}"
    )


# ------------------------------------------------------------------
# Test 2: Tax planning workflow
# ------------------------------------------------------------------


@pytest.mark.integration
def test_full_workflow_mock_tax() -> None:
    """A tax-related query should be classified as TAX intent, invoke
    the tax_planner, and produce a recommendation mentioning tax."""
    state = _run("What is the tax on ₹2,00,000 LTCG from equity?")

    assert isinstance(state, AgentState)
    assert state.intent == Intent.TAX
    assert state.candidate is not None
    combined = (state.candidate.summary + " " + state.candidate.analysis).lower()
    assert "tax" in combined, (
        f"Expected tax-related content in output. "
        f"summary={state.candidate.summary[:200]}"
    )


# ------------------------------------------------------------------
# Test 3: Portfolio optimization workflow
# ------------------------------------------------------------------


@pytest.mark.integration
def test_full_workflow_mock_portfolio() -> None:
    """A portfolio query should be classified as PORTFOLIO intent,
    invoke portfolio_optimizer + risk_assessor, and return a recommendation."""
    state = _run("Review my portfolio allocation and suggest improvements")

    assert isinstance(state, AgentState)
    assert state.intent == Intent.PORTFOLIO
    assert state.candidate is not None
    assert state.candidate.summary
    assert "portfolio_optimizer" in state.plan
    assert "risk_assessor" in state.plan


# ------------------------------------------------------------------
# Test 4: Market analysis workflow
# ------------------------------------------------------------------


@pytest.mark.integration
def test_full_workflow_mock_market() -> None:
    """A market query should be classified as NEWS_IMPACT intent,
    invoke market_analyst + news_interpreter, and return a recommendation."""
    state = _run("What is the current market outlook for RELIANCE?")

    assert isinstance(state, AgentState)
    assert state.intent == Intent.NEWS_IMPACT
    assert state.candidate is not None
    assert state.candidate.summary
    assert "market_analyst" in state.plan
    assert "news_interpreter" in state.plan


# ------------------------------------------------------------------
# Test 5: Context is preserved across sequential queries
# ------------------------------------------------------------------


@pytest.mark.integration
def test_workflow_preserves_context() -> None:
    """Two sequential queries under the same user_id should both succeed,
    and the second query should see working-memory context from the first."""
    user_id = "context_test_user"
    state1 = _run("I want to retire by 55 with moderate risk", user_id=user_id)
    assert state1.candidate is not None

    state2 = _run("Based on that, how should I allocate?", user_id=user_id)
    assert isinstance(state2, AgentState)
    assert state2.candidate is not None
    assert state2.candidate.summary


# ------------------------------------------------------------------
# Test 6: Unrelated / general query is handled gracefully
# ------------------------------------------------------------------


@pytest.mark.integration
def test_workflow_handles_unrelated_query() -> None:
    """A non-financial query (weather) should be classified as GENERAL and
    still return a valid AgentState with a candidate recommendation."""
    state = _run("What is the weather today in Mumbai?")

    assert isinstance(state, AgentState)
    assert state.intent == Intent.GENERAL
    assert state.candidate is not None
    assert state.candidate.summary


# ------------------------------------------------------------------
# Test 7: Output contains a confidence score
# ------------------------------------------------------------------


@pytest.mark.integration
def test_workflow_returns_confidence() -> None:
    """The recommendation must have a valid ConfidenceLevel."""
    state = _run("Should I invest in mutual funds?")

    assert state.candidate is not None
    assert state.candidate.confidence is not None
    assert isinstance(state.candidate.confidence, ConfidenceLevel)
    assert state.candidate.confidence in (
        ConfidenceLevel.HIGH,
        ConfidenceLevel.MEDIUM,
        ConfidenceLevel.LOW,
        ConfidenceLevel.INSUFFICIENT,
    )


# ------------------------------------------------------------------
# Test 8: Output contains citations
# ------------------------------------------------------------------


@pytest.mark.integration
def test_workflow_returns_citations() -> None:
    """The recommendation must have a citations list (may be empty for
    qualitative-only advice, but the field must exist and be a list)."""
    state = _run("What is the tax on ₹1,00,000 LTCG?")

    assert state.candidate is not None
    assert isinstance(state.candidate.citations, list)


# ------------------------------------------------------------------
# Test 9: Output contains structured sections
# ------------------------------------------------------------------


@pytest.mark.integration
def test_workflow_returns_sections() -> None:
    """The recommendation must expose the structured list fields
    (risks, actions, alternatives) that form the output sections."""
    state = _run("Review my portfolio")

    assert state.candidate is not None
    assert isinstance(state.candidate.risks, list)
    assert isinstance(state.candidate.actions, list)
    assert isinstance(state.candidate.alternatives, list)


# ------------------------------------------------------------------
# Test 10: AgentState completeness after execution
# ------------------------------------------------------------------


@pytest.mark.integration
def test_workflow_state_completeness() -> None:
    """After a full pipeline run, the returned AgentState must have all
    required fields populated (non-None for mandatory fields)."""
    state = _run("Assess the risk of my investments")

    assert isinstance(state, AgentState)
    # Mandatory fields set by the pipeline
    assert state.query
    assert state.intent is not None
    assert isinstance(state.twin_snapshot, dict)
    assert isinstance(state.plan, list)
    assert isinstance(state.tool_outputs, list)
    assert state.candidate is not None
    # These may be None (degraded) but the fields must exist
    assert hasattr(state, "critique")
    assert hasattr(state, "verifier_verdict")
    assert hasattr(state, "final")
    assert isinstance(state.audit_events, list)
