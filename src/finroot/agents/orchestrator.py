"""FinRootOrchestrator — the central reasoning pipeline coordinator.

Instantiates all agents, builds the LangGraph state graph, and runs
queries through the full classify → context → plan → execute → synthesize
pipeline.

Writes: ``src/finroot/agents/orchestrator.py`` (task 05, wave-4).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from finroot.agents.base import BaseAgent
from finroot.agents.intent import IntentClassifier
from finroot.audit.trail import AuditTrail
from finroot.llm.base import LLMProvider
from finroot.schemas.enums import ConfidenceLevel, Intent
from finroot.schemas.recommendation import Citation, Recommendation
from finroot.schemas.state import AgentState
from finroot.workflows.context import ContextAssembler
from finroot.workflows.graph import agent_state_to_graph, build_graph, graph_state_to_agent

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Minimal synthesizer (the full version lives in workflows/synthesize.py
# which is Forbid for this task — this is the smallest correct bridge)
# ------------------------------------------------------------------


class ResultSynthesizer:
    """Build a :class:`Recommendation` from the current :class:`AgentState`.

    If sub-agents produced tool outputs, those are summarised into the
    recommendation. If no agents ran (GENERAL intent), a direct greeting
    response is returned.
    """

    def synthesize(self, state: AgentState) -> Recommendation:
        """Produce the final :class:`Recommendation` from *state*.

        Parameters
        ----------
        state:
            The fully-populated :class:`AgentState` (post-execute).

        Returns
        -------
        Recommendation
            The user-facing output with summary, analysis, risks, actions,
            confidence, and citations.
        """
        tool_outputs = state.tool_outputs
        intent = state.intent or Intent.GENERAL

        # Collect agent-produced outputs (filter out infra tool outputs)
        agent_outputs = [
            o for o in tool_outputs
            if isinstance(o, dict) and "agent" in o
        ]
        errors = [
            o for o in agent_outputs
            if o.get("type") == "error"
        ]

        # Build citations from tool outputs
        citations: list[Citation] = []
        now = datetime.now(UTC)
        for o in tool_outputs:
            if isinstance(o, dict) and o.get("tool") and o.get("output"):
                citations.append(Citation(
                    source=str(o["tool"]),
                    detail=f"Output from {o['tool']}",
                    value=str(o["output"])[:200],
                    retrieved_at=now,
                ))

        # No agents ran → direct response
        if not agent_outputs and intent == Intent.GENERAL:
            return Recommendation(
                summary="Hello! How can I help you with your finances today?",
                analysis=(
                    "I can assist with portfolio analysis, risk assessment, "
                    "tax planning, market data, and news sentiment. "
                    "Please describe what you'd like to explore."
                ),
                risks=[],
                actions=["Ask a specific financial question to get started."],
                alternatives=[],
                confidence=ConfidenceLevel.HIGH,
                citations=[],
                assumptions=[],
                invalidation_conditions=[],
            )

        # Build summary from agent outputs
        summary_parts: list[str] = []
        analysis_parts: list[str] = []
        risk_parts: list[str] = []
        action_parts: list[str] = []

        for o in agent_outputs:
            agent_name = o.get("agent", "unknown")
            otype = o.get("type", "")

            if otype == "tax_computation":
                gain = o.get("gain", 0)
                gain_type = o.get("gain_type", "")
                tax_amount = o.get("tax_amount", 0)
                rate = o.get("effective_rate_pct", 0)
                rule = o.get("rule_applied", "")
                summary_parts.append(
                    f"Tax on ₹{gain:,.0f} {gain_type}: ₹{tax_amount:,.2f} "
                    f"(effective rate {rate:.2f}%)"
                )
                analysis_parts.append(
                    f"TaxPlanner computed ₹{tax_amount:,.2f} tax on a "
                    f"₹{gain:,.0f} {gain_type} gain. Rule: {rule}. "
                    f"Breakdown: {o.get('breakdown', {})}"
                )
                action_parts.append("Review the tax computation and plan advance tax payments if needed.")

            elif otype == "risk_metrics":
                vol = o.get("volatility_annual", 0)
                var = o.get("var_95", 0)
                sharpe = o.get("sharpe_ratio")
                max_dd = o.get("max_drawdown", 0)
                summary_parts.append(
                    f"Risk metrics: volatility={vol:.4f}, VaR95={var:.4f}, "
                    f"max drawdown={max_dd:.4f}"
                )
                analysis_parts.append(
                    f"Annualised volatility: {vol:.4f}. "
                    f"95% VaR: {var:.4f}. "
                    f"95% CVaR: {o.get('cvar_95', 0):.4f}. "
                    f"Sharpe ratio: {sharpe if sharpe is not None else 'N/A (zero std)'}. "
                    f"Maximum drawdown: {max_dd:.4f}."
                )
                if max_dd > 0.2:
                    risk_parts.append(f"High max drawdown ({max_dd:.2%}) indicates significant downside risk.")

            elif otype == "allocation_analysis":
                alloc = o.get("current_allocation", [])
                if alloc:
                    alloc_str = ", ".join(
                        f"{a.get('symbol')}: {a.get('weight', 0):.2%}"
                        for a in alloc
                    )
                    summary_parts.append(f"Current allocation: {alloc_str}")
                    analysis_parts.append(f"Portfolio allocation: {alloc_str}.")

            elif otype == "monte_carlo":
                exp_ret = o.get("expected_return", 0)
                prob_loss = o.get("probability_of_loss", 0)
                summary_parts.append(
                    f"Monte Carlo: expected return={exp_ret:.2%}, "
                    f"probability of loss={prob_loss:.2%}"
                )
                analysis_parts.append(
                    f"Monte Carlo simulation: expected return {exp_ret:.2%}, "
                    f"probability of loss {prob_loss:.2%}."
                )
                if prob_loss > 0.4:
                    risk_parts.append(f"High probability of loss ({prob_loss:.2%}).")

            elif otype == "error":
                summary_parts.append(f"{agent_name}: error — {o.get('error', 'unknown')}")

            elif otype == "diagnostic":
                summary_parts.append(f"{agent_name}: {o.get('message', '')}")

        if not summary_parts:
            summary_parts.append(f"Processed intent: {intent.value}")

        confidence = ConfidenceLevel.MEDIUM
        if errors:
            confidence = ConfidenceLevel.LOW
        elif not agent_outputs:
            confidence = ConfidenceLevel.HIGH

        return Recommendation(
            summary=" | ".join(summary_parts),
            analysis="\n\n".join(analysis_parts) if analysis_parts else f"Intent: {intent.value}. No detailed analysis produced.",
            risks=risk_parts if risk_parts else ["No specific risks identified."],
            actions=action_parts if action_parts else ["Review the analysis and consult a financial advisor if needed."],
            alternatives=[],
            confidence=confidence,
            citations=citations,
            assumptions=["Analysis based on available tool outputs and user query."],
            invalidation_conditions=["Data freshness may affect accuracy."],
        )


# ------------------------------------------------------------------
# Orchestrator
# ------------------------------------------------------------------


class FinRootOrchestrator:
    """Central coordinator that wires agents, graph, memory, and audit.

    Parameters
    ----------
    memory:
        The :class:`MemoryManager` facade.
    audit:
        The :class:`AuditTrail` for tamper-evident logging.
    llm:
        The :class:`LLMProvider` to inject into sub-agents.
    """

    def __init__(
        self,
        memory: Any,
        audit: AuditTrail,
        llm: LLMProvider,
    ) -> None:
        self._memory = memory
        self._audit = audit
        self._llm = llm

        self._intent_classifier = IntentClassifier()
        self._context_assembler = ContextAssembler()
        self._synthesizer = ResultSynthesizer()

        self._agent_map: dict[str, BaseAgent] = {}
        self._build_agents()

        self._graph = build_graph(
            intent_classifier=self._intent_classifier,
            context_assembler=self._context_assembler,
            agent_map=self._agent_map,
            memory=self._memory,
            synthesizer=self._synthesizer,
        ).compile()

    def _build_agents(self) -> None:
        """Instantiate all sub-agents and register them in the agent map.

        Uses lazy imports to avoid hard dependency on all agent modules
        at init time.
        """
        try:
            from finroot.agents.market_agent import MarketAnalystAgent
            from finroot.tools.fundamentals import FundamentalAnalysisTool
            from finroot.tools.market import MarketDataTool
            from finroot.tools.news import NewsSearchTool
            from finroot.tools.sentiment import SentimentAnalysisTool

            market_tools = [
                MarketDataTool(audit=self._audit, mock=True),
                FundamentalAnalysisTool(audit=self._audit),
            ]
            self._agent_map["market_analyst"] = MarketAnalystAgent(
                llm=self._llm, tools=market_tools, audit=self._audit,
            )

            news_tools = [
                NewsSearchTool(mock=True, audit=self._audit),
                SentimentAnalysisTool(mock=True, audit=self._audit),
            ]
            from finroot.agents.news_agent import NewsInterpreterAgent
            self._agent_map["news_interpreter"] = NewsInterpreterAgent(
                llm=self._llm, tools=news_tools, audit=self._audit,
            )
        except ImportError as exc:
            logger.warning("Could not load market/news agents: %s", exc)

        try:
            from finroot.agents.risk_agent import RiskAssessorAgent
            from finroot.tools.portfolio_sim import PortfolioSimulatorTool
            from finroot.tools.risk import RiskCalculationTool

            risk_tools = [
                RiskCalculationTool(audit=self._audit),
                PortfolioSimulatorTool(audit=self._audit, mock=True),
            ]
            self._agent_map["risk_assessor"] = RiskAssessorAgent(
                llm=self._llm, tools=risk_tools, audit=self._audit,
            )
        except ImportError as exc:
            logger.warning("Could not load risk agent: %s", exc)

        try:
            from finroot.agents.portfolio_agent import PortfolioOptimizerAgent

            self._agent_map["portfolio_optimizer"] = PortfolioOptimizerAgent(
                llm=self._llm, audit=self._audit,
            )
        except ImportError as exc:
            logger.warning("Could not load portfolio agent: %s", exc)

        try:
            from finroot.agents.tax_agent import TaxPlannerAgent

            self._agent_map["tax_planner"] = TaxPlannerAgent(
                llm=self._llm, audit=self._audit,
            )
        except ImportError as exc:
            logger.warning("Could not load tax agent: %s", exc)

    @property
    def agent_map(self) -> dict[str, BaseAgent]:
        """Registered agent instances (read-only)."""
        return dict(self._agent_map)

    @property
    def graph(self) -> Any:
        """The compiled LangGraph state graph."""
        return self._graph

    def run(self, query: str) -> AgentState:
        """Run the full reasoning pipeline for *query*.

        Parameters
        ----------
        query:
            The raw user query string.

        Returns
        -------
        AgentState
            The final state with ``candidate`` populated.

        Raises
        ------
        TypeError
            If *query* is not a ``str``.
        """
        if not isinstance(query, str):
            raise TypeError(f"query must be str, got {type(query).__name__}")

        initial_state = AgentState(query=query)

        self._audit.append("orchestrator.run", {"query": query})

        graph_input = agent_state_to_graph(initial_state)
        result = self._graph.invoke(graph_input)

        final_state = graph_state_to_agent(result)

        self._audit.append("orchestrator.done", {
            "query": query,
            "intent": final_state.intent.value if final_state.intent else None,
            "has_candidate": final_state.candidate is not None,
        })

        return final_state


__all__ = ["FinRootOrchestrator", "ResultSynthesizer"]
