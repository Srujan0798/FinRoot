"""Tests for IntentClassifier and ContextAssembler (wave-4, task 01).

Covers
------
* Each intent classification with keyword match (7 intents).
* Entity extraction: NSE/BSE tickers, timeframes.
* Default → GENERAL for ambiguous queries.
* Confidence values: 1.0 exact, 0.7 partial, 0.5 default.
* Context assembly with mock memory.
* Context handles missing twin (KeyError → empty dict).
* TypeError on non-str input.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from finroot.agents.intent import IntentClassifier
from finroot.memory.digital_twin import (
    DigitalTwin,
    InvestmentHorizon,
    RiskTolerance,
)
from finroot.schemas.enums import Intent
from finroot.schemas.state import AgentState
from finroot.workflows.context import ContextAssembler

UTC_NOW = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# IntentClassifier tests
# ---------------------------------------------------------------------------


class TestIntentClassifier:
    """Intent classification and entity extraction."""

    def setup_method(self) -> None:
        self.clf = IntentClassifier()

    # -- keyword intent tests --

    def test_portfolio_keyword(self) -> None:
        result = self.clf.classify("show me my portfolio allocation")
        assert result.intent == Intent.PORTFOLIO
        assert result.confidence == 1.0

    def test_risk_keyword(self) -> None:
        result = self.clf.classify("what is the risk of this stock")
        assert result.intent == Intent.RISK
        assert result.confidence == 1.0

    def test_tax_keyword(self) -> None:
        result = self.clf.classify("how much tax do I owe on capital gains")
        assert result.intent == Intent.TAX
        assert result.confidence == 1.0

    def test_news_impact_keyword(self) -> None:
        result = self.clf.classify("what is the current price of RELIANCE.NS")
        assert result.intent == Intent.NEWS_IMPACT
        assert result.confidence == 1.0

    def test_cashflow_keyword(self) -> None:
        result = self.clf.classify("show my monthly cashflow breakdown")
        assert result.intent == Intent.CASHFLOW
        assert result.confidence == 1.0

    def test_credit_keyword(self) -> None:
        result = self.clf.classify("should I take a loan for this")
        assert result.intent == Intent.CREDIT
        assert result.confidence == 1.0

    def test_general_greeting_keyword(self) -> None:
        result = self.clf.classify("hello, can you help me")
        assert result.intent == Intent.GENERAL
        assert result.confidence == 1.0

    # -- default / ambiguous --

    def test_default_general_advice(self) -> None:
        result = self.clf.classify("tell me something interesting")
        assert result.intent == Intent.GENERAL
        assert result.confidence == 0.5
        assert "default" in result.reasoning.lower()

    # -- entity extraction --

    def test_extract_nse_symbol(self) -> None:
        result = self.clf.classify("price of RELIANCE.NS")
        assert "RELIANCE.NS" in result.entities["symbols"]

    def test_extract_bse_symbol(self) -> None:
        result = self.clf.classify("INFY and TCS analysis")
        assert "INFY" in result.entities["symbols"]
        assert "TCS" in result.entities["symbols"]

    def test_extract_timeframe_years(self) -> None:
        result = self.clf.classify("show returns for 5 years")
        assert result.entities["timeframe"] == "5 years"

    def test_extract_timeframe_months(self) -> None:
        result = self.clf.classify("last 6 months performance")
        assert result.entities["timeframe"] == "6 months"

    def test_extract_timeframe_singular(self) -> None:
        result = self.clf.classify("last 1 year performance")
        assert result.entities["timeframe"] == "1 year"

    def test_no_entities(self) -> None:
        result = self.clf.classify("hello")
        assert result.entities["symbols"] == []
        assert result.entities["timeframe"] is None

    # -- edge cases --

    def test_type_error_on_non_str(self) -> None:
        with pytest.raises(TypeError, match="query must be str"):
            self.clf.classify(123)  # type: ignore[arg-type]

    def test_empty_query_defaults(self) -> None:
        result = self.clf.classify("")
        assert result.intent == Intent.GENERAL
        assert result.confidence == 0.5

    def test_intent_result_is_frozen(self) -> None:
        result = self.clf.classify("portfolio")
        with pytest.raises(ValidationError):
            result.confidence = 0.9  # type: ignore[misc]

    def test_multiple_symbols(self) -> None:
        result = self.clf.classify("compare RELIANCE.NS INFY TCS.NS")
        assert len(result.entities["symbols"]) >= 3


# ---------------------------------------------------------------------------
# ContextAssembler tests
# ---------------------------------------------------------------------------


def _make_twin(user_id: str = "u1") -> DigitalTwin:
    """Build a minimal valid DigitalTwin for testing."""
    return DigitalTwin(
        user_id=user_id,
        name="Test User",
        age=30,
        risk_tolerance=RiskTolerance.MODERATE,
        investment_horizon=InvestmentHorizon.MEDIUM,
        monthly_income=100_000.0,
        monthly_expenses=50_000.0,
        tax_bracket_pct=20.0,
        goals=["retirement"],
        constraints=["no crypto"],
        holdings=[],
        created_at=UTC_NOW,
        updated_at=UTC_NOW,
    )


def _mock_memory(
    *,
    twin: DigitalTwin | None = None,
    messages: list[dict[str, str]] | None = None,
    recall_results: list[dict[str, Any]] | None = None,
) -> MagicMock:
    """Build a mock MemoryManager."""
    mem = MagicMock()
    mem.user_id = "u1"
    if twin is not None:
        mem.get_twin.return_value = twin
    else:
        mem.get_twin.side_effect = KeyError("no twin for u1")
    mem.get_context.return_value = messages or []
    mem.recall.return_value = recall_results or []
    return mem


class TestContextAssembler:
    """Context assembly from AgentState + MemoryManager."""

    def setup_method(self) -> None:
        self.assembler = ContextAssembler()

    def test_assemble_basic(self) -> None:
        twin = _make_twin()
        mem = _mock_memory(twin=twin)
        state = AgentState(query="show my portfolio")
        result = self.assembler.assemble(state, mem)
        assert result["query"] == "show my portfolio"
        assert result["twin"]["user_id"] == "u1"
        assert result["intent"] is None
        assert isinstance(result["tools_available"], list)

    def test_assemble_with_intent(self) -> None:
        mem = _mock_memory(twin=_make_twin())
        state = AgentState(query="risk check", intent=Intent.RISK)
        result = self.assembler.assemble(state, mem)
        assert result["intent"] == "risk"

    def test_assemble_missing_twin(self) -> None:
        mem = _mock_memory(twin=None)
        state = AgentState(query="hello")
        result = self.assembler.assemble(state, mem)
        assert result["twin"] == {}

    def test_assemble_recent_history(self) -> None:
        history = [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "second"},
            {"role": "user", "content": "third"},
        ]
        mem = _mock_memory(twin=_make_twin(), messages=history)
        state = AgentState(query="next")
        result = self.assembler.assemble(state, mem)
        assert len(result["relevant_history"]) == 3
        assert result["relevant_history"][0]["content"] == "first"

    def test_assemble_limits_history_to_5(self) -> None:
        history = [{"role": "user", "content": f"turn {i}"} for i in range(10)]
        mem = _mock_memory(twin=_make_twin(), messages=history)
        state = AgentState(query="latest")
        result = self.assembler.assemble(state, mem)
        assert len(result["relevant_history"]) == 5

    def test_assemble_semantic_recall(self) -> None:
        recall = [{"text": "past fact", "metadata": {}, "score": 0.9}]
        mem = _mock_memory(twin=_make_twin(), recall_results=recall)
        state = AgentState(query="what was that fact")
        result = self.assembler.assemble(state, mem)
        assert len(result["semantic_recall"]) == 1
        mem.recall.assert_called_once_with("what was that fact", k=5)

    def test_tools_available_names(self) -> None:
        mem = _mock_memory(twin=_make_twin())
        state = AgentState(query="test")
        result = self.assembler.assemble(state, mem)
        assert "market_data" in result["tools_available"]
        assert "risk_calculation" in result["tools_available"]
        assert "tax_rule" in result["tools_available"]
