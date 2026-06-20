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
    test_count: int


__all__ = ["HealthResponse", "QueryRequest", "QueryResponse"]
