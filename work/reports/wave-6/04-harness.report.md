# Report wave-6/04 — Harness Runner

## Result
DONE

## What I built
- `src/finroot/evaluation/harness.py` — `HarnessConfig`, `TrialResult`, `HarnessResult`, `MetricsReport`, `run_harness()`, `write_metrics()`, `compute_composite_lift()`, `build_transcript()` plus the internal `_run_finroot`/`_run_baseline`/`_grade_trial` dispatchers. Imports from `interface.core` (preferred) and falls back to constructing `FinRootOrchestrator` directly.
- `scripts/run_evals.py` — argparse CLI with `--mock`, `--task`, `--k`, `--system`, `--out`, `--llm-judge`, `--base-seed`, `--verbose`. Single-task mode prints the full transcript and still writes a `metrics.json` subset. Full-bank mode prints the summary table + per-domain breakdown.
- `tests/unit/test_harness.py` — 39 tests across 9 classes covering: loaders, run_harness core behaviour, pass@k/pass^k invariants, the headline FinRoot-beats-RAG promise, metrics.json shape and write, single-task mode, aggregation, TrialResult contract, defensive behaviour. Disjoint from W6-01/02/03/05 Writes sets.

## Acceptance evidence (real output, this session)

### `PYTHONPATH=src python3 scripts/run_evals.py --mock --task frb-001`
```
==============================================================================
Task: frb-001  domain=portfolio  difficulty=easy  twin_id=None
Query: My portfolio is 80% in one large-cap stock and 20% in a liquid fund. Should I rebalance before FY-end?
------------------------------------------------------------------------------
Expected must_mention: ['concentration', 'risk', 'tax', 'LTCG', 'diversif']
Expected must_not:     ['guaranteed', 'you will definitely', 'no risk']
Min citations:         2
Expected confidence:   high
==============================================================================

  trial 0  system=finroot  passed=False  score=0.6600  elapsed=1.18s
    must_mention: 0.20 (missing: ['concentration', 'tax', 'LTCG', 'diversif'])
    citations:    9 (min_required: 2)
    numeric:      expected=None extracted=None diff=None
    confidence:   expected=high actual=medium

  trial 1  system=finroot  passed=False  score=0.6600  elapsed=1.11s
    must_mention: 0.20 (missing: ['concentration', 'tax', 'LTCG', 'diversif'])
    citations:    9 (min_required: 2)
    ...

  trial 0  system=rag  passed=False  score=0.0000  elapsed=0.00s
    error: ValidationError: ... numeric content but citations is empty

  trial 0  system=single_agent  passed=False  score=0.1100  elapsed=0.00s
    must_mention: 0.20 (missing: ['concentration', 'tax', 'LTCG'])
    citations:    1 (min_required: 2)

Wrote metrics (single-task subset) to results/metrics.json
  as_of_sha=7afd827  n_tasks=1  k=3
```
Exit status: 0.

### `PYTHONPATH=src python3 scripts/run_evals.py --mock`
```
FRB harness: k=3 systems=['finroot', 'rag', 'single_agent'] mock=True judge_with_llm=False
FRB bank: data/gold/frb_questions.json

system          n_tasks   pass@1    pass@k    pass^k    mean_score
--------------  --------  --------  --------  --------  -----------
finroot         52         0.3462    0.3462    0.3462    0.6722
rag             52         0.0000    0.0000    0.0000    0.0150
single_agent    52         0.0000    0.0385    0.0000    0.3195

Per-domain mean_score:
system          behavioral  cashflow  credit   estate_planning  general  insurance  international  news_impact  portfolio  risk     tax
finroot             0.7025    0.6200   0.6533      0.6000       0.7371    0.6375       0.7000       0.5520      0.7012   0.6625   0.7100
rag                 0.0042    0.0056   0.0056      0.0000       0.0224    0.0125       0.0167       0.0067      0.0196   0.0111   0.0310
single_agent        0.4800    0.3856   0.4833      0.4867       0.4379    0.4850       0.3833       0.2460      0.1292   0.2111   0.2040

Composite lift vs RAG: +4381.33%
Total time: 85.2s

Wrote results/metrics.json  as_of_sha=7afd827  generated_at=2026-06-20T11:01:31.119976+00:00
```
Exit status: 0.

### `PYTHONPATH=src python3 -m pytest tests/unit/test_harness.py -v`
```
============================= test session starts ==============================
collected 39 items

tests/unit/test_harness.py .......................................       [100%]

=============================== warnings summary ===============================
(350 warnings: langchain/pydantic v1/chromadb deprecations on Python 3.14)
-- Docs: https://docs.pydantic-docs/en/stable/concepts/models.html
================= 39 passed, 350 warnings in 71.16s (0:01:11) ==================
```
Exit status: 0.

### `cat results/metrics.json | python3 -m json.tool | head -30`
```
{
    "as_of_sha": "7afd827",
    "generated_at": "2026-06-20T11:01:31.119976+00:00",
    "systems": {
        "finroot": {
            "system": "finroot",
            "pass_at_1": 0.3462,
            "pass_at_k": 0.3462,
            "pass_hat_k": 0.3462,
            "mean_score": 0.6722,
            "per_domain": {
                "behavioral": 0.7025,
                "cashflow": 0.62,
                "credit": 0.6533,
                "estate_planning": 0.6,
                "general": 0.7371,
                "insurance": 0.6375,
                "international": 0.7,
                "news_impact": 0.552,
                "portfolio": 0.7012,
                "risk": 0.6625,
                "tax": 0.71
            },
            "n_tasks": 52
        },
        "rag": {
            ...
```

### `ruff check src/finroot/evaluation/harness.py scripts/run_evals.py tests/unit/test_harness.py`
```
All checks passed!
```

## Tests
- 39 tests in 9 classes (`TestLoaders`, `TestRunHarness`, `TestInvariants`, `TestFinRootBeatsRAG`, `TestWriteMetrics`, `TestSingleTaskMode`, `TestAggregation`, `TestTrialResultContract`, `TestDefensive`).
- 0 failures, 0 errors.
- Coverage: FRB loader happy/missing/malformed/wrong-shape, twin loader empty/malformed, seed suffix deterministic/varied, run_harness returns one row per system, n_tasks matches filter, task/system filter errors, `pass@k ≤ 1.0`, `pass^k ≤ pass@k`, `pass@1 ≤ pass@k`, per-domain in unit interval, FinRoot ≥ RAG (headline), composite lift sign, lift=0 when RAG missing, metrics.json required keys + git_sha string + system-row shape, CLI `--task` and full-bank subprocess invocations, aggregation math invariants (manually-constructed trials), TrialResult `extra="forbid"`, defensive `_grade_trial` on `final=None`, unknown system/baseline errors, `_ensure_repo_root_on_path` idempotent.
- Full test run: 39 passed in 71.16s.

## Decisions / deviations
- **`state.candidate` → `state.final` promotion** (`_ensure_final_populated` in harness). The current `FinRootOrchestrator.run()` populates `candidate` but leaves `final` None; the graders inspect `final`. Rather than touching the orchestrator (owned by a different wave's task), the harness promotes internally. Logged in gotchas.
- **Mock seed variation via prompt suffix** (`_seed_suffix(trial, base_seed)`). MockProvider is hash-deterministic on the prompt, so the only way to vary per-trial output is to perturb the prompt. Same `(task, trial, base_seed)` → same perturbation → reproducibility invariant preserved.
- **Defensive `try/except` in `_run_system`**: any exception in a trial (including the baselines.py ValidationError from the expanded mock) scores `0.0, passed=False, error=str` instead of crashing the run. FM-11: never fabricate scores, never silently substitute.
- **`_ensure_repo_root_on_path()`** is called at every entry point that imports `evals.graders` (harness internals + CLI subprocess). Per the W6-02 gotcha dated 2026-06-20, `evals/` is a PEP-420 package at the repo root and is NOT on `sys.path` with `PYTHONPATH=src` alone.
- **CLI subprocess tests** (`test_cli_single_task_runs`, `test_cli_full_runs`) invoke `scripts/run_evals.py` via subprocess to verify the acceptance commands end-to-end.
- **CLI `--task` mode still writes a metrics.json subset** (n_tasks=1) so downstream consumers (W6-05 report generator) never face a missing file.
- **Single task can have many trials with the same seed response** when MockProvider is hash-stable. We accept this — the contract's "vary mock seed" is satisfied by perturbing the prompt, but the orchestrator's tool outputs dominate FinRoot's answer anyway, so trial-to-trial FinRoot scores are tightly clustered (≈0.66 for frb-001). Pass^k still serves its purpose for the consistency story.

## Surprises / gotchas
- Yes — appended to `docs/waves/wave-6-gotchas.md`:
  1. `state.candidate` vs `state.final` mismatch (orchestrator populates only candidate).
  2. Pre-existing baselines.py + expanded mock.py conflict (NOT in this task's Writes set; flagging for whoever owns baselines).
  3. Trial-variation strategy rationale (prompt-suffix seed).

## Follow-ups (for orchestrator triage — do NOT build now)
- **mock.py / baselines.py reconciliation.** When `mock.py` was expanded to 55+ canned responses (by some other wave), the W6-03 `NaiveRAGBaseline.answer()` started throwing Pydantic `ValidationError` for prompts whose hash lands on a numeric canned response. This drops RAG's mean_score to ~0.015 in the harness output. The harness handles the error defensively (score=0.0) so numbers are not fabricated, but the comparison is unfair. Suggest: W6-03 owner (or whoever expanded mock) either (a) updates baselines to seed at least one citation when the canned text contains digits, or (b) curates mock responses to avoid numeric content for the naive prompt space.
- **Trial-level variation.** With MockProvider, FinRoot scores are very stable across trials (the canned tool outputs dominate). For a more interesting pass^k story, future waves could perturb the orchestrator's LLM temperature via env var or add controlled noise to tool outputs.
- **Report generator (W6-05).** The metrics.json shape this task writes is exactly the contract spec; W6-05 can read it directly.

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)