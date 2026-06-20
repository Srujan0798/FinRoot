"""Tests for the FinRoot FastAPI API (wave-7, task 07)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from interface.api.app import app
from interface.api.models import HealthResponse, QueryRequest, QueryResponse

client = TestClient(app)


class TestHealth:
    def test_health_returns_200(self) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_response_shape(self) -> None:
        resp = client.get("/health")
        body = resp.json()
        assert "status" in body
        assert "version" in body
        assert "test_count" in body
        assert body["status"] == "ok"
        assert body["version"] == "0.1.0"

    def test_health_valid_response_model(self) -> None:
        resp = client.get("/health")
        model = HealthResponse(**resp.json())
        assert model.status == "ok"


class TestQuery:
    def test_query_returns_200(self) -> None:
        resp = client.post("/query", json={"query": "What is my portfolio risk?"})
        assert resp.status_code == 200

    def test_query_response_shape(self) -> None:
        resp = client.post("/query", json={"query": "Review my holdings"})
        body = resp.json()
        assert "summary" in body
        assert "confidence" in body
        assert "risk_band" in body
        assert "citations" in body
        assert "reasoning_trace" in body
        assert "audit_events" in body

    def test_query_valid_response_model(self) -> None:
        resp = client.post("/query", json={"query": "What are the risks?"})
        model = QueryResponse(**resp.json())
        assert isinstance(model.summary, str) and len(model.summary) > 0
        assert model.confidence in ("high", "medium", "low", "insufficient")

    def test_query_mock_mode_default(self) -> None:
        """Default mock=True should work (no live API calls)."""
        resp = client.post("/query", json={"query": "Hello"})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["summary"]) > 0

    def test_query_custom_user_id(self) -> None:
        resp = client.post(
            "/query", json={"query": "Analyze risks", "user_id": "api_test_user"}
        )
        assert resp.status_code == 200

    def test_query_explicit_mock_true(self) -> None:
        resp = client.post("/query", json={"query": "Test", "mock": True})
        assert resp.status_code == 200

    def test_query_bad_empty_query_returns_422(self) -> None:
        resp = client.post("/query", json={"query": ""})
        assert resp.status_code == 422

    def test_query_missing_query_returns_422(self) -> None:
        resp = client.post("/query", json={})
        assert resp.status_code == 422

    def test_query_reasoning_trace_is_list(self) -> None:
        resp = client.post("/query", json={"query": "Portfolio check"})
        body = resp.json()
        assert isinstance(body["reasoning_trace"], list)

    def test_query_citations_are_list(self) -> None:
        resp = client.post("/query", json={"query": "Tax optimization"})
        body = resp.json()
        assert isinstance(body["citations"], list)


class TestMetrics:
    def test_metrics_returns_200(self) -> None:
        resp = client.get("/metrics")
        assert resp.status_code == 200

    def test_metrics_contains_systems(self) -> None:
        resp = client.get("/metrics")
        body = resp.json()
        if "error" not in body:
            assert "systems" in body or "finroot" in str(body)


class TestModels:
    def test_query_request_defaults(self) -> None:
        req = QueryRequest(query="test")
        assert req.query == "test"
        assert req.user_id == "demo"
        assert req.mock is True

    def test_query_request_custom(self) -> None:
        req = QueryRequest(query="test", user_id="custom", mock=False)
        assert req.user_id == "custom"
        assert req.mock is False

    def test_query_request_empty_query_rejected(self) -> None:
        with pytest.raises(ValidationError):
            QueryRequest(query="")

    def test_health_response_model(self) -> None:
        h = HealthResponse(status="ok", version="0.1.0", test_count=42)
        assert h.test_count == 42

    def test_health_response_defaults(self) -> None:
        """TestResponse doesn't have defaults, but ensure we can construct."""
        h = HealthResponse(status="degraded", version="0.2.0", test_count=0)
        assert h.status == "degraded"
