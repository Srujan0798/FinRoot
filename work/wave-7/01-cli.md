# Task wave-7/01 — Typer CLI + the `answer()` entry point

> Read `work/WORKER_PROMPT.md` then build. DEMO-CRITICAL. Depends on W4 (orchestrator, done).

## Objective
Build the single `answer()` entry point that both CLI and UI use, plus a polished Typer CLI that
runs the full pipeline in Mock mode and pretty-prints the answer + reasoning + citations.

## Writes (ONLY these)
- `src/interface/core.py`
- `src/interface/cli/__init__.py`
- `src/interface/cli/main.py`
- `src/interface/cli/__main__.py`
- `tests/unit/test_cli.py`

## Forbid
`src/interface/ui/**` (wave-7 tasks 02-05 own those). `src/finroot/**` (read/import only).

## Contract
Read `.specify/specs/wave-7/contracts/ui.contract.md` (entry point + orchestrator API).

## Steps
1. `src/interface/core.py` — `answer(query, *, user_id="demo", mock=True) -> AgentState`:
   - Build `MockProvider` (mock=True) or real via `get_provider` (mock=False).
   - Build `MemoryManager` for `user_id`; load a demo twin from `data/samples/twin_profiles.json` if present.
   - Build `AuditTrail` (temp/local path).
   - Instantiate `FinRootOrchestrator(memory=..., audit=..., llm=...)` and `return orch.run(query)`.
   - If W5 reasoning modules import cleanly, run critic on the result and attach to `state.critique`; degrade gracefully (try/except ImportError, log a warning — FM-11 no silent pass).
   - Also expose `build_trace(state) -> list[dict]` returning the trace-event shape from the contract (derive from audit_events + plan + tool_outputs).
2. `src/interface/cli/main.py` — Typer `app`:
   - Command `ask`: `finroot ask "<query>" [--mock/--no-mock] [--user demo]` → calls `answer()`, prints with `rich`:
     - Answer summary, confidence label (colored), risk band
     - Reasoning steps (numbered, from `build_trace`)
     - Citations list
     - Critic verdict if present
   - Default invocation `python -m interface.cli "<query>"` should work (use a callback or default command).
3. `__main__.py` — `from interface.cli.main import app; app()`.
4. `tests/unit/test_cli.py` (min 8): `answer()` returns AgentState in mock; build_trace shape; Typer CliRunner invokes `ask` and exits 0; mock default; handles empty query gracefully.

## Acceptance
```bash
PYTHONPATH=src python3 -m interface.cli --mock "Review my portfolio and flag risks"
PYTHONPATH=src python3 -m pytest tests/unit/test_cli.py -v
ruff check src/interface/core.py src/interface/cli/
```
CLI must print a real answer with reasoning + citations, fully offline.

## Report
`work/reports/wave-7/01-cli.report.md`
