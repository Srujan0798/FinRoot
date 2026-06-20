# Task wave-8/02 — README polish + SUBMISSION mapping

> Read `work/WORKER_PROMPT.md` then build. Depends on all waves. The judge's first impression.

## Objective
A README that wins on first read: clear value prop, architecture, the judging-criteria mapping, a
one-command quickstart, and the FRB results table (numbers from results/metrics.json).

## Writes (ONLY these)
- `README.md`
- `docs/SUBMISSION.md`

## Forbid
All other files. (Replace the existing README if present; preserve nothing stale.)

## Contract
Read `.specify/specs/wave-8/contracts/submission.contract.md` § README. Read `CLAUDE.md` for scoring weights + positioning. Read `results/metrics.json` if present for numbers.

## Steps
1. `README.md`:
   - Hero: "FinRoot — Sovereign, Reasoning-First AI Financial Agent" + one-line value prop + badges (Python 3.11, tests passing, license).
   - The problem (individual investors lack institutional-grade, explainable, auditable reasoning).
   - What FinRoot does — bullet the differentiators: 6-agent LangGraph orchestration, 12 tools, 4-tier memory + Digital Twin, 5-axis Self-Critic, Rooted Prudence verifier, hash-chained audit, sovereign/offline.
   - Architecture: embed `docs/architecture/architecture.mmd` (mermaid fenced block so GitHub renders it).
   - **Judging-criteria mapping table**: Reasoning 35% / Architecture 30% / Code 20% / Idea 15% → exactly where each is delivered (module paths + the FRB proof).
   - Quickstart: `docker compose up` AND `pip install -e . && python -m interface.cli --mock "..."` AND `streamlit run src/interface/ui/app.py`.
   - **FRB Results** table: pull pass@k + composite lift from `results/metrics.json` if present; else add a clear "regenerate with `make evals`" note (do NOT hand-fabricate numbers — FM-12).
   - Sovereignty + audit-trail story (short).
   - Repo map (top-level dirs).
2. `docs/SUBMISSION.md`:
   - Checklist mapping PS-1 asks (LLM reasoning, external tools/APIs, memory, agent workflows, real-time, accurate/contextual/actionable) → where FinRoot satisfies each.
   - Links to: demo script, deck, exec summary, ADRs, metrics.json, architecture diagram.
   - Demo instructions (how to reproduce screenshots/video offline).

## Acceptance
```bash
test -f README.md && test -f docs/SUBMISSION.md && echo "files present"
grep -qi "35%" README.md && grep -qi "quickstart\|quick start" README.md && echo "criteria + quickstart present"
grep -q "mermaid" README.md && echo "architecture embedded"
```
If metrics.json absent, README must say so (no fabricated numbers — FM-12).

## Report
`work/reports/wave-8/02-readme-submission.report.md`
