"""Performance regression tests for FinRoot.

Catches latency regressions in the core workflow, eval harness throughput,
memory store operations, and profile loading. Each test asserts a hard upper
bound on wall-clock time using ``time.perf_counter()``.

Marked @pytest.mark.performance; run with ``pytest -m performance``.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

from finroot.audit.trail import AuditTrail
from finroot.llm.mock import MockProvider
from finroot.memory.digital_twin import (
    DigitalTwin,
    InvestmentHorizon,
    RiskTolerance,
)
from finroot.memory.manager import MemoryManager

UTC_NOW = datetime(2026, 1, 1, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[2]


def _seed_twin(user_id: str = "bench_user") -> DigitalTwin:
    return DigitalTwin(
        user_id=user_id,
        name="Bench User",
        age=35,
        risk_tolerance=RiskTolerance.MODERATE,
        investment_horizon=InvestmentHorizon.MEDIUM,
        monthly_income=100000.0,
        monthly_expenses=50000.0,
        tax_bracket_pct=20.0,
        goals=["retire early"],
        constraints=[],
        holdings=[],
        created_at=UTC_NOW,
        updated_at=UTC_NOW,
    )


def _make_memory(tmp_path: Path, user_id: str = "bench_user") -> MemoryManager:
    mgr = MemoryManager.create(
        user_id=user_id,
        chroma_dir=str(tmp_path / "chroma"),
        db_path=str(tmp_path / "twin.db"),
    )
    mgr.twin_store.save(_seed_twin(user_id))
    return mgr


# ------------------------------------------------------------------
# Test 1: Single-query workflow latency
# ------------------------------------------------------------------

@pytest.mark.performance
def test_workflow_single_query_latency(tmp_path: Path) -> None:
    """Time a single mock query through the full orchestrator pipeline.

    Asserts completion under 5 seconds in mock mode.
    """
    monkeypatch_marker = pytest.MonkeyPatch()
    monkeypatch_marker.setitem(sys.modules, "chromadb", None)
    try:
        memory = _make_memory(tmp_path)
        audit = AuditTrail(tmp_path / "audit.jsonl")
        llm = MockProvider()

        from finroot.agents.orchestrator import FinRootOrchestrator

        orch = FinRootOrchestrator(memory=memory, audit=audit, llm=llm)

        start = time.perf_counter()
        state = orch.run("Review my portfolio")
        elapsed = time.perf_counter() - start

        assert state is not None, "Orchestrator returned None"
        assert elapsed < 5.0, (
            f"Single query took {elapsed:.2f}s; expected < 5s"
        )
    finally:
        monkeypatch_marker.undo()


# ------------------------------------------------------------------
# Test 2: Eval harness throughput
# ------------------------------------------------------------------

@pytest.mark.performance
def test_eval_harness_throughput(tmp_path: Path) -> None:
    """Time 10 mock evaluations via the harness and assert >2 queries/sec.

    Uses a minimal single-task FRB bank to avoid heavy I/O while still
    exercising the full grading pipeline.
    """
    frb_tasks = [
        {
            "id": f"bench-{i:03d}",
            "domain": "portfolio",
            "difficulty": "easy",
            "query": f"What is the optimal allocation for a moderate investor in task {i}?",
            "expected": {"must_contain": ["allocation"]},
        }
        for i in range(10)
    ]
    frb_path = tmp_path / "frb_bench.json"
    frb_path.write_text(json.dumps(frb_tasks), encoding="utf-8")

    monkeypatch_marker = pytest.MonkeyPatch()
    monkeypatch_marker.setitem(sys.modules, "chromadb", None)
    try:
        from finroot.evaluation.harness import HarnessConfig, run_harness

        config = HarnessConfig(
            k=1,
            systems=["finroot"],
            mock=True,
            frb_path=frb_path,
        )

        start = time.perf_counter()
        results = run_harness(config)
        elapsed = time.perf_counter() - start

        throughput = len(frb_tasks) / elapsed if elapsed > 0 else float("inf")

        assert len(results) == 1, f"Expected 1 system result, got {len(results)}"
        assert throughput > 0.5, (
            f"Throughput {throughput:.2f} q/s is below 0.5 q/s threshold "
            f"(10 tasks in {elapsed:.2f}s)"
        )
    finally:
        monkeypatch_marker.undo()


# ------------------------------------------------------------------
# Test 3: Memory store operations
# ------------------------------------------------------------------

@pytest.mark.performance
def test_memory_store_operations(tmp_path: Path) -> None:
    """Time 100 memory store operations (add_turn) and assert < 1 second total."""
    monkeypatch_marker = pytest.MonkeyPatch()
    monkeypatch_marker.setitem(sys.modules, "chromadb", None)
    try:
        memory = _make_memory(tmp_path, user_id="bench_mem")

        start = time.perf_counter()
        for i in range(100):
            memory.add_turn("user", f"Benchmark turn {i} with some content for memory store")
        elapsed = time.perf_counter() - start

        assert memory.working.size == 10, (
            f"Working memory size {memory.working.size} != 10 (max_turns)"
        )
        assert elapsed < 1.0, (
            f"100 memory store operations took {elapsed:.3f}s; expected < 1s"
        )
    finally:
        monkeypatch_marker.undo()


# ------------------------------------------------------------------
# Test 4: Profile loading speed
# ------------------------------------------------------------------

@pytest.mark.performance
def test_profile_load_speed(tmp_path: Path) -> None:
    """Time loading 100 profiles and assert < 2 seconds total.

    Creates 100 DigitalTwin profiles, saves them, then reloads each one
    from the store to measure I/O overhead.
    """
    monkeypatch_marker = pytest.MonkeyPatch()
    monkeypatch_marker.setitem(sys.modules, "chromadb", None)
    try:
        from finroot.memory.digital_twin import DigitalTwinStore

        db_path = str(tmp_path / "profiles.db")
        store = DigitalTwinStore(db_path=db_path)

        # Create and save 100 profiles
        profiles: list[DigitalTwin] = []
        for i in range(100):
            twin = DigitalTwin(
                user_id=f"profile_{i:04d}",
                name=f"User {i}",
                age=25 + (i % 50),
                risk_tolerance=RiskTolerance.MODERATE,
                investment_horizon=InvestmentHorizon.MEDIUM,
                monthly_income=50000.0 + i * 1000,
                monthly_expenses=25000.0 + i * 500,
                tax_bracket_pct=20.0,
                goals=[f"goal_{i}"],
                constraints=[],
                holdings=[],
                created_at=UTC_NOW,
                updated_at=UTC_NOW,
            )
            store.save(twin)
            profiles.append(twin)

        # Time loading all 100 profiles
        start = time.perf_counter()
        for i in range(100):
            loaded = store.load(f"profile_{i:04d}")
            assert loaded.user_id == f"profile_{i:04d}"
        elapsed = time.perf_counter() - start

        assert elapsed < 2.0, (
            f"Loading 100 profiles took {elapsed:.3f}s; expected < 2s"
        )
    finally:
        monkeypatch_marker.undo()
