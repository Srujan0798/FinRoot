"""The user-facing output contract for FinRoot.

A `Recommendation` is what the agent shows the user. It is the only object
that should cross the agent->user boundary. The `citations` field is the
structural FM-11 guard: if `analysis` contains any digit, the model is
invalid without at least one citation.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from finroot.schemas.enums import ConfidenceLevel

_NAIVE_DT_MSG = "must be timezone-aware (UTC)"
_DIGIT_RE = re.compile(r"\d")


def _to_utc(v: datetime) -> datetime:
    if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
        raise ValueError(_NAIVE_DT_MSG)
    return v.astimezone(UTC)


class Citation(BaseModel):
    """A single piece of evidence backing a recommendation.

    `source` is the tool name (e.g. `yfinance`, `tax_tables`, `portfolio_twin`)
    or upstream data source. `value` carries the figure when numeric.
    """

    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1, description="Tool or data source name")
    detail: str = Field(min_length=1, description="What was retrieved")
    value: str | None = Field(default=None, description="The figure/fact, if numeric")
    retrieved_at: datetime

    @field_validator("source", "detail")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must be a non-empty string")
        return v

    @field_validator("retrieved_at")
    @classmethod
    def _utc_aware(cls, v: datetime) -> datetime:
        return _to_utc(v)


class Recommendation(BaseModel):
    """The user-facing output. Only this object should be shown to the user.

    Invariants (enforced structurally, see `model_validator`):
    * `confidence` is always set.
    * If `analysis` contains any digit and `citations` is empty -> invalid.
    * This catches "looks-like-a-fact" prose that has no evidence attached
      (FM-11). Pure qualitative prose is allowed to ship without citations.
    """

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)
    analysis: str = Field(min_length=1)
    risks: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel
    citations: list[Citation] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    invalidation_conditions: list[str] = Field(default_factory=list)

    @field_validator("summary", "analysis")
    @classmethod
    def _non_empty_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must be a non-empty string")
        return v

    @field_validator("risks", "actions", "alternatives", "assumptions", "invalidation_conditions")
    @classmethod
    def _no_blank_items(cls, v: list[str]) -> list[str]:
        for i, item in enumerate(v):
            if not item or not item.strip():
                raise ValueError(f"item at index {i} must be a non-empty string")
        return v

    @model_validator(mode="after")
    def _numeric_content_needs_citation(self) -> Recommendation:
        if _DIGIT_RE.search(self.analysis) and not self.citations:
            raise ValueError(
                "Recommendation.analysis contains numeric content but citations is empty. "
                "Every numeric claim must cite its source (FM-11)."
            )
        return self


__all__ = ["Citation", "Recommendation"]
