"""Route handlers for the FinRoot FastAPI API."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from interface.api.models import HealthResponse, QueryRequest, QueryResponse
from interface.core import answer, build_trace

logger = logging.getLogger(__name__)

_METRICS_PATH = Path("results/metrics.json")


def handle_query(body: QueryRequest) -> QueryResponse:
    """POST /query — run the FinRoot pipeline and return results."""
    state = answer(query=body.query, user_id=body.user_id, mock=body.mock)

    rec = state.final or state.candidate

    if rec is not None:
        summary = rec.summary
        confidence = rec.confidence.value if rec.confidence else "unknown"
        citations = [c.model_dump(mode="json") for c in rec.citations]
    else:
        summary = "No recommendation produced."
        confidence = "insufficient"
        citations = []

    # Derive risk_band from verifier verdict if available
    if state.verifier_verdict and isinstance(state.verifier_verdict, dict):
        risk_band = state.verifier_verdict.get("risk_band", "moderate")
    else:
        risk_band = "moderate"

    reasoning_trace = build_trace(state)

    audit_events = [e.model_dump(mode="json") for e in state.audit_events]

    return QueryResponse(
        summary=summary,
        confidence=confidence,
        risk_band=str(risk_band),
        citations=citations,
        reasoning_trace=reasoning_trace,
        audit_events=audit_events,
    )


def handle_health() -> HealthResponse:
    """GET /health — basic service health check."""
    status = "ok"
    version = "0.1.0"
    test_count = _count_tests()
    return HealthResponse(status=status, version=version, test_count=test_count)


def handle_metrics() -> dict:
    """GET /metrics — return FRB benchmark metrics from results/metrics.json."""
    if not _METRICS_PATH.exists():
        logger.warning("Metrics file not found at %s", _METRICS_PATH)
        return {"error": "metrics not available", "path": str(_METRICS_PATH)}
    try:
        data = json.loads(_METRICS_PATH.read_text(encoding="utf-8"))
        return data
    except Exception as exc:
        logger.error("Failed to read metrics: %s", exc)
        return {"error": f"failed to read metrics: {exc}"}


def _count_tests() -> int:
    """Count pytest test files under tests/unit/."""
    test_dir = Path("tests/unit")
    if not test_dir.is_dir():
        return 0
    return sum(1 for f in test_dir.rglob("test_*.py"))


__all__ = ["handle_health", "handle_metrics", "handle_query"]
