# Deploy, Docs & Submission — Interface Contract (Wave-8)

> Frozen before dispatch. Converts the build into the win. Derived numbers come from
> `results/metrics.json` (FM-12) — never hand-typed.

## Docker (task 01)
- `Dockerfile` — python:3.11-slim base; `pip install -e .[ui]`; non-root user; healthcheck hitting Streamlit `:8501`.
- `docker-compose.yml` — service `finroot` exposing 8501; Mock mode default (no keys needed); optional `.env` mount.
- `.dockerignore` — exclude `.git`, `__pycache__`, `*.db`, `data/chroma`, caches, secrets.
- Acceptance: `docker compose up -d && curl -fsS localhost:8501 >/dev/null` succeeds.

## README (task 02) — `README.md`
Sections: hero one-liner · the problem · what FinRoot does (with the reasoning-trace screenshot
placeholder) · architecture diagram · **judging-criteria mapping table** (Reasoning 35% / Architecture
30% / Code 20% / Idea 15% → where each is satisfied) · quickstart (Mock, one command) · the FRB
results table (numbers pulled from `results/metrics.json`) · sovereignty story · audit-trail story.
Also `docs/SUBMISSION.md` — checklist mapping deliverables to PS-1 asks.

## ADRs (task 03) — `docs/decisions/000N-*.md`
5–8 architecture decision records (MADR format): why LangGraph Plan-and-Execute, why the 4-tier
memory, why the 5-axis critic, why sovereign-first/Mock default, why hash-chained audit, why the
Digital Twin, why deterministic tax engine. Each: Context · Decision · Consequences.

## Demo script (task 04) — `docs/business/7_minute_demo_script.md`
Timed narration (0:00–7:00) walking judges through: the problem → ask a portfolio question → show
the live reasoning trace → show the critic catching a bad answer → show the Digital Twin → show the
harness delta vs RAG → the audit trail. Each beat has: timestamp, what to click, what to say.

## Deck + exec summary (task 05)
- `docs/business/presentation_outline.md` — 6 slides (Problem · Solution/Idea · Architecture · Reasoning Quality+FRB results · Demo · Why we win/sovereignty).
- `docs/business/executive_summary.md` — 1 page: what, why it matters, the measured edge, the moat.

## Architecture diagram + submission (task 06)
- `docs/architecture/architecture.mmd` — mermaid: user → CLI/UI → orchestrator → 6 agents → 12 tools → memory(4-tier) → critic/principles → audit. Render note for png.
- `scripts/make_submission.sh` — produces `finroot-submission.zip` excluding secrets/caches/.git/venv/db; includes src, tests, docs, README, results/metrics.json, evals/reports.

## DEMO ASSETS (orchestrator-run after waves land)
- `scripts/capture_demo.py` — runs `answer()` on 3-4 showcase queries in Mock, writes the formatted
  outputs (answer + reasoning trace + critic verdict + citations) to `docs/demo/transcript_*.md` for
  screenshots/video narration. (Owned by task 04 demo author OR orchestrator.)

## File map (disjoint write-sets)
| Task | Writes |
|------|--------|
| 01 | `Dockerfile`, `docker-compose.yml`, `.dockerignore` |
| 02 | `README.md`, `docs/SUBMISSION.md` |
| 03 | `docs/decisions/0003-langgraph-orchestration.md` … `0008-*.md` (6 ADRs) |
| 04 | `docs/business/7_minute_demo_script.md`, `scripts/capture_demo.py` |
| 05 | `docs/business/presentation_outline.md`, `docs/business/executive_summary.md` |
| 06 | `docs/architecture/architecture.mmd`, `scripts/make_submission.sh` |
