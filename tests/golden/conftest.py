"""Shared fixtures for golden tests: mock_state and run_pipeline."""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest

from finroot.schemas.enums import ConfidenceLevel
from finroot.schemas.recommendation import Citation, Recommendation
from finroot.schemas.state import AgentState


@pytest.fixture
def mock_state():
    """Build an AgentState pre-populated with mock tool outputs and a recommendation.

    Useful for testing downstream stages (critic, prudence verifier) without
    running the full pipeline.  The recommendation carries synthetic but valid
    citations so the FM-11 structural guard is satisfied.
    """
    return AgentState(
        query="mock query for golden testing",
        twin_snapshot={
            "risk_tolerance": "conservative",
            "investment_horizon": "medium",
            "monthly_income": 150_000.0,
        },
        tool_outputs=[
            {"tool": "intent_classifier", "output": {"intent": "portfolio"}},
            {"tool": "context_assembler", "output": {"twin": {}}},
        ],
        candidate=Recommendation(
            summary="Mock portfolio summary",
            analysis="Mock analysis with numeric content 42% allocation to verify citation guard.",
            risks=["Mock risk"],
            actions=["Mock action"],
            confidence=ConfidenceLevel.HIGH,
            citations=[
                Citation(
                    source="mock_tool",
                    detail="Mock citation for golden testing",
                    value="42",
                    retrieved_at=datetime.now(UTC),
                ),
            ],
        ),
    )


@pytest.fixture
def run_pipeline():
    """Return a callable that runs interface.core.answer() in mock mode."""
    os.environ.setdefault("FINROOT_LLM_PROVIDER", "mock")
    from interface.core import answer

    def _run(query: str) -> AgentState:
        return answer(query, mock=True)

    return _run
