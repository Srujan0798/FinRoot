# Task wave-6/04 — Harness Runner (pass@k / pass^k, multi-system)

> Read `work/WORKER_PROMPT.md` then build. Depends on W6-01 (bank), 02 (graders), 03 (baselines).

## Objective
The runner that executes the FRB across FinRoot + baselines, computes pass@1 / pass@k / pass^k and
per-domain scores, and writes the single metrics source `results/metrics.json`.

## Writes (ONLY these)
- `src/finroot/evaluation/harness.py`
- `scripts/run_evals.py`
- `tests/unit/test_harness.py`

## Forbid
`baselines.py`, `report.py`, `evals/graders/**`, `data/gold/**` (other tasks — import only).

## Contract
Read `.specify/specs/wave-6/contracts/evals.contract.md` § Harness + metrics.json shape. Match exactly.

## Steps
1. `harness.py`:
   - `run_harness(config: HarnessConfig) -> list[HarnessResult]`.
   - For each system in config.systems: run each FRB task k times (vary mock seed), grade with code_based (+ llm_judge if available), compute:
     - pass@1 (first trial), pass@k (≥1 of k passes), pass^k (ALL k pass), mean_score, per_domain.
   - finroot system: use `interface.core.answer()` if importable, else `FinRootOrchestrator` directly.
   - baselines: `NaiveRAGBaseline`, `SingleAgentBaseline` from `finroot.evaluation.baselines`.
   - Compute `composite_lift_vs_rag_pct = (finroot.mean_score - rag.mean_score)/max(rag.mean_score,1e-9)*100`.
   - `write_metrics(results, path="results/metrics.json")` — include `as_of_sha` (from `git rev-parse --short HEAD`, fail-soft to "unknown") and `generated_at`.
2. `scripts/run_evals.py` — Typer/argparse CLI:
   - `--mock` (default True), `--task <id>` (single task), `--k N` (default 3), `--system <name>` (filter).
   - Prints a summary table; writes metrics.json. Single-task mode prints the full transcript.
3. `tests/unit/test_harness.py` (min 10):
   - run_harness in mock returns results for each system
   - finroot mean_score >= rag mean_score (the whole point; if not, the pipeline or graders are broken — surface loudly)
   - pass^k <= pass@k <= 1.0 invariants hold
   - metrics.json written with required keys
   - single-task mode works

## Acceptance
```bash
PYTHONPATH=src python3 scripts/run_evals.py --mock --task frb-001
PYTHONPATH=src python3 scripts/run_evals.py --mock
PYTHONPATH=src python3 -m pytest tests/unit/test_harness.py -v
cat results/metrics.json | python3 -m json.tool | head -30
```

## Report
`work/reports/wave-6/04-harness.report.md`
