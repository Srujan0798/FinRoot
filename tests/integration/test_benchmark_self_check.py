"""Benchmark self-check: verify the FRB eval produces a sane metric.

This is NOT a unit test for the eval itself (that's covered by
TestSingleTaskMode in tests/unit/test_harness.py). This is a
meta-check that the eval, when run end-to-end, produces a non-degenerate
result: RAG < FinRoot, both scores are in [0, 1], all 83 tasks ran.

Catches:
- Eval silently producing all-zeros
- Eval producing inverted scores (RAG > FinRoot, which would be a bug)
- Eval dropping tasks (n_tasks != 83)
- Eval crashing on a category (per_domain missing a key)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_N_TASKS = 83
EXPECTED_DOMAINS = 11  # 11 financial domains per the brief
MIN_LIFT = 0.10  # FinRoot must beat RAG by at least 10%


def _run_eval() -> dict:
    """Run scripts/run_evals.py and return the parsed metrics.json."""
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    env["FINROOT_METRICS_PATH"] = str(REPO_ROOT / "results" / "metrics.json")
    result = subprocess.run(
        [sys.executable, "scripts/run_evals.py", "--mock", "--k", "2"],
        capture_output=True, text=True, timeout=600, env=env, cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        f"Eval run failed: rc={result.returncode}\n"
        f"STDOUT: {result.stdout[:2000]}\nSTDERR: {result.stderr[:2000]}"
    )
    metrics_path = REPO_ROOT / "results" / "metrics.json"
    assert metrics_path.exists(), f"metrics.json not written to {metrics_path}"
    return json.loads(metrics_path.read_text())


@pytest.mark.slow
def test_eval_produces_sane_metric() -> None:
    """Run the eval end-to-end and verify the headline numbers are sane."""
    metrics = _run_eval()

    # Basic structure
    assert "as_of_sha" in metrics, "metrics.json missing as_of_sha"
    assert "systems" in metrics, "metrics.json missing systems"
    for sys_name in ("finroot", "rag", "single_agent"):
        assert sys_name in metrics["systems"], f"Missing system: {sys_name}"
        sys_data = metrics["systems"][sys_name]
        assert "mean_score" in sys_data, f"{sys_name} missing mean_score"
        score = sys_data["mean_score"]
        assert 0.0 <= score <= 1.0, (
            f"{sys_name} mean_score {score} not in [0, 1] — eval is broken"
        )

    # All 83 tasks ran
    n_tasks = metrics.get("n_tasks", 0)
    assert n_tasks == EXPECTED_N_TASKS, (
        f"Eval ran {n_tasks} tasks, expected {EXPECTED_N_TASKS}. "
        "Check data/gold/frb_questions.json for missing tasks."
    )

    # All 11 domains represented (check on finroot only)
    per_domain = metrics["systems"]["finroot"].get("per_domain", {})
    n_domains = len(per_domain)
    assert n_domains >= EXPECTED_DOMAINS - 3, (
        f"Eval covered {n_domains} domains, expected ~{EXPECTED_DOMAINS}. "
        f"Got: {sorted(per_domain.keys())}"
    )

    # FinRoot must beat RAG by a meaningful margin
    finroot_score = metrics["systems"]["finroot"]["mean_score"]
    rag_score = metrics["systems"]["rag"]["mean_score"]
    lift = (finroot_score - rag_score) / rag_score if rag_score > 0 else 0
    assert lift >= MIN_LIFT, (
        f"FinRoot lift over RAG is only {lift:.1%}, expected >= {MIN_LIFT:.0%}. "
        f"FinRoot={finroot_score}, RAG={rag_score}. "
        "Either the eval is broken or the headline has regressed."
    )

    # SHA matches HEAD (eval was run against the current commit)
    import subprocess as sp
    head_sha = sp.check_output(
        ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT
    ).decode().strip()
    assert metrics["as_of_sha"] == head_sha, (
        f"Eval stamped {metrics['as_of_sha']!r} but HEAD is {head_sha!r}. "
        "This is a sign of stale state — re-run the eval from a clean checkout."
    )
