"""Unit tests for evaluation report generator (wave-6/05).

Covers ``generate_report`` and ``write_report``: markdown output structure,
headline lift, system/domain tables, missing-file failure, and disk I/O.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from finroot.evaluation.report import generate_report, write_report

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_METRICS: dict[str, Any] = {
    "as_of_sha": "abc1234",
    "generated_at": "2026-06-20T12:00:00+00:00",
    "k": 3,
    "mock": True,
    "n_tasks": 24,
    "systems": {
        "finroot": {
            "system": "finroot",
            "pass_at_1": 0.75,
            "pass_at_k": 0.80,
            "pass_hat_k": 0.60,
            "mean_score": 0.85,
            "per_domain": {"portfolio": 0.90, "risk": 0.80, "tax": 0.75},
            "n_tasks": 24,
            "n_trials": 3,
            "elapsed_sec": 45.0,
        },
        "rag": {
            "system": "rag",
            "pass_at_1": 0.20,
            "pass_at_k": 0.25,
            "pass_hat_k": 0.10,
            "mean_score": 0.40,
            "per_domain": {"portfolio": 0.45, "risk": 0.35, "tax": 0.30},
            "n_tasks": 24,
            "n_trials": 3,
            "elapsed_sec": 0.5,
        },
    },
    "composite_lift_vs_rag_pct": 112.5,
    "composite_lift_vs_rag_x": 2.12,
    "headline_finroot_mean": 0.85,
    "headline_rag_mean": 0.40,
}


@pytest.fixture
def fixture_dir(tmp_path: Path) -> Path:
    d = tmp_path / "metrics"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def metrics_path(fixture_dir: Path) -> str:
    p = fixture_dir / "metrics.json"
    p.write_text(json.dumps(_METRICS))
    return str(p)


# ---------------------------------------------------------------------------
# generate_report
# ---------------------------------------------------------------------------


class TestGenerateReport:
    def test_returns_string(self, metrics_path: str) -> None:
        report = generate_report(metrics_path)
        assert isinstance(report, str)
        assert len(report) > 100

    def test_headline_lift_present(self, metrics_path: str) -> None:
        report = generate_report(metrics_path)
        assert "112.5%" in report
        assert "2.12" in report
        assert "Composite lift vs RAG" in report

    def test_system_table_present(self, metrics_path: str) -> None:
        report = generate_report(metrics_path)
        assert "| System |" in report
        assert "| finroot |" in report
        assert "| rag |" in report
        assert "75.0%" in report  # finroot pass@1 formatted

    def test_per_domain_rows_present(self, metrics_path: str) -> None:
        report = generate_report(metrics_path)
        assert "Per-Domain Breakdown" in report
        assert "| portfolio |" in report
        assert "| risk |" in report
        assert "| tax |" in report

    def test_methodology_note_present(self, metrics_path: str) -> None:
        report = generate_report(metrics_path)
        assert "## Methodology" in report
        assert "3" in report  # k=3
        assert "24" in report  # n_tasks=24

    def test_as_of_sha_stamp(self, metrics_path: str) -> None:
        report = generate_report(metrics_path)
        assert "abc1234" in report

    def test_missing_file_raises(self) -> None:
        with pytest.raises(FileNotFoundError) as exc:
            generate_report("/nonexistent/path/metrics.json")
        assert "run_evals.py" in str(exc.value)

    def test_per_domain_handles_missing_domain(self, fixture_dir: Path) -> None:
        """A system missing a domain that another has should show '—'."""
        data = dict(_METRICS)
        data["systems"]["finroot"]["per_domain"] = {"portfolio": 0.9}
        data["systems"]["rag"]["per_domain"] = {"portfolio": 0.4, "risk": 0.3}
        p = fixture_dir / "metrics_partial.json"
        p.write_text(json.dumps(data))
        report = generate_report(str(p))
        assert "| portfolio |" in report
        assert "| risk |" in report


class TestWriteReport:
    def test_creates_files(self, metrics_path: str, fixture_dir: Path) -> None:
        out = fixture_dir / "reports"
        out.mkdir(parents=True, exist_ok=True)
        result = write_report(metrics_path=metrics_path, out_dir=str(out))
        assert result.exists()
        assert (out / "latest.md").exists()
        assert result.name.startswith("frb_report_")
        assert result.name.endswith(".md")

    def test_returns_path(self, metrics_path: str, fixture_dir: Path) -> None:
        out = fixture_dir / "reports"
        out.mkdir(parents=True, exist_ok=True)
        result = write_report(metrics_path=metrics_path, out_dir=str(out))
        assert isinstance(result, Path)

    def test_latest_is_overwritten(self, metrics_path: str, fixture_dir: Path) -> None:
        out = fixture_dir / "reports"
        out.mkdir(parents=True, exist_ok=True)
        write_report(metrics_path=metrics_path, out_dir=str(out))
        content1 = (out / "latest.md").read_text()
        write_report(metrics_path=metrics_path, out_dir=str(out))
        content2 = (out / "latest.md").read_text()
        assert content1 == content2  # deterministic
