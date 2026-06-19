"""NewsInterpreterAgent — ReAct sub-agent for news search + sentiment.

Extends :class:`~finroot.agents.base.BaseAgent`. On each ``act`` call it:
1. Extracts a search query from ``state.tool_outputs`` or ``state.query``.
2. Calls :class:`~finroot.tools.news.NewsSearchTool` to retrieve articles.
3. Calls :class:`~finroot.tools.sentiment.SentimentAnalysisTool` on article
   summaries.
4. Runs up to 3 ReAct iterations (think → act → observe).

Every tool call emits an audit event via :class:`~finroot.tools.base.BaseTool`.
"""

from __future__ import annotations

import logging

from finroot.agents.base import BaseAgent
from finroot.audit.trail import AuditTrail
from finroot.llm.base import LLMProvider
from finroot.schemas.state import AgentState
from finroot.tools.base import BaseTool
from finroot.tools.news import NewsInput
from finroot.tools.sentiment import SentimentInput

logger = logging.getLogger(__name__)

_MAX_REACT_ITERATIONS = 3


class NewsInterpreterAgent(BaseAgent):
    """ReAct agent that searches news and analyzes sentiment."""

    name = "news_interpreter"

    def __init__(
        self,
        llm: LLMProvider,
        tools: list[BaseTool],
        audit: AuditTrail,
    ) -> None:
        super().__init__(llm=llm, tools=tools, audit=audit)

    def act(self, state: AgentState) -> AgentState:
        """Execute the news interpretation ReAct loop.

        1. Determine search query from state.
        2. Search news articles.
        3. Run sentiment on article summaries.
        """
        query = self._extract_query(state)
        if not query:
            logger.info("NewsInterpreterAgent: no query found; returning state unchanged.")
            return state

        for iteration in range(_MAX_REACT_ITERATIONS):
            logger.debug(
                "NewsInterpreterAgent ReAct iteration %d/%d",
                iteration + 1,
                _MAX_REACT_ITERATIONS,
            )

            # Think: determine what we still need
            needs_news = not self._has_tool_output(state, "news_search")
            needs_sentiment = self._has_tool_output(state, "news_search") and not self._has_tool_output(state, "sentiment_analysis")

            if not needs_news and not needs_sentiment:
                logger.debug("NewsInterpreterAgent: all data collected; stopping early.")
                break

            # Act + Observe
            if needs_news:
                self._search_news(state, query)
            elif needs_sentiment:
                self._analyze_sentiment(state)

        return state

    def _extract_query(self, state: AgentState) -> str:
        """Extract search query from state.tool_outputs or state.query."""
        # Check intent classifier for entities
        for entry in state.tool_outputs:
            if entry.get("tool") == "intent_classifier":
                raw = entry.get("output")
                if isinstance(raw, dict):
                    query = raw.get("query", "")
                    if query:
                        return str(query)
                    # Use entities to build query
                    entities = raw.get("entities", {})
                    symbols = entities.get("symbols", [])
                    if symbols:
                        return " ".join(str(s) for s in symbols)
                if isinstance(raw, str):
                    import json

                    try:
                        parsed = json.loads(raw)
                        if isinstance(parsed, dict):
                            query = parsed.get("query", "")
                            if query:
                                return str(query)
                            entities = parsed.get("entities", {})
                            symbols = entities.get("symbols", [])
                            if symbols:
                                return " ".join(str(s) for s in symbols)
                    except (json.JSONDecodeError, TypeError):
                        pass

        # Check context assembler
        for entry in state.tool_outputs:
            if entry.get("tool") == "context_assembler":
                raw = entry.get("output")
                if isinstance(raw, dict):
                    query = raw.get("query", "")
                    if query:
                        return str(query)
                    entities = raw.get("entities", {})
                    symbols = entities.get("symbols", [])
                    if symbols:
                        return " ".join(str(s) for s in symbols)

        # Fall back to state.query
        if state.query:
            return state.query

        return ""

    def _has_tool_output(self, state: AgentState, tool_name: str) -> bool:
        """Check if state already has output from the named tool."""
        return any(entry.get("tool") == tool_name for entry in state.tool_outputs)

    def _search_news(self, state: AgentState, query: str) -> None:
        """Call NewsSearchTool and append results to state."""
        inp = NewsInput(query=query)
        logger.debug("NewsInterpreterAgent calling news_search with query=%r", query)
        self._call_tool(state, "news_search", inp)

    def _analyze_sentiment(self, state: AgentState) -> None:
        """Extract article summaries from news output and run sentiment analysis."""
        summaries: list[str] = []
        for entry in state.tool_outputs:
            if entry.get("tool") == "news_search":
                raw = entry.get("output")
                # Parse articles from the output string
                if isinstance(raw, str):
                    # The output is a str() of NewsOutput; try to extract summaries
                    # from the tool_outputs entry's structured data
                    import json

                    try:
                        parsed = json.loads(raw)
                        if isinstance(parsed, dict):
                            articles = parsed.get("articles", [])
                            for article in articles:
                                summary = article.get("summary", "")
                                if summary:
                                    summaries.append(summary)
                    except (json.JSONDecodeError, TypeError):
                        # If we can't parse, use the raw string as a single text
                        if raw and raw.strip():
                            summaries.append(raw.strip())

        if not summaries:
            logger.info("NewsInterpreterAgent: no article summaries found for sentiment.")
            return

        inp = SentimentInput(texts=summaries)
        logger.debug("NewsInterpreterAgent calling sentiment_analysis on %d texts", len(summaries))
        self._call_tool(state, "sentiment_analysis", inp)


__all__ = ["NewsInterpreterAgent"]
