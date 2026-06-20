# Interface & Demo — Interface Contract (Wave-7)

> Frozen before dispatch. The demo surface. MUST run fully offline in Mock mode (no API keys).

## The single entry point (both CLI and UI call this)

`src/interface/core.py` (owned by task 01 — CLI task creates it, UI imports it):

```python
def answer(query: str, *, user_id: str = "demo", mock: bool = True) -> AgentState:
    """One-call pipeline: build memory + audit + llm → FinRootOrchestrator.run(query).
    Returns the full AgentState (candidate/final recommendation, plan, tool_outputs,
    critique, verifier_verdict, audit_events) for the caller to render."""
```
- Internally: `MockProvider` when `mock=True`; loads a demo DigitalTwin from `data/samples/twin_profiles.json`.
- Wraps `FinRootOrchestrator(memory=..., audit=..., llm=...).run(query)`.
- Wires W5 reasoning if available (critic/refine/explain) — degrade gracefully if a module is absent.

## Orchestrator API (already built, W4) — for reference
```python
from finroot.agents.orchestrator import FinRootOrchestrator
orch = FinRootOrchestrator(memory=MemoryManager, audit=AuditTrail, llm=Provider)
state: AgentState = orch.run(query)
```

## AgentState fields the UI renders (already built, W1/W4)
```
intent, twin_snapshot, plan (list[str]), tool_outputs (list[dict]),
candidate (Recommendation), critique (dict), verifier_verdict (dict),
final (Recommendation), audit_events (list[AuditEvent]), created_at
```

## Trace event shape (what the reasoning-trace panel renders)
Derived from `audit_events` and `plan`/`tool_outputs`:
```python
{"step": int, "node": str, "action": str, "detail": str, "source": str | None}
```

## Recommendation shape (the answer card) — already built (W1)
```
summary: str, rationale: str, confidence: ConfidenceLevel, risk_band: RiskBand,
citations: list[Citation], action_items: list[str]  # (verify exact fields in schemas/recommendation.py)
```

## CLI (task 01) — `src/interface/cli/`
- `python -m interface.cli "<query>"` and `python -m interface.cli --mock "<query>"`
- Typer app; pretty-prints: answer summary, confidence, risk band, reasoning steps, citations.
- `main.py` exposes `app` (Typer) — referenced by `pyproject.toml` `[project.scripts] finroot=...`.

## Streamlit UI (tasks 02-05) — `src/interface/ui/`
- `app.py` — entry; dark theme; tabs: **Chat**, **Reasoning Trace**, **Digital Twin**, **Harness**.
- `theme.py` — dark finance palette (deep navy/charcoal bg, green/red accents, monospace numbers).
- Mock mode is the DEFAULT (sidebar toggle, defaults ON). No keys needed for the full demo.
- Reliability > flash: every tab must render without throwing even if a backend piece is missing.

## File map (disjoint write-sets)
| Task | Writes |
|------|--------|
| 01 | `src/interface/core.py`, `src/interface/cli/__init__.py`, `src/interface/cli/main.py`, `src/interface/cli/__main__.py`, `tests/unit/test_cli.py` |
| 02 | `src/interface/ui/app.py`, `src/interface/ui/theme.py`, `src/interface/ui/__init__.py` |
| 03 | `src/interface/ui/components/__init__.py`, `src/interface/ui/components/chat.py`, `src/interface/ui/components/trace.py` |
| 04 | `src/interface/ui/components/twin.py` |
| 05 | `src/interface/ui/components/harness.py` |

NOTE: task 02 creates `src/interface/ui/__init__.py` and the `app.py` shell with placeholder tab
imports wrapped in try/except so it runs before 03/04/05 land. Tasks 03/04/05 create
`components/` files. Task 03 owns `components/__init__.py`.
