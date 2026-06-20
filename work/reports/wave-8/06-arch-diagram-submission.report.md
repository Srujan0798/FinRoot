# Report wave-8/06 — Architecture Diagram + Submission Packager

## Result
DONE

## What I built
- `docs/architecture/architecture.mmd` — updated mermaid flowchart TD with User → CLI/UI → answer() → FinRootOrchestrator → 6 agents → 12 tools (6 groups) → 4-tier memory → Self-Critic + Principles → hash-chained audit → LLM layer (Mock/Ollama/Groq/OpenAI). Includes legend comment block and mmdc render note.
- `scripts/make_submission.sh` — `finroot-submission.zip` builder with set -euo pipefail. Includes all required paths, excludes forbidden patterns (.git, __pycache__, .pyc, .venv, *.db, data/chroma, secrets, keys, work/, caches). Prints zip name + size + file count.

## Acceptance evidence (real output, this session)
```
$ bash scripts/make_submission.sh
Packaging submission...
  adding: src/ (stored 0%)
  ... (full file list in build output above)
  adding: LICENSE (deflated 40%)

  ZIP: finroot-submission.zip
  Size: 300688 bytes
  Files: 236

$ unzip -l finroot-submission.zip | grep -E "\.env|secret|\.key|\.git/" && echo "LEAK!" && exit 1 || echo "no secrets in zip"
no secrets in zip

$ test -f docs/architecture/architecture.mmd && echo "diagram present"
diagram present
```

## Tests
N/A (no code tests — asset files and shell script). Shell syntax validated by execution.

## Decisions / deviations
- Updated the existing `architecture.mmd` rather than replacing from scratch, preserving the detailed sub-orchestrator flow (Intent Classify → Context Assemble → Plan → Execute → Synthesize → Self-Critic → Prudence → Finalize → Audit Emit) which the spec didn't mandate but the existing diagram already had.
- Used `flowchart TD` (spec-preferred) instead of existing `graph TB`.
- Added "Intent Agent" to the 6 agents (was missing from earlier version).
- Renamed tool groups to match spec: market/fundamentals, news/sentiment, risk/portfolio_sim, tax, macro/currency, profile/documents/watchlist.
- For "kernel docs", included root-level .md files: AGENTS.md, HANDOFF.md, HIERARCHY.md, OS_SETUP.md, BACKLOG.md, CONTRIBUTING.md, HOW_TO_RUN.md, LICENSE.
- Results/metrics.json not present in repo; skipped conditionally (no error).
- data/gold/ was empty; still included per spec.
- No tests were required for this task (shell script + mermaid asset).

## Surprises / gotchas
- No surprises encountered. Contract file existed at `.specify/specs/wave-8/contracts/submission.contract.md`.

## Follow-ups (for orchestrator triage — do NOT build now)
- None.

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above) — N/A (no Python code)
- [x] No secrets committed (FM-07)
