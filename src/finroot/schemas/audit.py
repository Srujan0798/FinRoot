"""The `AuditEvent` shape — shared with task 03 (audit backbone).

This module deliberately contains **only the data model**. The hash-chain
construction, append, verify, and replay logic live in `src/finroot/audit/`
(task 03). Keeping the shape here (in `schemas/`) means `AgentState` can
type-annotate `audit_events: list[AuditEvent]` without depending on the
audit machinery, and tests can construct events without standing up a chain.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from finroot.schemas.recommendation import _to_utc  # reuse UTC validator


class AuditEvent(BaseModel):
    """A single event in the tamper-evident hash chain.

    Fields:
    * `ts`: timezone-aware UTC timestamp of the event.
    * `seq`: monotonic sequence number within a chain (0, 1, 2, ...).
    * `type`: a stable event-type identifier. Examples (not enforced here):
        - `task.dispatched`   — orchestrator queued a task for a worker
        - `tool.called`       — a tool/agent was invoked with inputs
        - `step.done`         — a pipeline step finished
        - `critique`          — the 5-axis critic scored a candidate
        - `merge`             — orchestrator merged a worker report
    * `payload`: structured event data (must be JSON-serializable).
    * `prev_hash`: hex sha256 of the previous event in the chain
      (`"0" * 64` for the genesis event).
    * `hash`: hex sha256 of `prev_hash + canonical(payload) + ts + seq`.
      Construction is task 03's job; this model only carries the value.
    """

    model_config = ConfigDict(extra="forbid")

    ts: datetime
    seq: int = Field(ge=0)
    type: str = Field(min_length=1)
    payload: dict = Field(default_factory=dict)
    prev_hash: str = Field(min_length=64, max_length=64)
    hash: str = Field(min_length=64, max_length=64)

    @field_validator("ts")
    @classmethod
    def _utc_aware(cls, v: datetime) -> datetime:
        return _to_utc(v)

    @field_validator("prev_hash", "hash")
    @classmethod
    def _hex(cls, v: str) -> str:
        try:
            int(v, 16)
        except ValueError as e:
            raise ValueError(f"must be a hex string, got {v!r}") from e
        return v.lower()

    @field_validator("type")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("type must be a non-empty string")
        return v


__all__ = ["AuditEvent"]
