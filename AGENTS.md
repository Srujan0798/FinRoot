# FinRoot — Orchestrator Kernel

> Auto-loaded every session. Keep this ≤ ~3K tokens. Deep detail is **lazy-loaded** from
> `orchestrator/core/*`, `plan/*`, `.specify/*`, and `docs/*` — read those on demand, not up front.

## What FinRoot is
A **Sovereign, Reasoning-First AI Financial Agent** (LangChain + LangGraph). Not a chatbot
wrapper — a multi-agent reasoning pipeline that *shows its work*, flags risk, cites evidence,
self-critiques, and keeps a tamper-evident audit trail. Built to win SCALE ML Club PS-1
("Build an AI Agent for Finance"). One-line goal:

> **Give an individual investor / small family office institutional-grade, explainable,
> auditable financial reasoning — locally and on their own terms.**

Scoring we optimize for (memorize): **Reasoning Quality 35% · Agent Architecture 30% ·
Code Implementation 20% · Solution Idea 15%.** Every decision serves these weights.

## The two-tier methodology (NEVER violate)
- **TIER 1 — Orchestrator (this Claude/Kimi session).** Plans, writes task files into `work/`,
  reviews reports, runs acceptance, merges, updates state. **Never writes implementation code.**
- **TIER 2 — Workers (OpenCode CLI windows / your agents).** Receive ONE self-contained task
  file from `work/<wave>/<task>.md`, implement into `src/`, write a report to
  `work/reports/<wave>/<task>.report.md`. Stateless, parallel.
- Handoff is the file boundary: `work/<wave>/<task>.md` → `work/reports/<wave>/<task>.report.md`.
- Orchestrator never executes; workers never plan.

## Read order on a cold start (wake)
1. `HANDOFF.md` — current state, active wave, what's in flight.
2. This kernel.
3. `plan/EXECUTION.md` — wave status table (one row per wave, commit hashes).
4. Active wave spec: `.specify/specs/wave-N/spec.md`.
5. Recent `orchestrator/memory/session/<wave>-<task>.events.jsonl`.
Then act. Run `bash orchestrator/scripts/replay_session.sh <wave> <task>` to reconstruct context.

## The wave loop
```
/plan wave-N  → .specify/specs/wave-N/{spec,plan,tasks,contracts}
/dispatch     → work/wave-N/0X-*.md (DISJOINT write-sets, parallel-safe)
workers run   → work/reports/wave-N/0X.report.md
/review       → APPROVE→/merge | REVISE→rewrite brief | REJECT→attic/
/ship         → acceptance + tests + EXECUTION.md(commit) + CHANGELOG
```
Waves: see `plan/EXECUTION.md`. Tasks per wave have **disjoint `writes` and explicit `forbid`**
(FM-13). Extras nobody asked for → `BACKLOG.md`, never silently built (FM-08).

## Tech stack (the smallest winning stack)
Python 3.11 · LangChain + LangGraph · Pydantic v2 · ChromaDB (vector) + SQLite (structured +
audit) + JSON fallback · Streamlit (dark UI) + Typer CLI · LLM providers: **Ollama (local,
sovereign default)** / OpenAI / Groq / Mock (offline judging) · Docker · pytest · ruff.
Sovereign-first: local model preference, offline fallback, no blind reliance on closed APIs.

## The non-negotiables (failure-mode guardrails — full table: §13 of OS_SETUP.md)
- **FM-09 Evidence required.** Never claim "done/passing" without the command + its output this
  session. Never round "partly" up to "done". Own bugs.
- **FM-11 No silent failures.** No bare `except: pass`. Fallbacks log loud. Missing required
  input fails loud — NEVER substitute synthetic/hallucinated financial data.
- **FM-08 Scope guard.** `docs/SCOPE_GUARD.md` is law. IN / OUT / LATER.
- **FM-13 No parallel collisions.** Disjoint write-sets per wave; check before dispatch.
- **FM-01 No state drift.** `EXECUTION.md`/`HANDOFF.md` are rewritten to current truth, one row
  per item; active wave matches across files.
- **FM-05/12 One source for metrics.** Numbers live in `results/metrics.json` + eval reports;
  docs regenerate, never hand-type. Stamp "as of <sha>".
- **FM-07 Publish gate.** No secrets / cheat-sheets / raw prompts committed. Brainstorm inputs
  live in `resources/brainstorm/` (design inputs, not shipped code).
- **Domain rule.** Financial advice must be explainable, risk-aware, cited, and confidence-
  labeled. When evidence is insufficient, the agent says so and may recommend "do not act yet".

## Blast radius (governance — full: orchestrator/core/blast-radius.md)
r0 read · r1 local repo (auto) · r2 local services (confirm) · r3 remote/push (confirm) ·
r4 external humans (always confirm) · r5 money/data-loss (block). Auto-mode skips r0/r1 only.

## Where things live
`orchestrator/` Tier-1 apparatus · `work/` the bridge · `src/finroot/` agent code (workers) ·
`src/interface/` UI+CLI · `evals/` reasoning-quality proof (the 35% weapon) · `plan/` strategy ·
`.specify/` specs · `docs/` everything explanatory · `attic/` superseded (never delete).
Full map: `HIERARCHY.md`.

## Commands (orchestrator/skills + orchestrator/commands)
`/plan` `/dispatch` `/review` `/merge` `/ship` `/status` `/next` `/handoff` `/audit` `/reflect`.

> When in doubt: read `HANDOFF.md` and `plan/EXECUTION.md` first. Plan, dispatch, review, merge.
> Discipline over speed. Evidence over assertion.
