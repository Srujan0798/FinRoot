# Task wave-1/06 — Project Bootstrap, Smoke Test & CI

> Self-contained worker brief. **Dispatch LAST** — it integrates tasks 01–05 and proves CI green.
> Read `work/WORKER_PROMPT.md`, then build.

## Objective
Wire the package together (exports, importability), write an end-to-end smoke test that exercises the
foundation (Mock provider answers, audit chain verifies, state round-trips), and confirm CI runs the
acceptance suite green.

## Why it matters
Code Implementation (20%): a clean, installable package with green CI is table stakes for "engineering
practices". The smoke test is the fast feedback loop the whole build relies on.

## Writes (ONLY these)
- `src/finroot/__init__.py`
- `scripts/smoke_test.py`
- `pyproject.toml`  *(finalize/confirm — see note)*
- `.github/workflows/ci.yml`  *(finalize/confirm — see note)*

## Forbid
The implementation files owned by tasks 01–05 (`llm/`, `schemas/`, `audit/`, `tools/base.py`,
`agents/base.py`, `config/`). You import them; you don't edit them.

## Note on shared infra files
`pyproject.toml` and `.github/workflows/ci.yml` are seeded by the OS-Setup. Your job is to confirm
they install the package and run wave-1 acceptance; adjust ONLY if needed and note it in your report
(these are the one task that owns these files — no collision).

## Steps
1. `src/finroot/__init__.py`: export the public surface (`get_provider`, `AgentState`, `AuditTrail`,
   `BaseTool`, `BaseAgent`, `get_settings`).
2. `scripts/smoke_test.py`: instantiate Mock provider → complete a prompt; create an `AuditTrail` →
   append 2 events → `verify_chain()` True; build `AgentState`, round-trip it. Print `FOUNDATION OK`
   and exit 0; any failure → loud non-zero exit.
3. Confirm `pyproject.toml` makes `finroot` importable (src layout) and configures ruff + pytest.
4. Confirm `.github/workflows/ci.yml` runs: install → `ruff check src/` → `pytest tests/unit` →
   `python scripts/smoke_test.py`.

## Acceptance (paste real output)
```bash
pip install -e .
python scripts/smoke_test.py            # prints FOUNDATION OK, exit 0
ruff check src/ && pytest tests/unit -v
```

## Domain rules
Smoke test fails loud on any broken piece (no "OK" unless every step passed, FM-09).

## Report
`work/reports/wave-1/06-project-bootstrap-ci.report.md`.
