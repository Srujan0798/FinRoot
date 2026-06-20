# Task wave-7/07 — FastAPI REST API

> Read `work/WORKER_PROMPT.md` then build. The missing API layer.

## Objective
Build a FastAPI REST API that exposes the FinRoot pipeline as HTTP endpoints, enabling third-party integration and the architecture diagram's API layer.

## Writes (ONLY these)
- `src/interface/api/__init__.py`
- `src/interface/api/app.py`
- `src/interface/api/routes.py`
- `src/interface/api/models.py`
- `tests/unit/test_api.py`

## Forbid
`src/interface/ui/**`, `src/interface/cli/**`, `src/interface/core.py` (import only).

## Steps
1. `models.py` — Pydantic request/response models:
   - `QueryRequest(query: str, user_id: str = "demo", mock: bool = True)`
   - `QueryResponse(summary: str, confidence: str, risk_band: str, citations: list[dict], reasoning_trace: list[dict], audit_events: list[dict])`
   - `HealthResponse(status: str, version: str, test_count: int)`
2. `app.py` — FastAPI app:
   - `POST /query` → calls `interface.core.answer()` → returns QueryResponse
   - `GET /health` → returns HealthResponse
   - `GET /metrics` → returns FRB metrics from results/metrics.json
   - CORS enabled, mock mode default
3. `routes.py` — route handlers (separate from app for cleanliness)
4. `tests/unit/test_api.py` (min 8): health endpoint returns 200, query endpoint returns valid response, mock mode works, bad query returns 422
5. Guard fastapi import: `try: from fastapi import FastAPI; except ImportError: FastAPI = None`

## Acceptance
```bash
PYTHONPATH=src:. python3 -c "import interface.api.app; print('API app import OK')"
PYTHONPATH=src:. python3 -m pytest tests/unit/test_api.py -v
ruff check src/interface/api/
# If fastapi+uvicorn installed: uvicorn interface.api.app:app --port 8000
```

## Report
`work/reports/wave-7/07-fastapi-api.report.md`
