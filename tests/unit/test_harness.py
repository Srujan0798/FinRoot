"""Unit tests for the FRB benchmark harness (finroot.evaluation.harness).

Tests the core loop, pass@k computation, metrics.json output, and the
deterministic single-task path.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from finroot.evaluation.harness import (
    HarnessConfig,
    HarnessResult,
    _ensure_final,
    run_harness,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_FRB_SAMPLE = [
    {
        "id": "test-001",
        "domain": "tax",
        "difficulty": "easy",
        "query": "What is the tax on ₹2L LTCG from equity?",
        "twin_id": "twin_priya_sharma_001",
        "expected": {
            "must_mention": ["LTCG", "tax"],
            "must_not": ["guaranteed"],
            "min_citations": 1,
            "numeric_answer": 10400.0,
            "numeric_tolerance": 500.0,
            "expected_confidence": "medium",
        },
        "rationale": "LTCG 10% over ₹1L exemption + 4% cess = ₹10,400",
    },
    {
        "id": "test-002",
        "domain": "portfolio",
        "difficulty": "medium",
        "query": "Review my portfolio allocation",
        "twin_id": "twin_priya_sharma_001",
        "expected": {
            "must_mention": ["allocation"],
            "must_not": ["guaranteed"],
            "min_citations": 1,
        },
        "rationale": "Standard portfolio review",
    },
]


@pytest.fixture()
def frb_file(tmp_path: Path) -> Path:
    p = tmp_path / "frb_questions.json"
    p.write_text(json.dumps(_FRB_SAMPLE))
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestHarnessConfig:
    def test_defaults(self) -> None:
        cfg = HarnessConfig()
        assert cfg.k == 2
        assert "finroot" in cfg.systems
        assert cfg.mock is True

    def test_from_dict(self) -> None:
        cfg = HarnessConfig(k=3, systems=["rag"], mock=False)
        assert cfg.k == 3
        assert cfg.systems == ["rag"]


class TestHarnessResult:
    def test_model_dump_roundtrip(self) -> None:
        r = HarnessResult(
            system="finroot",
            pass_at_1=0.5,
            pass_at_k=0.75,
            pass_hat_k=0.25,
            mean_score=0.65,
            n_tasks=4,
            n_trials=3,
            elapsed_sec=1.23,
        )
        d = r.model_dump()
        assert d["system"] == "finroot"
        assert d["mean_score"] == 0.65


class TestEnsureFinal:
    def test_promotes_candidate(self) -> None:
        from finroot.schemas.state import AgentState
        from finroot.schemas.recommendation import Recommendation, ConfidenceLevel

        state = AgentState(
            query="test",
            candidate=Recommendation(summary="x", analysis="x", confidence=ConfidenceLevel.MEDIUM),
        )
        assert state.final is None
        _ensure_final(state)
        assert state.final is not None
        assert state.final.summary == "x"

    def test_no_promote_when_final_set(self) -> None:
        from finroot.schemas.state import AgentState
        from finroot.schemas.recommendation import Recommendation, ConfidenceLevel

        state = AgentState(
            query="test",
            final=Recommendation(summary="already", analysis="already", confidence=ConfidenceLevel.HIGH),
            candidate=Recommendation(summary="other", analysis="other", confidence=ConfidenceLevel.LOW),
        )
        _ensure_final(state)
        assert state.final.summary == "already"


class TestRunHarness:
    def test_mock_returns_results(
        self, frb_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cfg = HarnessConfig(
            k=1,
            systems=["rag"],
            mock=True,
            frb_path=str(frb_file),
            metrics_path=str(tmp_path / "metrics.json"),
        )
        results = run_harness(cfg)
        assert len(results) == 1
        assert results[0].system == "rag"
        assert 0.0 <= results[0].mean_score <= 1.0

    def test_metrics_json_written(
        self, frb_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        out = tmp_path / "metrics.json"
        cfg = HarnessConfig(
            k=1,
            systems=["rag"],
            mock=True,
            frb_path=str(frb_file),
            metrics_path=str(out),
        )
        run_harness(cfg)
        assert out.exists()
        data = json.loads(out.read_text())
        assert "as_of_sha" in data
        assert "systems" in data
        assert "rag" in data["systems"]
        assert data["n_tasks"] == 2
        assert data["k"] == 1

    def test_finroot_in_results(
        self, frb_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("FINROOT_LLM_PROVIDER", "mock")
        cfg = HarnessConfig(
            k=1,
            systems=["finroot"],
            mock=True,
            frb_path=str(frb_file),
            metrics_path=str(tmp_path / "metrics.json"),
        )
        results = run_harness(cfg)
        assert len(results) == 1
        assert results[0].system == "finroot"
        assert 0.0 <= results[0].mean_score <= 1.0

    def test_pass_at_k_invariants(
        self, frb_file: Path, tmp_path: Path
    ) -> None:
        cfg = HarnessConfig(
            k=2,
            systems=["rag"],
            mock=True,
            frb_path=str(frb_file),
            metrics_path=str(tmp_path / "metrics.json"),
        )
        results = run_harness(cfg)
        r = results[0]
        assert r.pass_at_k >= r.pass_hat_k
        assert r.pass_at_1 <= 1.0
        assert r.n_tasks == 2
        assert r.n_trials == 2
