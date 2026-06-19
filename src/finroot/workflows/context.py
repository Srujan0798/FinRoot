"""ContextAssembler — build the reasoning context for the planner.

Pulls twin profile, recent working-memory turns, and semantic recall
from :class:`~finroot.memory.manager.MemoryManager` into a flat dict
that downstream nodes can consume.

Contract: `.specify/specs/wave-4/contracts/graph.contract.md` § 1.
"""

from __future__ import annotations

import logging
from typing import Any

from finroot.memory.manager import MemoryManager
from finroot.schemas.state import AgentState

logger = logging.getLogger(__name__)

_TOOLS_AVAILABLE: list[str] = [
    "market_data",
    "fundamental_analysis",
    "news_search",
    "sentiment_analysis",
    "risk_calculation",
    "portfolio_simulator",
    "tax_rule",
    "user_profile",
]


class ContextAssembler:
    """Build the context dict for the planner from AgentState + MemoryManager.

    Returns a dict with keys: ``query``, ``twin``, ``relevant_history``,
    ``intent``, ``tools_available``.
    """

    def assemble(self, state: AgentState, memory: MemoryManager) -> dict[str, Any]:
        """Assemble reasoning context from *state* and *memory*.

        Parameters
        ----------
        state:
            The current :class:`AgentState` (carries the query and intent).
        memory:
            The :class:`MemoryManager` facade for twin, working, and
            semantic stores.

        Returns
        -------
        dict[str, Any]
            Context dict with keys: ``query``, ``twin``, ``relevant_history``,
            ``intent``, ``tools_available``.
        """
        query: str = state.query

        twin_snapshot = self._load_twin(memory)
        recent_history = memory.get_context()[-5:]
        semantic_recall = memory.recall(query, k=5)

        return {
            "query": query,
            "twin": twin_snapshot,
            "relevant_history": recent_history,
            "semantic_recall": semantic_recall,
            "intent": state.intent.value if state.intent else None,
            "tools_available": list(_TOOLS_AVAILABLE),
        }

    @staticmethod
    def _load_twin(memory: MemoryManager) -> dict[str, Any]:
        """Load the twin profile, returning an empty dict on missing twin."""
        try:
            twin = memory.get_twin()
            return twin.model_dump(mode="python")
        except KeyError:
            logger.info("No digital twin found for user %s", memory.user_id)
            return {}


__all__ = ["ContextAssembler"]
