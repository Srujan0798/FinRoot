"""MarketAnalystAgent — ReAct sub-agent for price + fundamentals.

Extends :class:`~finroot.agents.base.BaseAgent`. On each ``act`` call it:
1. Extracts symbols from ``state.tool_outputs`` (assembled by intent classifier).
2. Calls :class:`~finroot.tools.market.MarketDataTool` for each symbol.
3. Calls :class:`~finroot.tools.fundamentals.FundamentalAnalysisTool` for each symbol.
4. Runs up to 3 ReAct iterations (think → act → observe).

Every tool call emits an audit event via :class:`~finroot.tools.base.BaseTool`.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from finroot.agents.base import BaseAgent
from finroot.audit.trail import AuditTrail
from finroot.llm.base import LLMProvider
from finroot.schemas.state import AgentState
from finroot.tools.base import BaseTool
from finroot.tools.fundamentals import FundamentalInput
from finroot.tools.market import MarketDataInput

logger = logging.getLogger(__name__)

_MAX_REACT_ITERATIONS = 3


class MarketAnalystAgent(BaseAgent):
    """ReAct agent that fetches price data and fundamental ratios for symbols."""

    name = "market_analyst"

    def __init__(
        self,
        llm: LLMProvider,
        tools: list[BaseTool],
        audit: AuditTrail,
    ) -> None:
        super().__init__(llm=llm, tools=tools, audit=audit)

    def act(self, state: AgentState) -> AgentState:
        """Execute the market analysis ReAct loop.

        Symbols are extracted from ``state.tool_outputs`` entries whose
        ``tool`` key is ``"intent_classifier"`` and whose ``output`` contains
        a ``symbols`` list. If no symbols are found, state is returned
        unchanged (no tool calls).
        """
        symbols = self._extract_symbols(state)
        if not symbols:
            logger.info("MarketAnalystAgent: no symbols found; returning state unchanged.")
            return state

        for iteration in range(_MAX_REACT_ITERATIONS):
            logger.debug("MarketAnalystAgent ReAct iteration %d/%d", iteration + 1, _MAX_REACT_ITERATIONS)

            # Think: use LLM to reason about what data we need
            llm_reasoning = self._llm_think(state, symbols, iteration)

            # Plan: determine what data we still need
            actions = self._plan_actions(state, symbols)
            if not actions:
                logger.debug("MarketAnalystAgent: all data collected; stopping early.")
                break

            # Act + Observe: execute each planned action
            for action in actions:
                self._execute_action(state, action)

            # Record LLM reasoning in tool_outputs
            if llm_reasoning:
                state.tool_outputs.append({
                    "agent": self.name,
                    "type": "llm_reasoning",
                    "iteration": iteration + 1,
                    "reasoning": llm_reasoning,
                })

        return state

    def _llm_think(self, state: AgentState, symbols: list[str], iteration: int) -> str | None:
        """Use LLM to reason about the analysis step (ReAct 'think' phase)."""
        try:
            # Build context from existing tool outputs
            existing_data = []
            for entry in state.tool_outputs:
                tool = entry.get("tool", "")
                if tool in ("market_data", "fundamental_analysis"):
                    existing_data.append(f"- {tool}: {entry.get('input', '')}")

            context = f"Symbols: {', '.join(symbols)}\n"
            if existing_data:
                context += f"Data already fetched:\n{''.join(existing_data)}\n"
            else:
                context += "No data fetched yet.\n"

            prompt = (
                f"You are a market analyst agent. Analyze these stock symbols: {', '.join(symbols)}.\n"
                f"Context: {context}\n"
                f"Iteration {iteration + 1} of {_MAX_REACT_ITERATIONS}.\n"
                "What market data and fundamental analysis should be prioritized? "
                "Respond in 2-3 sentences about what to look for."
            )
            result = self.llm.complete(
                prompt=prompt,
                system="You are a financial market analyst. Be concise and focus on actionable insights.",
                temperature=0.3,
                max_tokens=200,
            )
            return result.text
        except Exception as exc:
            logger.debug("MarketAnalystAgent LLM think failed (non-fatal): %s", exc)
            return None

    def _extract_symbols(self, state: AgentState) -> list[str]:
        """Pull symbols from state.tool_outputs (set by intent classifier / context)."""
        for entry in state.tool_outputs:
            tool_name = entry.get("tool", "")
            raw = entry.get("output")

            if tool_name == "intent_classifier":
                syms = self._symbols_from_raw(raw)
                if syms:
                    return syms

            if tool_name == "context_assembler":
                syms = self._symbols_from_raw(raw, nested_key="entities")
                if syms:
                    return syms

        # Fallback: look for any output dict with "symbols"
        for entry in state.tool_outputs:
            raw = entry.get("output")
            if isinstance(raw, dict):
                syms = raw.get("symbols", [])
                if syms:
                    return [str(s) for s in syms if s]

        return []

    @staticmethod
    def _symbols_from_raw(raw: object, nested_key: str | None = None) -> list[str]:
        """Extract symbols list from a raw output value (dict or JSON string)."""
        data: dict | None = None
        if isinstance(raw, dict):
            data = raw
        elif isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    data = parsed
            except (json.JSONDecodeError, TypeError):
                pass

        if data is None:
            return []

        source = data
        if nested_key:
            source = data.get(nested_key, {})
            if not isinstance(source, dict):
                return []

        syms = source.get("symbols", [])
        return [str(s) for s in syms if s]

    def _plan_actions(self, state: AgentState, symbols: list[str]) -> list[dict[str, Any]]:
        """Determine which tools still need to be called for each symbol."""
        # Track what we've already fetched
        fetched: set[tuple[str, str]] = set()
        for entry in state.tool_outputs:
            tool_name = entry.get("tool", "")
            inp = entry.get("input", "")
            fetched.add((tool_name, str(inp)))

        actions: list[dict[str, Any]] = []
        for symbol in symbols:
            market_key = str(MarketDataInput(symbol=symbol))
            if ("market_data", market_key) not in fetched:
                actions.append({
                    "tool": "market_data",
                    "symbol": symbol,
                    "input": MarketDataInput(symbol=symbol),
                })
            fund_key = str(FundamentalInput(symbol=symbol))
            if ("fundamental_analysis", fund_key) not in fetched:
                actions.append({
                    "tool": "fundamental_analysis",
                    "symbol": symbol,
                    "input": FundamentalInput(symbol=symbol),
                })

        return actions

    def _execute_action(self, state: AgentState, action: dict[str, Any]) -> None:
        """Execute a single tool call and append results to state."""
        tool_name: str = action["tool"]
        inp = action["input"]
        logger.debug("MarketAnalystAgent calling %s with %s", tool_name, inp)
        self._call_tool(state, tool_name, inp)


__all__ = ["MarketAnalystAgent"]
