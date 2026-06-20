"""FastAPI application for the FinRoot REST API.

Usage:
    PYTHONPATH=src:. uvicorn interface.api.app:app --port 8000
"""

from __future__ import annotations

import logging

from interface.api.models import QueryRequest
from interface.api.routes import handle_health, handle_metrics, handle_query

logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
except ImportError:
    FastAPI = None  # type: ignore[assignment]
    logger.warning("fastapi not installed — API endpoints unavailable")


def create_app() -> FastAPI | None:
    """Build and return the FastAPI application instance."""
    if FastAPI is None:
        return None

    app = FastAPI(
        title="FinRoot API",
        description="Sovereign, reasoning-first AI financial agent REST API",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.post("/query", response_model=None)
    async def query(body: QueryRequest):
        return handle_query(body)

    @app.get("/health", response_model=None)
    async def health():
        return handle_health()

    @app.get("/metrics", response_model=None)
    async def metrics():
        return handle_metrics()

    return app


app = create_app()

if app is None:

    def _stub_app():
        raise RuntimeError(
            "FastAPI is not installed. Install it with: pip install fastapi uvicorn"
        )

    app = _stub_app  # type: ignore[assignment]


__all__ = ["app"]
