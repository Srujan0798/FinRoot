"""Zip-consistency smoke test.

Verifies that the local finroot-submission.zip is internally consistent:
- results/metrics.json inside the zip matches the on-disk canonical file
- docs/SUBMISSION_MESSAGE.md inside the zip mentions the canonical HEAD SHA
- The zip's as_of_sha matches the current git HEAD

If any of these drift, the zip needs to be rebuilt. Run as part of the
submission quality gate; fast (<1s).
"""

from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ZIP_PATH = REPO_ROOT / "finroot-submission.zip"
CANONICAL_METRICS = REPO_ROOT / "results" / "metrics.json"


def _read_zip_member(zip_path: Path, member: str) -> bytes:
    """Read a member from a zip file, or skip the test if it's missing."""
    with zipfile.ZipFile(zip_path) as zf:
        try:
            return zf.read(member)
        except KeyError as e:
            pytest.skip(f"Zip is missing {member}: {e}")


def test_zip_exists() -> None:
    assert ZIP_PATH.exists(), (
        f"finroot-submission.zip not found at {ZIP_PATH}. "
        "Run `bash scripts/make_submission.sh` to build it."
    )


def test_zip_contains_canonical_metrics() -> None:
    """The zip's results/metrics.json must match the on-disk canonical."""
    if not ZIP_PATH.exists():
        pytest.skip("zip not built")
    zip_metrics_bytes = _read_zip_member(ZIP_PATH, "results/metrics.json")
    zip_metrics = json.loads(zip_metrics_bytes)
    assert CANONICAL_METRICS.exists(), (
        "Canonical results/metrics.json missing. Run `make evals` to regenerate."
    )
    canonical_metrics = json.loads(CANONICAL_METRICS.read_text())
    assert zip_metrics["as_of_sha"] == canonical_metrics["as_of_sha"], (
        f"Zip metrics as_of_sha {zip_metrics['as_of_sha']!r} != "
        f"canonical {canonical_metrics['as_of_sha']!r}. Rebuild the zip."
    )
    # Also check the headline numbers match (defense-in-depth: someone could
    # have stamped a new SHA but kept the old numbers)
    for sys_name in ("finroot", "rag"):
        assert zip_metrics["systems"][sys_name]["mean_score"] == (
            canonical_metrics["systems"][sys_name]["mean_score"]
        ), f"Zip {sys_name} mean_score drifted from canonical. Rebuild the zip."


def test_zip_sha_matches_head() -> None:
    """The zip's stamped as_of_sha must match the current git HEAD."""
    if not ZIP_PATH.exists():
        pytest.skip("zip not built")
    zip_metrics_bytes = _read_zip_member(ZIP_PATH, "results/metrics.json")
    zip_metrics = json.loads(zip_metrics_bytes)
    head_sha = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT
    ).decode().strip()
    assert zip_metrics["as_of_sha"] == head_sha, (
        f"Zip metrics as_of_sha {zip_metrics['as_of_sha']!r} != HEAD {head_sha!r}. "
        f"Rebuild the zip after committing."
    )


def test_zip_submission_message_cites_head() -> None:
    """The zip's docs/SUBMISSION_MESSAGE.md must mention the current HEAD SHA."""
    if not ZIP_PATH.exists():
        pytest.skip("zip not built")
    msg_bytes = _read_zip_member(ZIP_PATH, "docs/SUBMISSION_MESSAGE.md")
    msg = msg_bytes.decode("utf-8", errors="replace")
    head_sha = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT
    ).decode().strip()
    # Accept either the full short SHA or just the first 7 chars (git's
    # default short format)
    short_sha = head_sha[:7]
    assert short_sha in msg, (
        f"docs/SUBMISSION_MESSAGE.md inside the zip does not mention HEAD "
        f"{head_sha!r}. The submission message is stale; rebuild the zip "
        f"after running `make evals` and updating the message."
    )


def test_zip_under_5mb() -> None:
    """The zip should be reasonably sized (under 5 MB for a code-only artifact)."""
    if not ZIP_PATH.exists():
        pytest.skip("zip not built")
    size = ZIP_PATH.stat().st_size
    assert size < 5 * 1024 * 1024, (
        f"Zip is {size:,} bytes, which is over 5 MB. Investigate bloat."
    )


def test_zip_clean_of_real_key_shapes() -> None:
    """Real-key-shape secret scan: no sk-, ghp-, gsk-, or AKIA values in the zip."""
    if not ZIP_PATH.exists():
        pytest.skip("zip not built")
    # Extract to a temp dir and grep
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(ZIP_PATH) as zf:
            zf.extractall(tmp_path)
        # Use ripgrep if available, else grep -r
        result = subprocess.run(
            [
                "grep", "-rInE",
                r"(sk-[A-Za-z0-9]{20,}|gsk_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16,})",
                str(tmp_path),
            ],
            capture_output=True,
        )
        # grep returns 1 when no matches — that's success
        assert result.returncode == 1, (
            f"Real-key-shape secrets found in zip:\n{result.stdout.decode()}"
        )


def test_zip_contains_required_artifacts() -> None:
    """The zip must contain a small set of expected files for a judge to
    evaluate the submission: LICENSE, README, requirements.txt, and the
    headline metric."""
    if not ZIP_PATH.exists():
        pytest.skip("zip not built")
    with zipfile.ZipFile(ZIP_PATH) as zf:
        names = set(zf.namelist())
    # Case-insensitive check for each required artifact (use lowercase form)
    names_lower = {n.lower() for n in names}
    required = {
        "license": ["license", "license.md", "license.txt"],
        "readme": ["readme.md", "readme"],
        "requirements": ["requirements.txt", "pyproject.toml"],
        "metric": ["results/metrics.json"],
    }
    for label, candidates in required.items():
        found = any(c in names_lower for c in candidates)
        assert found, (
            f"Zip is missing required artifact: {label} "
            f"(looked for {candidates}). Zip has {len(names)} files."
        )


def test_zip_no_node_modules_or_pycache() -> None:
    """Sanity: the zip must not contain development artifacts that bloat it."""
    if not ZIP_PATH.exists():
        pytest.skip("zip not built")
    with zipfile.ZipFile(ZIP_PATH) as zf:
        bad = [
            n for n in zf.namelist()
            if "__pycache__" in n
            or "/.pytest_cache" in n
            or "/.ruff_cache" in n
            or "/node_modules/" in n
            or n.endswith(".pyc")
        ]
    assert not bad, (
        f"Zip contains dev artifacts (should be excluded by make_submission.sh): "
        f"{bad[:10]}{'...' if len(bad) > 10 else ''}"
    )
