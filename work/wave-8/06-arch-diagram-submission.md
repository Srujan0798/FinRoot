# Task wave-8/06 — Architecture Diagram + Submission Packager

> Read `work/WORKER_PROMPT.md` then build. Depends on the built system.

## Objective
A clean mermaid architecture diagram of the whole FinRoot system and a submission-zip script that
packages a clean, secret-free deliverable.

## Writes (ONLY these)
- `docs/architecture/architecture.mmd`
- `scripts/make_submission.sh`

## Forbid
All other files.

## Contract
Read `.specify/specs/wave-8/contracts/submission.contract.md` § Architecture diagram + submission.

## Steps
1. `docs/architecture/architecture.mmd` — mermaid `flowchart TD` (or `graph TD`):
   - User → CLI / Streamlit UI
   - → `answer()` entry → FinRootOrchestrator (LangGraph: plan → execute → synthesize)
   - Orchestrator → 6 agents (intent, market, news, portfolio, risk, tax)
   - Agents → 12 tools (group them: market/fundamentals, news/sentiment, risk/portfolio_sim, tax, macro/currency, profile/documents/watchlist)
   - Cross-cutting: 4-tier Memory (working/semantic/digital-twin/audit), Self-Critic + Principles verifier, hash-chained Audit Trail
   - LLM layer: Mock / Ollama / Groq / OpenAI
   - Include a short legend comment block. Must be valid mermaid (renders on mermaid.live).
   - Add a sibling note in the file (as mermaid comment) on how to render to PNG: `mmdc -i architecture.mmd -o architecture.png`.
2. `scripts/make_submission.sh`:
   - Produces `finroot-submission.zip` at repo root.
   - INCLUDE: `src/`, `tests/`, `docs/`, `evals/`, `config/`, `scripts/`, `data/samples/`, `data/gold/`, `data/tax_rules.json`, `README.md`, `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `results/metrics.json` (if present), `.github/`, `CHANGELOG.md`, kernel docs.
   - EXCLUDE (hard): `.git`, `__pycache__`, `*.pyc`, `.venv`/`venv`, `*.db`, `data/chroma`, `data/watchlists`, `logs/`, `.env`, any `*secret*`, `*.key`, `work/` internal task logs, `.pytest_cache`, `.ruff_cache`.
   - Print the zip name + size + file count on success. Fail loud (set -euo pipefail) if a required file is missing.

## Acceptance
```bash
bash scripts/make_submission.sh
unzip -l finroot-submission.zip | grep -E "\.env|secret|\.key|\.git/" && echo "LEAK!" && exit 1 || echo "no secrets in zip"
test -f docs/architecture/architecture.mmd && echo "diagram present"
```

## Report
`work/reports/wave-8/06-arch-diagram-submission.report.md`
