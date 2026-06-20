"""Tiny CLI wrapper for the eval harness. Most logic lives in ``harness.py``.

Usage:
    python -m scripts.run_evals --mock --task frb-001
    python -m scripts.run_evals --mock
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from finroot.evaluation.harness import HarnessConfig, run_harness  # noqa: E402


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Run FinRoot FRB benchmark")
    ap.add_argument("--k", type=int, default=2)
    ap.add_argument("--max-tasks", type=int, default=None)
    ap.add_argument("--task", default=None)
    ap.add_argument("--system", default=None)
    ap.add_argument("--mock", action="store_true", default=True)
    ap.add_argument("--no-mock", dest="mock", action="store_false")
    args = ap.parse_args()

    if args.task:
        import os

        os.environ["FINROOT_LLM_PROVIDER"] = "mock"
        from evals.graders.code_based import grade_code  # noqa: PLC0415

        from interface.core import answer  # noqa: PLC0415

        tasks = [
            t
            for t in __import__("json").loads(Path("data/gold/frb_questions.json").read_text())
            if t["id"] == args.task
        ]
        if not tasks:
            raise SystemExit(f"task {args.task} not found")
        t = tasks[0]
        state = answer(t["query"], mock=True)
        if state.final is None and state.candidate is not None:
            state.final = state.candidate
        r = grade_code(t, state)
        print(f"{t['id']}: score={r.score:.3f} passed={r.passed}")
        print(f"summary: {state.final.summary[:200] if state.final else '<none>'}")
        return

    cfg = HarnessConfig(k=args.k, max_tasks=args.max_tasks, mock=args.mock)
    if args.system:
        cfg.systems = [args.system]
    results = run_harness(cfg)
    print("\nWrote results/metrics.json")
    for r in results:
        print(
            f"  {r.system:14} mean={r.mean_score:.3f}  "
            f"pass@1={r.pass_at_1:.3f}  pass^k={r.pass_hat_k:.3f}  "
            f"({r.n_tasks} tasks, k={r.n_trials}, {r.elapsed_sec}s)"
        )


if __name__ == "__main__":
    main()
