"""Tests for MarketAnalystAgent + NewsInterpreterAgent (wave-4, task 02).

Covers the contract in ``.specify/specs/wave-4/contracts/graph.contract.md`` § Sub-Agents:

* MarketAnalyst with mock tools returns price + fundamental data in tool_outputs
* NewsInterpreter with mock tools returns news + sentiment in tool_outputs
* Empty symbols list → no tool calls, state unchanged
* Audit trail has entries after agent runs
* Agent name correct
"""

from __future__ import annotations

from pathlib import Path
from tempfile import mkdtemp

import pytest

from finroot.agents.market_agent import MarketAnalystAgent
from finroot.agents.news_agent import NewsInterpreterAgent
from finroot.audit.trail import AuditTrail
from finroot.llm.mock import MockProvider
from finroot.schemas.enums import Intent
from finroot.schemas.state import AgentState
from finroot.tools.base import BaseTool
from finroot.tools.fundamentals import FundamentalAnalysisTool, FundamentalInput, FundamentalOutput
from finroot.tools.market import MarketDataInput, MarketDataOutput, MarketDataTool
from finroot.tools.news import NewsInput, NewsOutput, NewsSearchTool
from finroot.tools.sentiment import SentimentAnalysisTool, SentimentInput, SentimentOutput


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state(
    query: str = "Analyze AAPL",
    intent: Intent = Intent.NEWS_IMPACT,
    symbols: list[str] | None = None,
    tool_outputs: list[dict] | None = None,
) -> AgentState:
    """Build an AgentState with optional intent classifier output."""
    outputs = list(tool_outputs or [])
    if symbols is not None:
        outputs.insert(0, {
            "tool": "intent_classifier",
            "input": query,
            "output": {"symbols": symbols, "intent": intent.value},
        })
    return AgentState(
        query=query,
        intent=intent,
        tool_outputs=outputs,
    )


def _make_market_tools(audit: AuditTrail | None = None) -> list[BaseTool]:
    """Create mock market + fundamental tools."""
    return [
        MarketDataTool(audit=audit, mock=True),
        FundamentalAnalysisTool(audit=audit, mock=True),
    ]


def _make_news_tools(audit: AuditTrail | None = None) -> list[BaseTool]:
    """Create mock news + sentiment tools."""
    return [
        NewsSearchTool(audit=audit, mock=True),
        SentimentAnalysisTool(audit=audit, mock=True),
    ]


# ===========================================================================
# MarketAnalystAgent — basic behavior
# ===========================================================================


class TestMarketAnalystAgent:
    def test_agent_name_is_market_analyst(self) -> None:
        audit = AuditTrail(Path(mkdtemp()) / "audit.jsonl")
        agent = MarketAnalystAgent(
            llm=MockProvider(), tools=_make_market_tools(audit), audit=audit,
        )
        assert agent.name == "market_analyst"

    def test_returns_price_data_in_tool_outputs(self) -> None:
        audit = AuditTrail(Path(mkdtemp()) / "audit.jsonl")
        agent = MarketAnalystAgent(
            llm=MockProvider(), tools=_make_market_tools(audit), audit=audit,
        )
        state = _make_state(symbols=["AAPL"])
        result = agent.act(state)

        market_outputs = [
            e for e in result.tool_outputs if e.get("tool") == "market_data"
        ]
        assert len(market_outputs) == 1
        assert "AAPL" in str(market_outputs[0].get("input", ""))

    def test_returns_fundamental_data_in_tool_outputs(self) -> None:
        audit = AuditTrail(Path(mkdtemp()) / "audit.jsonl")
        agent = MarketAnalystAgent(
            llm=MockProvider(), tools=_make_market_tools(audit), audit=audit,
        )
        state = _make_state(symbols=["AAPL"])
        result = agent.act(state)

        fund_outputs = [
            e for e in result.tool_outputs if e.get("tool") == "fundamental_analysis"
        ]
        assert len(fund_outputs) == 1
        assert "AAPL" in str(fund_outputs[0].get("input", ""))

    def test_multiple_symbols_generates_multiple_calls(self) -> None:
        audit = AuditTrail(Path(mkdtemp()) / "audit.jsonl")
        agent = MarketAnalystAgent(
            llm=MockProvider(), tools=_make_market_tools(audit), audit=audit,
        )
        state = _make_state(symbols=["AAPL", "MSFT"])
        result = agent.act(state)

        market_outputs = [
            e for e in result.tool_outputs if e.get("tool") == "market_data"
        ]
        fund_outputs = [
            e for e in result.tool_outputs if e.get("tool") == "fundamental_analysis"
        ]
        assert len(market_outputs) == 2
        assert len(fund_outputs) == 2

    def test_empty_symbols_no_tool_calls_state_unchanged(self) -> None:
        audit = AuditTrail(Path(mkdtemp()) / "audit.jsonl")
        agent = MarketAnalystAgent(
            llm=MockProvider(), tools=_make_market_tools(audit), audit=audit,
        )
        state = _make_state(symbols=[])
        original_outputs = list(state.tool_outputs)
        result = agent.act(state)
        assert result.tool_outputs == original_outputs

    def test_no_intent_classifier_no_symbols_state_unchanged(self) -> None:
        audit = AuditTrail(Path(mkdtemp()) / "audit.jsonl")
        agent = MarketAnalystAgent(
            llm=MockProvider(), tools=_make_market_tools(audit), audit=audit,
        )
        state = AgentState(query="hello", tool_outputs=[])
        result = agent.act(state)
        assert result.tool_outputs == []

    def test_audit_trail_has_entries_after_run(self) -> None:
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        agent = MarketAnalystAgent(
            llm=MockProvider(), tools=_make_market_tools(audit), audit=audit,
        )
        state = _make_state(symbols=["AAPL"])
        agent.act(state)

        events = audit.replay()
        assert len(events) >= 2  # at least market_data + fundamental_analysis
        tool_types = {e.type for e in events}
        assert "tool.called" in tool_types

    def test_tool_outputs_contain_mock_source(self) -> None:
        audit = AuditTrail(Path(mkdtemp()) / "audit.jsonl")
        agent = MarketAnalystAgent(
            llm=MockProvider(), tools=_make_market_tools(audit), audit=audit,
        )
        state = _make_state(symbols=["AAPL"])
        result = agent.act(state)

        for entry in result.tool_outputs:
            if entry.get("tool") in ("market_data", "fundamental_analysis"):
                assert entry.get("output") is not None


# ===========================================================================
# NewsInterpreterAgent — basic behavior
# ===========================================================================


class TestNewsInterpreterAgent:
    def test_agent_name_is_news_interpreter(self) -> None:
        audit = AuditTrail(Path(mkdtemp()) / "audit.jsonl")
        agent = NewsInterpreterAgent(
            llm=MockProvider(), tools=_make_news_tools(audit), audit=audit,
        )
        assert agent.name == "news_interpreter"

    def test_returns_news_in_tool_outputs(self) -> None:
        audit = AuditTrail(Path(mkdtemp()) / "audit.jsonl")
        agent = NewsInterpreterAgent(
            llm=MockProvider(), tools=_make_news_tools(audit), audit=audit,
        )
        state = _make_state(symbols=["AAPL"])
        result = agent.act(state)

        news_outputs = [
            e for e in result.tool_outputs if e.get("tool") == "news_search"
        ]
        assert len(news_outputs) == 1

    def test_returns_sentiment_in_tool_outputs(self) -> None:
        audit = AuditTrail(Path(mkdtemp()) / "audit.jsonl")
        agent = NewsInterpreterAgent(
            llm=MockProvider(), tools=_make_news_tools(audit), audit=audit,
        )
        state = _make_state(symbols=["AAPL"])
        result = agent.act(state)

        sentiment_outputs = [
            e for e in result.tool_outputs if e.get("tool") == "sentiment_analysis"
        ]
        assert len(sentiment_outputs) == 1

    def test_empty_query_no_tool_calls_state_unchanged(self) -> None:
        audit = AuditTrail(Path(mkdtemp()) / "audit.jsonl")
        agent = NewsInterpreterAgent(
            llm=MockProvider(), tools=_make_news_tools(audit), audit=audit,
        )
        state = AgentState(query="", tool_outputs=[])
        result = agent.act(state)
        assert result.tool_outputs == []

    def test_audit_trail_has_entries_after_run(self) -> None:
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        agent = NewsInterpreterAgent(
            llm=MockProvider(), tools=_make_news_tools(audit), audit=audit,
        )
        state = _make_state(symbols=["AAPL"])
        agent.act(state)

        events = audit.replay()
        assert len(events) >= 2  # news_search + sentiment_analysis
        tool_types = {e.type for e in events}
        assert "tool.called" in tool_types

    def test_news_output_has_articles(self) -> None:
        audit = AuditTrail(Path(mkdtemp()) / "audit.jsonl")
        agent = NewsInterpreterAgent(
            llm=MockProvider(), tools=_make_news_tools(audit), audit=audit,
        )
        state = _make_state(symbols=["AAPL"])
        result = agent.act(state)

        news_outputs = [
            e for e in result.tool_outputs if e.get("tool") == "news_search"
        ]
        assert len(news_outputs) == 1
        output_str = news_outputs[0].get("output", "")
        assert output_str  # not empty


# ===========================================================================
# Edge cases / integration
# ===========================================================================


class TestAgentEdgeCases:
    def test_market_agent_preserves_existing_tool_outputs(self) -> None:
        """Agent should append, not overwrite, existing tool_outputs."""
        audit = AuditTrail(Path(mkdtemp()) / "audit.jsonl")
        agent = MarketAnalystAgent(
            llm=MockProvider(), tools=_make_market_tools(audit), audit=audit,
        )
        existing = {"tool": "prior_tool", "input": "x", "output": "y"}
        state = _make_state(symbols=["AAPL"], tool_outputs=[existing])
        result = agent.act(state)

        # First entry is the intent_classifier (prepended by _make_state), then prior, then new
        assert any(e.get("tool") == "prior_tool" for e in result.tool_outputs)
        assert any(e.get("tool") == "market_data" for e in result.tool_outputs)

    def test_news_agent_uses_state_query_as_fallback(self) -> None:
        """When no intent_classifier output, agent falls back to state.query."""
        audit = AuditTrail(Path(mkdtemp()) / "audit.jsonl")
        agent = NewsInterpreterAgent(
            llm=MockProvider(), tools=_make_news_tools(audit), audit=audit,
        )
        state = AgentState(query="What's happening with Indian markets?", tool_outputs=[])
        result = agent.act(state)

        news_outputs = [
            e for e in result.tool_outputs if e.get("tool") == "news_search"
        ]
        assert len(news_outputs) == 1
