#!/usr/bin/env python3
"""FRB evaluation harness — CLI runner (wave-6, task 04).

Loads the FRB question bank, runs each system ``k`` times, grades with the
deterministic code-based grader, and writes the single-source
``results/metrics.json``. The 35%-weight Reasoning-Quality proof lives in
that JSON.

Usage::

    PYTHONPATH=src python3 scripts/run_evals.py --mock --task frb-001
    PYTHONPATH=src python3 scripts/run_evals.py --mock
    PYTHONPATH=src python3 scripts/run_evals.py --mock --system finroot --k 5
    PYTHONPATH=src python3 scripts/run_evals.py --mock --llm-judge

Notes
-----
* The ``evals.graders`` package is PEP-420 / ``__init__.py``-based and lives
  at the repo root, NOT under ``src/``. With ``PYTHONPATH=src``, it is not
  importable until we prepend the repo root to ``sys.path``. This script
  does that at startup so the same ``PYTHONPATH=src`` command the
  orchestrator uses to invoke it Just Works. See
  ``docs/waves/wave-6-gotchas.md`` for the rationale.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

# Repo root on sys.path BEFORE anything else imports ``evals``.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Now safe to import the project modules.
from finroot.evaluation.harness import (  # noqa: E402
    DEFAULT_FRB_PATH,
    DEFAULT_METRICS_PATH,
    HarnessConfig,
    HarnessResult,
    TrialResult,
    compute_composite_lift,
    run_harness,
    write_metrics,
)

logger = logging.getLogger("finroot.run_evals")


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def _fmt_float(x: float, width: int = 7) -> str:
    """Format a float with fixed width for the summary table."""
    return f"{x:>{width}.4f}"


def _fmt_pct(x: float, width: int = 8) -> str:
    """Format a percentage."""
    return f"{x:>{width}.2f}%"


def print_summary_table(results: list[HarnessResult]) -> None:
    """Print the per-system summary table that goes into the deck."""
    if not results:
        print("No results to display.")
        return

    headers = ("system", "n_tasks", "pass@1", "pass@k", "pass^k", "mean_score")
    widths = (14, 8, 8, 8, 8, 11)

    def _row(values: tuple[str, ...]) -> str:
        return "  ".join(v.ljust(w) for v, w in zip(values, widths, strict=True))

    print(_row(headers))
    print(_row(tuple("-" * w for w in widths)))
    for r in results:
        print(
            _row(
                (
                    r.system,
                    str(r.n_tasks),
                    _fmt_float(r.pass_at_1),
                    _fmt_float(r.pass_at_k),
                    _fmt_float(r.pass_hat_k),
                    _fmt_float(r.mean_score),
                )
            )
        )

    # Per-domain breakdown
    domains: set[str] = set()
    for r in results:
        domains.update(r.per_domain.keys())

    if domains:
        print()
        print("Per-domain mean_score:")
        header = "  ".join(["system".ljust(14)] + [d.ljust(10) for d in sorted(domains)])
        print(header)
        for r in results:
            row = [r.system.ljust(14)]
            for d in sorted(domains):
                val = r.per_domain.get(d, 0.0)
                row.append(_fmt_float(val, 10))
            print("  ".join(row))


def print_transcript(task: dict, trials: list[TrialResult]) -> None:
    """Print the full transcript for a single FRB task (CLI ``--task`` mode)."""
    print("=" * 78)
    print(f"Task: {task.get('id')}  domain={task.get('domain')}  "
          f"difficulty={task.get('difficulty')}  twin_id={task.get('twin_id')}")
    print(f"Query: {task.get('query')}")
    print("-" * 78)
    expected = task.get("expected", {}) or {}
    print(f"Expected must_mention: {expected.get('must_mention')}")
    print(f"Expected must_not:     {expected.get('must_not')}")
    print(f"Min citations:         {expected.get('min_citations')}")
    print(f"Expected confidence:   {expected.get('expected_confidence')}")
    if expected.get("numeric_answer") is not None:
        print(f"Expected numeric:      {expected.get('numeric_answer')} "
              f"±{expected.get('numeric_tolerance')}")
    print("=" * 78)

    for t in trials:
        bd = t.grader_breakdown
        breakdown_lines = []
        if "must_mention" in bd and isinstance(bd["must_mention"], dict):
            mm = bd["must_mention"]
            breakdown_lines.append(
                f"    must_mention: {mm.get('ratio', 0):.2f} "
                f"(missing: {mm.get('missing', [])})"
            )
        if "citations" in bd and isinstance(bd["citations"], dict):
            c = bd["citations"]
            breakdown_lines.append(
                f"    citations:    {c.get('count', 0)} "
                f"(min_required: {c.get('min_required', 0)})"
            )
        if "numeric" in bd and isinstance(bd["numeric"], dict):
            n = bd["numeric"]
            breakdown_lines.append(
                f"    numeric:      expected={n.get('expected')} "
                f"extracted={n.get('extracted')} diff={n.get('diff')}"
            )
        if "confidence" in bd and isinstance(bd["confidence"], dict):
            cf = bd["confidence"]
            breakdown_lines.append(
                f"    confidence:   expected={cf.get('expected')} "
                f"actual={cf.get('actual')}"
            )
        if "error" in bd:
            breakdown_lines.append(f"    error:        {bd['error']}")

        print()
        print(f"  trial {t.trial}  system={t.system}  passed={t.passed}  "
              f"score={t.score:.4f}  elapsed={t.elapsed_s:.2f}s")
        for line in breakdown_lines:
            print(line)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _gather_trials_for_task(
    task: dict, config: HarnessConfig
) -> list[TrialResult]:
    """Re-run the harness restricted to one task to build a transcript.

    The full ``run_harness`` aggregates and discards per-trial records; here
    we keep them so the CLI's ``--task`` mode can print the full transcript.
    """
    # Re-import the internal helpers via the harness module (private but
    # well-typed; we are within the same package so this is fine).
    from finroot.evaluation import harness as _h

    frb = _h._load_frb(config.frb_path)
    frb = [q for q in frb if q.get("id") == task.get("id")]
    if not frb:
        raise ValueError(f"No FRB task matches --task {task.get('id')!r}")

    # Inline a slim copy of the harness loop. We can't reuse run_harness
    # because it returns HarnessResult (aggregated), not TrialResult.
    twins = _h._load_twins(_h.DEFAULT_TWIN_PROFILES_PATH)
    systems = (
        [config.system_filter]
        if config.system_filter
        else list(config.systems)
    )
    judge_llm = None
    if config.judge_with_llm:
        from finroot.llm.mock import MockProvider
        judge_llm = MockProvider()

    trials: list[TrialResult] = []
    for t in frb:
        twin_id = t.get("twin_id")
        twin = twins.get(twin_id) if twin_id else None
        for system in systems:
            for trial_idx in range(config.k):
                trial_query = (
                    str(t.get("query", "")) + _h._seed_suffix(trial_idx, config.base_seed)
                )
                t0 = time.monotonic()
                error: str | None = None
                try:
                    state = _h._run_system(system, trial_query, twin, twin_id)
                except Exception as exc:  # noqa: BLE001
                    error = f"{type(exc).__name__}: {exc}"
                    state = None  # type: ignore[assignment]
                elapsed = time.monotonic() - t0

                if state is None:
                    trials.append(
                        TrialResult(
                            system=system,
                            task_id=str(t.get("id", "")),
                            domain=str(t.get("domain", "")),
                            trial=trial_idx,
                            passed=False,
                            score=0.0,
                            grader_breakdown={"error": error or "unknown"},
                            elapsed_s=round(elapsed, 4),
                            error=error,
                        )
                    )
                    continue

                score, passed, breakdown = _h._grade_trial(t, state)
                if config.judge_with_llm:
                    score, passed, breakdown = _h._maybe_blend_judge(
                        t, state, judge_llm, score, breakdown
                    )
                trials.append(
                    TrialResult(
                        system=system,
                        task_id=str(t.get("id", "")),
                        domain=str(t.get("domain", "")),
                        trial=trial_idx,
                        passed=passed,
                        score=score,
                        grader_breakdown=breakdown,
                        elapsed_s=round(elapsed, 4),
                        error=error,
                    )
                )
    return trials


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="run_evals",
        description=(
            "Run the FRB evaluation harness across FinRoot + baselines. "
            "Writes results/metrics.json (the single source of numbers)."
        ),
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        default=True,
        help="Force the offline MockProvider (default: True).",
    )
    parser.add_argument(
        "--no-mock",
        dest="mock",
        action="store_false",
        help="Disable mock mode (use the configured real provider — rare; tests use mock).",
    )
    parser.add_argument(
        "--task",
        type=str,
        default=None,
        help="Run only this FRB task id (single-task transcript mode).",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=3,
        help="Trials per task per system (pass@k denominator). Default: 3.",
    )
    parser.add_argument(
        "--system",
        type=str,
        default=None,
        choices=("finroot", "rag", "single_agent"),
        help="Restrict to one system (default: all three).",
    )
    parser.add_argument(
        "--frb-path",
        type=Path,
        default=DEFAULT_FRB_PATH,
        help="FRB question bank path (default: data/gold/frb_questions.json).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_METRICS_PATH,
        help="metrics.json output path (default: results/metrics.json).",
    )
    parser.add_argument(
        "--llm-judge",
        action="store_true",
        help="Blend in the LLM-judge grader (0.5 code + 0.5 judge).",
    )
    parser.add_argument(
        "--base-seed",
        type=int,
        default=0,
        help="Base seed for trial-by-trial prompt variation (default: 0).",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose logging.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config = HarnessConfig(
        k=args.k,
        systems=["finroot", "rag", "single_agent"],
        mock=args.mock,
        frb_path=args.frb_path,
        task_filter=args.task,
        system_filter=args.system,
        judge_with_llm=args.llm_judge,
        base_seed=args.base_seed,
    )

    if config.task_filter:
        # Single-task mode — print full transcript for that task across all
        # configured systems (or the filtered one).
        from finroot.evaluation import harness as _h

        frb = _h._load_frb(config.frb_path)
        target = next(
            (q for q in frb if q.get("id") == config.task_filter),
            None,
        )
        if target is None:
            print(
                f"ERROR: FRB task {config.task_filter!r} not found in {config.frb_path}",
                file=sys.stderr,
            )
            return 2

        trials = _gather_trials_for_task(target, config)
        print_transcript(target, trials)

        # Also write a single-task subset of metrics.json so downstream
        # tools (the W6-05 report generator) still have a file to read.
        results = _h._aggregate(
            trials,
            [config.system_filter] if config.system_filter else list(config.systems),
            k=config.k,
        )
        report = write_metrics(
            results,
            path=args.out,
            k=config.k,
            n_tasks=1,
        )
        print()
        print(f"Wrote metrics (single-task subset) to {args.out}")
        print(f"  as_of_sha={report.as_of_sha}  n_tasks={report.n_tasks}  k={report.k}")
        return 0

    # Full-bank mode.
    print(f"FRB harness: k={config.k} systems={config.systems} mock={config.mock} "
          f"judge_with_llm={config.judge_with_llm}")
    print(f"FRB bank: {config.frb_path}")
    print()

    t0 = time.monotonic()
    results = run_harness(config)
    elapsed = time.monotonic() - t0

    # n_tasks = number of unique task ids we actually ran.
    frb_full = json.loads(config.frb_path.read_text(encoding="utf-8"))
    n_tasks = len(frb_full) if isinstance(frb_full, list) else 0

    print_summary_table(results)
    print()
    print(f"Composite lift vs RAG: {compute_composite_lift(results):+.2f}%")
    print(f"Total time: {elapsed:.1f}s")
    print()

    report = write_metrics(results, path=args.out, k=config.k, n_tasks=n_tasks)
    print(f"Wrote {args.out}  as_of_sha={report.as_of_sha}  "
          f"generated_at={report.generated_at}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())