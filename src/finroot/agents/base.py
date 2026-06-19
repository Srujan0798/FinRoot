"""Abstract base for every FinRoot agent.

Holds the :class:`~finroot.llm.base.LLMProvider`, a list of
:class:`~finroot.tools.base.BaseTool` instances, and an
:class:`~finroot.audit.trail.AuditTrail`. The core loop is::

    final_state = agent.act(initial_state)

Subclasses implement :meth:`act` with their own reasoning loop
(ReAct, plan-then-execute, etc.).
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from finroot.audit.trail import AuditTrail
from finroot.llm.base import LLMProvider
from finroot.schemas.recommendation import Citation
from finroot.schemas.state import AgentState
from finroot.tools.base import BaseTool

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base for every FinRoot agent.

    Subclasses must set ``name`` and implement :meth:`act`.
    """

    name: str
    """Subclass must set this."""

    tools: list[BaseTool]
    """Subclass may provide a default list; overridable via init."""

    def __init__(
        self,
        llm: LLMProvider,
        tools: list[BaseTool],
        audit: AuditTrail,
    ) -> None:
        self.llm = llm
        self.tools = list(tools)
        self.audit = audit

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @abstractmethod
    def act(self, state: AgentState) -> AgentState:
        """Execute one full reasoning cycle.

        Args:
            state: the current :class:`AgentState`.

        Returns:
            A new (or mutated) :class:`AgentState` with the next pipeline
            stage populated.
        """

    # ------------------------------------------------------------------
    # Tool helper — call a named tool and record a citation
    # ------------------------------------------------------------------

    def _call_tool(self, state: AgentState, tool_name: str, inp: Any) -> Any:
        """Find a tool by *tool_name*, call it with *inp*, and record a
        :class:`Citation` in *state*.

        Args:
            state: the current agent state (mutated in-place for
                   ``tool_outputs``).
            tool_name: must match ``tool.name`` of one registered tool.
            inp: passed to the tool's ``__call__``.

        Returns:
            The tool's output (typed per the tool's ``Out`` type var).

        Raises:
            ValueError: if *tool_name* is not registered.
        """
        tool = self._find_tool(tool_name)
        result = tool(inp)

        citation = Citation(
            source=tool_name,
            detail=str(inp) if inp is not None else "",
            value=str(result)[:200] if result is not None else None,
            retrieved_at=datetime.now(UTC),
        )
        state.tool_outputs.append({
            "tool": tool_name,
            "input": str(inp) if inp is not None else None,
            "output": str(result)[:500] if result is not None else None,
        })

        if state.candidate is not None:
            state.candidate.citations.append(citation)

        return result

    def _find_tool(self, name: str) -> BaseTool:
        for t in self.tools:
            if t.name == name:
                return t
        raise ValueError(
            f"Agent {self.name!r} has no tool named {name!r}. "
            f"Registered: {[t.name for t in self.tools]}"
        )


__all__ = ["BaseAgent"]
