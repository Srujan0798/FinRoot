"""LangGraph state graph — the central reasoning pipeline.

Builds the plan-and-execute orchestrator graph with nodes:
classify_intent → assemble_context → plan → execute_agents → synthesize.

Uses a TypedDict for LangGraph state (avoids forward-ref resolution issues
with Pydantic models that have TYPE_CHECKING-guarded imports). Converts
to/from :class:`AgentState` at the orchestrator boundary.

Contract: `.specify/specs/wave-4/contracts/graph.contract.md` § Plan-and-Execute.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from finroot.agents.intent import IntentClassifier
from finroot.schemas.enums import Intent
from finroot.schemas.recommendation import Recommendation
from finroot.schemas.state import AgentState
from finroot.workflows.context import ContextAssembler

logger = logging.getLogger(__name__)

# Routing map: intent → list of agent names to invoke
_INTENT_AGENT_MAP: dict[Intent, list[str]] = {
    Intent.PORTFOLIO: ["portfolio_optimizer", "risk_assessor"],
    Intent.RISK: ["risk_assessor"],
    Intent.TAX: ["tax_planner"],
    Intent.NEWS_IMPACT: ["market_analyst", "news_interpreter"],
    Intent.CASHFLOW: [],
    Intent.CREDIT: [],
    Intent.GENERAL: [],
}


class GraphState(TypedDict, total=False):
    """TypedDict mirror of AgentState for LangGraph compatibility.

    Replaces complex Pydantic forward-ref fields (AuditEvent) with Any
    so LangGraph's ``get_type_hints`` can resolve the schema.
    """

    query: str
    intent: Intent | None
    twin_snapshot: dict
    plan: list[str]
    tool_outputs: list[dict]
    candidate: Recommendation | None
    critique: dict | None
    verifier_verdict: dict | None
    final: Recommendation | None
    audit_events: list[Any]
    created_at: datetime | None
    retry_count: int


def agent_state_to_graph(state: AgentState) -> GraphState:
    """Convert an :class:`AgentState` to the LangGraph :class:`GraphState`."""
    return {
        "query": state.query,
        "intent": state.intent,
        "twin_snapshot": state.twin_snapshot,
        "plan": state.plan,
        "tool_outputs": state.tool_outputs,
        "candidate": state.candidate,
        "critique": state.critique,
        "verifier_verdict": state.verifier_verdict,
        "final": state.final,
        "audit_events": list(state.audit_events),
        "created_at": state.created_at,
        "retry_count": 0,
    }


def graph_state_to_agent(state: GraphState) -> AgentState:
    """Convert a LangGraph :class:`GraphState` back to :class:`AgentState`."""
    return AgentState(
        query=state.get("query", ""),
        intent=state.get("intent"),
        twin_snapshot=state.get("twin_snapshot", {}),
        plan=state.get("plan", []),
        tool_outputs=state.get("tool_outputs", []),
        candidate=state.get("candidate"),
        critique=state.get("critique"),
        verifier_verdict=state.get("verifier_verdict"),
        final=state.get("final"),
        audit_events=state.get("audit_events", []),
        created_at=state.get("created_at"),
    )


def build_graph(
    intent_classifier: IntentClassifier,
    context_assembler: ContextAssembler,
    agent_map: dict[str, Any],
    memory: Any,
    synthesizer: Any,
) -> StateGraph:
    """Build and return the LangGraph state graph (uncompiled).

    Parameters
    ----------
    intent_classifier:
        The :class:`IntentClassifier` instance.
    context_assembler:
        The :class:`ContextAssembler` instance.
    agent_map:
        Dict mapping agent name → agent instance (BaseAgent subclass).
    memory:
        The :class:`MemoryManager` instance for context assembly.
    synthesizer:
        The :class:`ResultSynthesizer` instance (or compatible).

    Returns
    -------
    StateGraph
        The uncompiled state graph.
    """

    # ------------------------------------------------------------------
    # Node functions — all operate on GraphState (TypedDict)
    # ------------------------------------------------------------------

    def classify_intent(state: GraphState) -> dict[str, Any]:
        """Classify the user query's intent."""
        agent_st = graph_state_to_agent(state)
        result = intent_classifier.classify(agent_st.query)
        logger.info(
            "Intent classified: %s (confidence=%.2f)",
            result.intent.value,
            result.confidence,
        )
        agent_st.tool_outputs.append({
            "tool": "intent_classifier",
            "output": result.model_dump(mode="json"),
        })
        return {
            "intent": result.intent,
            "tool_outputs": list(agent_st.tool_outputs),
        }

    def assemble_context(state: GraphState) -> dict[str, Any]:
        """Assemble reasoning context from state and memory."""
        agent_st = graph_state_to_agent(state)
        context = context_assembler.assemble(agent_st, memory)
        agent_st.tool_outputs.append({
            "tool": "context_assembler",
            "output": context,
        })
        logger.info("Context assembled for intent=%s", state.get("intent"))
        return {
            "twin_snapshot": context.get("twin", {}),
            "tool_outputs": list(agent_st.tool_outputs),
        }

    def select_agents(state: GraphState) -> dict[str, Any]:
        """Select sub-agents based on the classified intent."""
        intent = state.get("intent") or Intent.GENERAL
        selected = _INTENT_AGENT_MAP.get(intent, [])
        logger.info("Plan: selected agents %s for intent=%s", selected, intent.value)
        return {"plan": list(selected)}

    def execute_agents(state: GraphState) -> dict[str, Any]:
        """Invoke selected sub-agents in sequence."""
        selected = state.get("plan", [])
        if not selected:
            logger.info("No agents to execute (plan is empty).")
            return {}

        agent_st = graph_state_to_agent(state)
        for agent_name in selected:
            agent = agent_map.get(agent_name)
            if agent is None:
                logger.warning("Agent %r not found in agent_map; skipping.", agent_name)
                continue
            logger.info("Executing agent: %s", agent_name)
            try:
                agent_st = agent.act(agent_st)
            except Exception as exc:
                logger.error("Agent %s failed: %s", agent_name, exc)
                agent_st.tool_outputs.append({
                    "agent": agent_name,
                    "type": "error",
                    "error": str(exc),
                })

        return {"tool_outputs": list(agent_st.tool_outputs)}

    def synthesize(state: GraphState) -> dict[str, Any]:
        """Synthesize final recommendation from agent outputs."""
        agent_st = graph_state_to_agent(state)
        recommendation = synthesizer.synthesize(agent_st)
        logger.info(
            "Synthesis complete: confidence=%s",
            recommendation.confidence.value,
        )
        return {"candidate": recommendation, "final": recommendation}

    # ------------------------------------------------------------------
    # Routing functions for conditional edges
    # ------------------------------------------------------------------

    def _route_after_classify(state: GraphState) -> str:
        """Route based on intent: GENERAL goes straight to synthesize."""
        intent = state.get("intent") or Intent.GENERAL
        if intent == Intent.GENERAL:
            logger.info("GENERAL intent — skipping agent execution, synthesizing directly.")
            return "synthesize"
        return "assemble_context"

    # ------------------------------------------------------------------
    # Build the graph with conditional edges
    # ------------------------------------------------------------------

    graph = StateGraph(GraphState)

    graph.add_node("classify_intent", classify_intent)
    graph.add_node("assemble_context", assemble_context)
    graph.add_node("select_agents", select_agents)
    graph.add_node("execute_agents", execute_agents)
    graph.add_node("synthesize", synthesize)

    graph.set_entry_point("classify_intent")

    # Conditional: GENERAL intent skips directly to synthesize
    graph.add_conditional_edges(
        "classify_intent",
        _route_after_classify,
        {
            "assemble_context": "assemble_context",
            "synthesize": "synthesize",
        },
    )

    graph.add_edge("assemble_context", "select_agents")
    graph.add_edge("select_agents", "execute_agents")
    graph.add_edge("execute_agents", "synthesize")
    graph.add_edge("synthesize", END)

    return graph


__all__ = [
    "GraphState",
    "agent_state_to_graph",
    "build_graph",
    "graph_state_to_agent",
]
