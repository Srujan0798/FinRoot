"""Test that the canonical results/metrics.json is fresh.

Catches the class of bug where:
- Someone hand-edits metrics.json (FM-11 violation)
- Someone commits an old metrics.json from a different state
- src/, data/gold/, or evals/ changed after the eval was last run,
  and nobody re-stamped metrics with the new state

Freshness is judged by git history, not wall-clock time or literal
SHA equality:
- A committed file can never literally embed its own future commit
  hash (content hashing is not a fixed point), so as_of_sha will
  always be HEAD or an *ancestor* of HEAD, never HEAD itself, once
  committed. Requiring exact equality guarantees failure on every
  clone taken after the metrics-regen commit.
- A wall-clock "generated within N hours" window guarantees failure
  for any judge/CI run that happens more than N hours after the
  metrics were generated — which is virtually every real judging
  scenario. It says nothing about correctness.
The real invariant we want: no commit that could change eval results
(src/, data/gold/, evals/) landed after as_of_sha.
"""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
METRICS_PATH = REPO_ROOT / "results" / "metrics.json"
RESULT_AFFECTING_PATHS = ["src", "data/gold", "evals"]


def _parse_iso(s: str) -> datetime:
    """Parse an ISO 8601 string, tolerating Z suffix and timezone offsets."""
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def _commits_since(sha: str, paths: list[str]) -> int:
    """Count commits touching `paths` strictly after `sha`, up to HEAD."""
    result = subprocess.run(
        ["git", "rev-list", "--count", f"{sha}..HEAD", "--", *paths],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return int(result.stdout.strip() or "0")


def test_metrics_json_exists() -> None:
    assert METRICS_PATH.exists(), "results/metrics.json missing. Run `make evals` to generate it."


def test_metrics_json_is_fresh() -> None:
    """generated_at must be a sane, non-future timestamp (sanity, not a wall-clock cliff)."""
    data = json.loads(METRICS_PATH.read_text())
    assert "generated_at" in data, "results/metrics.json missing 'generated_at' field"
    gen_at = _parse_iso(data["generated_at"])
    if gen_at.tzinfo is None:
        gen_at = gen_at.replace(tzinfo=UTC)
    assert gen_at <= datetime.now(UTC), (
        f"results/metrics.json generated_at = {data['generated_at']!r} is in the future."
    )


def test_metrics_json_sha_matches_head() -> None:
    """No result-affecting commit may have landed after metrics.json's as_of_sha."""
    data = json.loads(METRICS_PATH.read_text())
    as_of = data.get("as_of_sha")
    assert as_of, "metrics.json missing as_of_sha"
    n = _commits_since(as_of, RESULT_AFFECTING_PATHS)
    assert n == 0, (
        f"{n} commit(s) touching {RESULT_AFFECTING_PATHS} landed after "
        f"metrics.json's as_of_sha={as_of!r}. Re-run `make evals` to refresh."
    )


def test_metrics_json_pass_at_1_in_range() -> None:
    """All pass@1 values should be in [0, 1]."""
    data = json.loads(METRICS_PATH.read_text())
    for sys_name, sys_data in data["systems"].items():
        for k in ("pass@1", "pass@k", "pass^k", "mean_score"):
            v = sys_data.get(k)
            if v is None:
                continue
            assert 0.0 <= v <= 1.0, f"{sys_name}.{k} = {v} not in [0, 1]"
