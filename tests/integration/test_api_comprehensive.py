"""Comprehensive FastAPI integration tests.

Uses TestClient to exercise health, query, and edge-case endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from interface.api.app import create_app

app = create_app()
assert app is not None, "FastAPI app could not be created"

client = TestClient(app)


# ── Health ────────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_api_health_returns_200():
    """GET /health must return 200."""
    response = client.get("/health")
    assert response.status_code == 200


@pytest.mark.integration
def test_api_health_response_schema():
    """/health response must contain expected fields."""
    response = client.get("/health")
    body = response.json()
    assert "status" in body, "Missing 'status' field"
    assert "version" in body, "Missing 'version' field"
    assert "test_count" in body, "Missing 'test_count' field"
    assert body["status"] == "ok"
    assert isinstance(body["version"], str)
    assert isinstance(body["test_count"], int)


# ── Answer / Query endpoint ──────────────────────────────────────────────


@pytest.mark.integration
def test_api_answer_endpoint_exists():
    """POST /query must exist and accept a JSON body."""
    response = client.post(
        "/query",
        json={"query": "What is compound interest?", "mock": True},
    )
    # 200 for success, but the endpoint must at least exist (not 404/405)
    assert response.status_code != 404, "POST /query endpoint not found"
    assert response.status_code != 405, "POST /query method not allowed"


@pytest.mark.integration
def test_api_answer_empty_body_returns_error():
    """POST /query with an empty body should return 422 (validation error)."""
    response = client.post("/query", json={})
    assert response.status_code == 422, (
        f"Expected 422 for empty body, got {response.status_code}: {response.text[:300]}"
    )


@pytest.mark.integration
def test_api_answer_invalid_json():
    """POST /query with invalid JSON should return 422."""
    response = client.post(
        "/query",
        content="not json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422, (
        f"Expected 422 for invalid JSON, got {response.status_code}: {response.text[:300]}"
    )


# ── CORS ──────────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_api_cors_headers():
    """Responses should include CORS headers (allow-origin)."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    # FastAPI CORS middleware should respond with 200 for preflight
    assert response.status_code == 200
    # The middleware sets Access-Control-Allow-Origin
    assert "access-control-allow-origin" in response.headers, (
        f"Missing CORS headers. Headers: {dict(response.headers)}"
    )
