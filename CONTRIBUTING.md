# Contributing to FinRoot

FinRoot is built by a **dual-tier agentic process**. Whether you're a human or an agent, the
rules below keep the build collision-free and the quality high.

## Who does what
- **Orchestrator (Tier 1, Claude/Kimi):** plans waves, writes task files, reviews, merges, ships.
  Never writes feature code. Owns `orchestrator/`, `plan/`, `.specify/`, `docs/`, status files.
- **Workers (Tier 2, agent swarm):** implement exactly one task file into `src/`+`tests/`. Never
  plan beyond their brief. Own only the files listed in their task's `writes` set.

## Golden rules (failure-mode guardrails — full table in OS_SETUP.md §13)
1. **Evidence over assertion (FM-09).** Never say "done/passing" without the command + output.
2. **Fail loud (FM-11).** No `except: pass`. Never fabricate financial data — missing input is an error.
3. **Stay in scope (FM-08).** Build only what the task file asks. Extras → `BACKLOG.md`.
4. **Disjoint writes (FM-13).** Touch only your task's `writes` files. Never edit another task's files.
5. **One source of truth for metrics (FM-05/12).** Numbers come from `results/metrics.json` + eval
   reports. Don't hand-type numbers into docs.
6. **Never delete (§6.5).** Superseded work → `attic/`, `docs/historical/`, `prompts/archive/`.
7. **Publish gate (FM-07).** No secrets, raw prompts, or scratch files committed.

## Quick Setup
1. `make install` — install dependencies
2. `make setup-hooks` — install git hooks
3. `make test-fast` — run tests
4. `make doctor` — verify everything works

## Code conventions
- Python 3.11, type-hinted, **Pydantic v2** for all data at boundaries.
- `ruff` for lint+format (`make lint`). Tests with `pytest` (`make test`).
- Path-scoped rules: `orchestrator/rules/python.md`, `security.md`, `orchestrator/rules/docs.md`.
- Domain rule: financial outputs MUST carry rationale, risk notes, citations, and a confidence label.

## Workflow for a worker
1. Read your task file in `work/<wave>/<task>.md` and `work/WORKER_PROMPT.md`.
2. Read the contracts in `.specify/specs/<wave>/contracts/` your task references.
3. Implement into the `writes` files only. Write tests. Run them.
4. Fill `work/reports/<wave>/<task>.report.md` using `work/REPORT_TEMPLATE.md` (with command output).
5. If you hit a surprise, add it to `docs/waves/<wave>-gotchas.md` immediately.

## Quality gates (run before you commit)
- `make lint` — ruff clean
- `make test-fast` — fast pytest path (skips `@pytest.mark.slow`)
- `make validate` — structural + execution + doc drift checks
- `make coverage` — coverage ≥ threshold (default 80%)
- `make session-start` — print current context (HEAD, metric, dirty tree, zip status)

## Commits
- Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`) — used by
  `scripts/changelog_suggest.sh` to draft a CHANGELOG entry.
- One logical change per commit. Reference the wave/task: `feat(wave-1): LLM provider layer (task 01)`.
- Use `git push --no-verify` to bypass pre-push hooks only in an emergency. The default hook
  runs `validate_execution.sh` + `validate_docs.sh`.

## Reviews
The orchestrator runs acceptance commands from your task's `acceptance` block before approving.
APPROVE → merge · REVISE → it rewrites your brief with specifics · REJECT → work moves to `attic/`.

## Local development tips
- Run `make session-start` at the start of any session to see current state.
- The suite is hermetic (no `data/` leakage) and runs in 5-7 minutes without slow tests.
  The slow tests (`test_cli_*_runs` subprocess tests) take 5-10 min; skip with `-m 'not slow'`.
- `make evals` regenerates `results/metrics.json`. After that, update any doc that cites
  the old metric (or run `make validate` to catch it).
- `make metrics-drift` compares HEAD's `results/metrics.json` with the on-disk version and
  flags regressions. Useful before deciding to commit.
- The submission zip (`finroot-submission.zip`) must be rebuilt after every metric change
  via `bash scripts/make_submission.sh`. The `test_zip_consistency.py` tests catch zip drift.
