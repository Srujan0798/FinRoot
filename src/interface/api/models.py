"""Pydantic request/response models for the FastAPI API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, description="The user's financial query")
    user_id: str = Field(default="demo", description="Stable user identifier")
    mock: bool = Field(default=True, description="Use offline mock LLM provider")


class QueryResponse(BaseModel):
    summary: str
    confidence: str
    risk_band: str
    citations: list[dict]
    reasoning_trace: list[dict]
    audit_events: list[dict]


class HealthResponse(BaseModel):
    status: str
    version: str
    # Honest name kept as test_count for API stability: count of unit test *files*
    # under tests/unit/ (not assertion count). See handle_health docs.
    test_count: int
    mode: str = "single-user-local"
    llm_default: str = "mock"


__all__ = ["HealthResponse", "QueryRequest", "QueryResponse"]
