"""Deliberately weaker baseline systems for comparison.

Both produce AgentState-compatible outputs that the same graders measure,
proving the lift of the full FinRoot pipeline.

These are NOT sandbagged — they simply lack the critic, principles, and
multi-agent orchestration that define the full system (see README.md for
architectural rationale).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from finroot.llm.mock import MockProvider
from finroot.schemas.enums import ConfidenceLevel
from finroot.schemas.recommendation import Citation, Recommendation
from finroot.schemas.state import AgentState

logger = logging.getLogger(__name__)


def _map_confidence(label: str | None) -> ConfidenceLevel:
    mapping = {
        "high": ConfidenceLevel.HIGH,
        "medium": ConfidenceLevel.MEDIUM,
        "low": ConfidenceLevel.LOW,
    }
    return mapping.get(label or "", ConfidenceLevel.MEDIUM)


class NaiveRAGBaseline:
    """Retrieve -> single LLM call -> answer.

    Represents a typical RAG chatbot: no agents, no critic, no principles
    pipeline. The answer is a single call to the LLM with retrieved context
    (the query and optional twin). Citations are weak/absent and there is
    no risk framing or confidence calibration.

    Intentionally weaker than the full FinRoot pipeline to demonstrate
    the lift from multi-agent reasoning, self-critique, and principle
    verification.
    """

    name: str = "rag"

    def __init__(self, llm: MockProvider | None = None) -> None:
        self.llm = llm or MockProvider()

    def answer(self, query: str, twin: dict | None = None) -> AgentState:
        """Produce a naive RAG answer.

        Args:
            query: The user's financial query.
            twin: Optional user profile/twin snapshot (unused in naive RAG).

        Returns:
            An AgentState with a ``final`` Recommendation and a simple
            two-step plan.
        """
        context = self._build_context(twin)
        prompt = self._build_prompt(query, context)
        result = self.llm.complete(prompt)

        rec = Recommendation(
            summary=result.text[:120],
            analysis=result.text,
            confidence=_map_confidence(result.confidence),
        )

        return AgentState(
            query=query,
            twin_snapshot=twin or {},
            plan=["retrieve_context", "generate_answer"],
            final=rec,
            created_at=datetime.now(UTC),
        )

    @staticmethod
    def _build_context(twin: dict | None) -> str:
        if twin is None:
            return ""
        return f"User context: {twin}"

    @staticmethod
    def _build_prompt(query: str, context: str) -> str:
        parts = [f"Question: {query}"]
        if context:
            parts.append(context)
        parts.append("Provide a financial answer.")
        return "\n".join(parts)


class SingleAgentBaseline:
    """Single ReAct-style agent answering via tool call.

    Uses a ReAct loop: decide which tool to call -> call it -> synthesize
    the final answer. Unlike the full FinRoot pipeline, there is no
    multi-agent orchestration, no self-critic, no consistency check, and
    no principles verifier.

    Better than NaiveRAGBaseline (tool-augmented, structured reasoning)
    but still intentionally weaker than the full FinRoot system.
    """

    name: str = "single_agent"

    def __init__(self, llm: MockProvider | None = None) -> None:
        self.llm = llm or MockProvider()

    def answer(self, query: str, twin: dict | None = None) -> AgentState:
        """Run a single-agent ReAct cycle.

        Args:
            query: The user's financial query.
            twin: Optional user profile/twin snapshot.

        Returns:
            An AgentState with ``plan`` (tool selection -> tool call ->
            synthesize), ``tool_outputs``, and ``final`` Recommendation.
        """
        plan = self._decide_plan(query, twin)
        tool_result = self._call_tool(query)
        rec = self._synthesize(query, twin, tool_result)

        return AgentState(
            query=query,
            twin_snapshot=twin or {},
            plan=plan,
            tool_outputs=[tool_result],
            final=rec,
            created_at=datetime.now(UTC),
        )

    def _decide_plan(self, query: str, twin: dict | None) -> list[str]:
        prompt = f"Question: {query}\nDecide which tool to use and return a plan."
        if twin:
            prompt += f"\nUser profile: {twin}"
        self.llm.complete(prompt)
        return ["tool_selection", "tool_call", "synthesize_answer"]

    @staticmethod
    def _call_tool(query: str) -> dict[str, Any]:
        return {
            "tool": "mock_tool",
            "input": query,
            "output": f"Simulated result for: {query[:80]}",
        }

    def _synthesize(
        self,
        query: str,
        twin: dict | None,
        tool_result: dict[str, Any],
    ) -> Recommendation:
        context = self._build_context(twin)
        prompt = (
            f"Question: {query}\n"
            f"Tool result: {tool_result['output']}\n"
            f"{context}\n"
            "Provide a financial recommendation based on the tool result."
        )
        result = self.llm.complete(prompt)

        return Recommendation(
            summary=result.text[:120],
            analysis=result.text,
            confidence=_map_confidence(result.confidence),
            citations=[
                Citation(
                    source="mock_tool",
                    detail=f"Tool result for query: {query[:60]}",
                    value=tool_result["output"][:200],
                    retrieved_at=datetime.now(UTC),
                ),
            ],
        )

    @staticmethod
    def _build_context(twin: dict | None) -> str:
        if twin is None:
            return ""
        return f"User context: {twin}"
