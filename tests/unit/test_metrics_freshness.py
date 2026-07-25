"""Test that the canonical results/metrics.json is fresh.

Catches the class of bug where:
- Someone hand-edits metrics.json (FM-11 violation)
- Someone commits an old metrics.json from a different state
- The eval was run but never re-stamped with the current SHA

The test is intentionally lenient (3-hour window) to allow for
manual rebuilds and CI delays. If you want a tighter check, lower
MAX_AGE_HOURS.
"""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
METRICS_PATH = REPO_ROOT / "results" / "metrics.json"
MAX_AGE_HOURS = 3


def _parse_iso(s: str) -> datetime:
    """Parse an ISO 8601 string, tolerating Z suffix and timezone offsets."""
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def test_metrics_json_exists() -> None:
    assert METRICS_PATH.exists(), (
        "results/metrics.json missing. Run `make evals` to generate it."
    )


def test_metrics_json_is_fresh() -> None:
    """The canonical metric must be recent (regenerated within MAX_AGE_HOURS)."""
    data = json.loads(METRICS_PATH.read_text())
    assert "generated_at" in data, (
        "results/metrics.json missing 'generated_at' field"
    )
    gen_at = _parse_iso(data["generated_at"])
    if gen_at.tzinfo is None:
        gen_at = gen_at.replace(tzinfo=UTC)
    age = datetime.now(UTC) - gen_at
    assert age < timedelta(hours=MAX_AGE_HOURS), (
        f"results/metrics.json is stale: generated_at = {data['generated_at']}, "
        f"age = {age.total_seconds() / 3600:.1f}h (max {MAX_AGE_HOURS}h). "
        "Re-run `make evals` to refresh."
    )


def test_metrics_json_sha_matches_head() -> None:
    """The as_of_sha in the metric must match the current HEAD."""
    data = json.loads(METRICS_PATH.read_text())
    head_sha = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT
    ).decode().strip()
    assert data.get("as_of_sha") == head_sha, (
        f"metrics.json as_of_sha = {data.get('as_of_sha')!r} but HEAD = {head_sha!r}. "
        "Re-run `make evals` to refresh."
    )


def test_metrics_json_pass_at_1_in_range() -> None:
    """All pass@1 values should be in [0, 1]."""
    data = json.loads(METRICS_PATH.read_text())
    for sys_name, sys_data in data["systems"].items():
        for k in ("pass@1", "pass@k", "pass^k", "mean_score"):
            v = sys_data.get(k)
            if v is None:
                continue
            assert 0.0 <= v <= 1.0, (
                f"{sys_name}.{k} = {v} not in [0, 1]"
            )
