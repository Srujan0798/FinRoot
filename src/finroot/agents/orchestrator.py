"""FinRootOrchestrator — the central reasoning pipeline coordinator.

Instantiates all agents, builds the LangGraph state graph, and runs
queries through the full classify → context → plan → execute → synthesize
pipeline.

Writes: ``src/finroot/agents/orchestrator.py`` (task 05, wave-4; wave-10 update).

Wave-10 update: the orchestrator now wires the canonical
``finroot.workflows.synthesize.ResultSynthesizer`` (query- and domain-aware)
into the graph instead of the older placeholder bridge. The class is
re-exported under the same name for backward compatibility with the
integration tests and downstream callers.
"""

from __future__ import annotations

import logging
from typing import Any

from finroot.agents.base import BaseAgent
from finroot.agents.intent import IntentClassifier
from finroot.audit.trail import AuditTrail
from finroot.llm.base import LLMProvider
from finroot.schemas.state import AgentState
from finroot.workflows.context import ContextAssembler
from finroot.workflows.graph import agent_state_to_graph, build_graph, graph_state_to_agent
from finroot.workflows.synthesize import ResultSynthesizer as _CanonicalSynthesizer

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Re-export the canonical synthesizer so the orchestrator (and its
# callers) get the query-aware, evidence-cited version. The class
# shape is unchanged: ``synthesizer.synthesize(state) -> Recommendation``.
# ------------------------------------------------------------------


class ResultSynthesizer(_CanonicalSynthesizer):
    """Backward-compatible alias for the canonical :class:`ResultSynthesizer`.

    Inherits all behaviour from
    :class:`finroot.workflows.synthesize.ResultSynthesizer` so the graph
    and integration tests see the same API while the pipeline produces
    the query- and domain-aware recommendations introduced in wave-10.
    """


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
