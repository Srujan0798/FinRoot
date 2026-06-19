"""The LangGraph `AgentState` carried through the reasoning pipeline.

This is the typed message-passing shape between nodes. It must be JSON-
serializable (LangGraph state checkpointing), so all values are Pydantic
models, primitives, or plain dicts. `extra="forbid"` catches typos at the
boundary — the first of the Swiss-cheese layers from the OS setup.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from finroot.schemas.enums import Intent
from finroot.schemas.recommendation import Recommendation

if TYPE_CHECKING:
    from finroot.schemas.audit import AuditEvent


class AgentState(BaseModel):
    """The state object passed between LangGraph nodes.

    Fields are populated incrementally as the pipeline progresses:
    router -> planner -> tools -> synthesizer -> critic -> verifier -> ship.

    Invariants:
    * `extra="forbid"`: unknown fields raise (typo guard).
    * Datetimes are timezone-aware UTC (enforced by sub-models where they
      appear; AgentState itself stores plain dicts and primitives that are
      checkpoint-safe).
    * Lossless JSON round-trip: `model_validate_json(model_dump_json())`
      reconstructs an equal state.
    """

    model_config = ConfigDict(extra="forbid")

    query: str
    intent: Intent | None = None
    twin_snapshot: dict = {}
    plan: list[str] = []
    tool_outputs: list[dict] = []
    candidate: Recommendation | None = None
    critique: dict | None = None
    verifier_verdict: dict | None = None
    final: Recommendation | None = None
    audit_events: list[AuditEvent] = []  # type: ignore[type-arg]
    created_at: datetime | None = None


# Resolve the forward reference to `AuditEvent` (defined in the sibling
# `audit` module). Done at import-time so downstream code can use
# `AgentState` without `model_rebuild()` calls.
def _resolve_forward_refs() -> None:
    from finroot.schemas.audit import AuditEvent  # noqa: F401  (import for side effect)

    AgentState.model_rebuild()


_resolve_forward_refs()


__all__ = ["AgentState"]
