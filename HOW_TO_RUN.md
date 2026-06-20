# HOW TO RUN — The Dual-Tier Workflow (plain language)

This file explains how **you (Srujan) drive the build** using one orchestrator and many worker
agents. It is the human-readable version of the loop in `CLAUDE.md` and `OS_SETUP.md`.

## The mental model
- **One orchestrator** (Claude Code or Kimi — pick either, they're interchangeable). It is the
  brain: it plans, writes task files, reviews, merges. It never writes feature code.
- **Many workers** (your agent swarm — OpenCode CLI windows or external agents). Each gets ONE
  self-contained task file and implements it. They run in parallel.
- **The bridge** is the `work/` folder. Orchestrator writes `work/<wave>/<task>.md`; the worker
  writes back `work/reports/<wave>/<task>.report.md`.

## Day-to-day loop
```
1. /status                 → orchestrator reads HANDOFF.md + EXECUTION.md, tells you where we are
2. /plan wave-N            → (already done for wave-1) generates .specify/specs/wave-N/*
3. /dispatch wave-N        → writes work/wave-N/0X-*.md task files (disjoint write-sets)
4. YOU open worker windows → paste each task file into a separate agent. They run in parallel.
5. workers finish          → each writes work/reports/wave-N/0X.report.md
6. /review                 → orchestrator runs acceptance commands, then APPROVE / REVISE / REJECT
7. /merge                  → approved work is integrated
8. /ship                   → final tests, tag, EXECUTION.md gets the commit hash, CHANGELOG bump
9. repeat for next wave
```

## Running the build right now (wave-1 is ready)
1. Open the orchestrator in this folder: `claude` (or your Kimi setup). It auto-loads `CLAUDE.md`.
2. Tell it: *"Read HANDOFF.md. Dispatch wave-1."* (Task files already exist in `work/wave-1/`.)
3. Open **6 worker windows**. Into each, paste one of:
   - `work/wave-1/01-llm-provider-layer.md`
   - `work/wave-1/02-pydantic-schemas-state.md`
   - `work/wave-1/03-audit-trail-backbone.md`
   - `work/wave-1/04-config-settings.md`
   - `work/wave-1/05-base-tool-agent-interfaces.md`
   - `work/wave-1/06-project-bootstrap-ci.md`
   Plus the shared worker preamble: `work/WORKER_PROMPT.md`.
4. Workers implement into `src/finroot/**`, write reports.
5. Back in the orchestrator: *"Review wave-1 reports, run acceptance, merge, ship."*

## Running the app (once waves ship)
```bash
make install        # pip install -r requirements.txt
make smoke          # python scripts/smoke_test.py
make ui             # streamlit run src/interface/ui/app.py
make cli ARGS="--mock 'analyze my portfolio'"
make evals          # the reasoning-quality benchmark → results/metrics.json
make test           # pytest
docker compose up   # full stack
```

## If the orchestrator session dies (wake / resume)
1. Reopen Claude/Kimi in this folder.
2. It auto-loads `CLAUDE.md`, then reads `HANDOFF.md`.
3. Run `bash orchestrator/scripts/replay_session.sh <wave> <task>` to see the last events.
4. Resume from exactly there. Nothing is lost — `work/` + `events.jsonl` are durable.

## LLM provider modes
| Mode | Set | When |
|---|---|---|
| **Mock** | `--mock` flag | Demos / CI / judging — instant, offline, deterministic |
| **Ollama (sovereign)** | `FINROOT_LLM_PROVIDER=ollama` | Default real mode, fully local |
| **Groq / OpenAI** | `FINROOT_LLM_PROVIDER=groq` + key | Fast cloud inference when allowed |

See `.env.example` for keys (all optional — Mock + Ollama need none).
