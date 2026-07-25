"""Tests for JSONL store write-read round-trip with eval trial data.

Exercises ``JsonlAuditStore`` (``finroot.audit.store``) with
``TrialResult`` payloads from the eval harness to verify:
1. File creation on first write
2. Write → read round-trip (field fidelity)
3. Append multiple trials and read all back
4. Missing file returns empty list
5. Corrupt line is handled gracefully
6. Concurrent writes don't corrupt the store

Run with::

    PYTHONPATH=src python3 -m pytest tests/unit/test_eval_harness_store.py -v
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

import pytest

from finroot.audit.store import AuditStoreIOError, JsonlAuditStore
from finroot.evaluation.harness import TrialResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.wave1


def _make_trial(**overrides: Any) -> TrialResult:
    """Build a minimal TrialResult with sensible defaults."""
    defaults: dict[str, Any] = {
        "system": "finroot",
        "task_id": "frb-001",
        "domain": "portfolio",
        "trial": 0,
        "passed": True,
        "score": 0.85,
        "grader_breakdown": {"mentions": 3, "citations": 2},
        "elapsed_s": 1.23,
        "error": None,
    }
    defaults.update(overrides)
    return TrialResult(**defaults)


def _write_trial(store: JsonlAuditStore, trial: TrialResult) -> None:
    """Persist a TrialResult as one JSONL line via the store."""
    store.append(trial.model_dump(mode="json"))


def _read_trials(store: JsonlAuditStore) -> list[TrialResult]:
    """Read all lines back as TrialResult instances."""
    return [TrialResult.model_validate(raw) for raw in store.read_all()]


# ---------------------------------------------------------------------------
# 1. File creation
# ---------------------------------------------------------------------------


class TestJsonlStoreCreatesFile:
    def test_creates_jsonl_file_on_first_write(self, tmp_path: Path) -> None:
        store_path = tmp_path / "trials.jsonl"
        assert not store_path.exists()

        store = JsonlAuditStore(store_path)
        trial = _make_trial()
        _write_trial(store, trial)

        assert store_path.exists()
        assert store_path.stat().st_size > 0

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        store_path = tmp_path / "nested" / "dir" / "trials.jsonl"
        store = JsonlAuditStore(store_path)
        _write_trial(store, _make_trial())
        assert store_path.exists()


# ---------------------------------------------------------------------------
# 2. Write → read round-trip
# ---------------------------------------------------------------------------


class TestJsonlStoreWriteReadRoundtrip:
    def test_roundtrip_preserves_all_fields(self, tmp_path: Path) -> None:
        store = JsonlAuditStore(tmp_path / "trials.jsonl")
        original = _make_trial(
            system="rag",
            task_id="frb-042",
            domain="risk",
            trial=2,
            passed=False,
            score=0.31,
            grader_breakdown={"mentions": 0, "citations": 0},
            elapsed_s=0.456,
            error="TimeoutError: exceeded 30s",
        )
        _write_trial(store, original)

        trials = _read_trials(store)
        assert len(trials) == 1
        restored = trials[0]

        assert restored.system == original.system
        assert restored.task_id == original.task_id
        assert restored.domain == original.domain
        assert restored.trial == original.trial
        assert restored.passed == original.passed
        assert restored.score == pytest.approx(original.score)
        assert restored.grader_breakdown == original.grader_breakdown
        assert restored.elapsed_s == pytest.approx(original.elapsed_s)
        assert restored.error == original.error

    def test_roundtrip_jsonl_is_valid_json_per_line(self, tmp_path: Path) -> None:
        store = JsonlAuditStore(tmp_path / "trials.jsonl")
        for i in range(3):
            _write_trial(store, _make_trial(trial=i, score=0.1 * i))

        lines = (tmp_path / "trials.jsonl").read_text(encoding="utf-8").splitlines()
        for line in lines:
            obj = json.loads(line)
            assert isinstance(obj, dict)
            assert "system" in obj
            assert "task_id" in obj
            assert "score" in obj


# ---------------------------------------------------------------------------
# 3. Append multiple trials
# ---------------------------------------------------------------------------


class TestJsonlStoreAppendMultiple:
    def test_append_three_trials_read_all_back(self, tmp_path: Path) -> None:
        store = JsonlAuditStore(tmp_path / "trials.jsonl")
        originals = [
            _make_trial(system="finroot", trial=0, score=0.9),
            _make_trial(system="rag", trial=1, score=0.5),
            _make_trial(system="single_agent", trial=2, score=0.7),
        ]
        for t in originals:
            _write_trial(store, t)

        restored = _read_trials(store)
        assert len(restored) == 3
        for orig, got in zip(originals, restored, strict=True):
            assert got.system == orig.system
            assert got.score == pytest.approx(orig.score)
            assert got.trial == orig.trial

    def test_read_all_returns_empty_for_empty_file(self, tmp_path: Path) -> None:
        store = JsonlAuditStore(tmp_path / "empty.jsonl")
        assert store.read_all() == []

    def test_read_tail_returns_last_n(self, tmp_path: Path) -> None:
        store = JsonlAuditStore(tmp_path / "trials.jsonl")
        for i in range(5):
            _write_trial(store, _make_trial(trial=i, score=float(i)))

        tail = store.read_tail(2)
        assert len(tail) == 2
        assert tail[0]["trial"] == 3
        assert tail[1]["trial"] == 4


# ---------------------------------------------------------------------------
# 4. Missing file
# ---------------------------------------------------------------------------


class TestJsonlStoreMissingFile:
    def test_read_from_nonexistent_file_returns_empty(self, tmp_path: Path) -> None:
        store = JsonlAuditStore(tmp_path / "does_not_exist.jsonl")
        assert store.read_all() == []

    def test_iter_all_from_nonexistent_file_returns_empty(self, tmp_path: Path) -> None:
        store = JsonlAuditStore(tmp_path / "ghost.jsonl")
        assert list(store.iter_all()) == []


# ---------------------------------------------------------------------------
# 5. Corrupt line handling
# ---------------------------------------------------------------------------


class TestJsonlStoreCorruptLine:
    def test_corrupt_line_raises_on_read(self, tmp_path: Path) -> None:
        store_path = tmp_path / "trials.jsonl"
        store = JsonlAuditStore(store_path)
        _write_trial(store, _make_trial(trial=0, score=0.8))

        # Append a corrupt line manually.
        with store_path.open("a", encoding="utf-8") as fh:
            fh.write("NOT VALID JSON\n")

        with pytest.raises(AuditStoreIOError, match="Corrupt JSONL line"):
            store.read_all()

    def test_blank_lines_are_skipped(self, tmp_path: Path) -> None:
        store_path = tmp_path / "trials.jsonl"
        store = JsonlAuditStore(store_path)
        _write_trial(store, _make_trial(trial=0, score=0.8))

        # Inject blank lines between valid entries.
        with store_path.open("a", encoding="utf-8") as fh:
            fh.write("\n\n\n")
        _write_trial(store, _make_trial(trial=1, score=0.6))

        trials = _read_trials(store)
        assert len(trials) == 2
        assert trials[0].trial == 0
        assert trials[1].trial == 1

    def test_trailing_newline_handled(self, tmp_path: Path) -> None:
        store_path = tmp_path / "trials.jsonl"
        store = JsonlAuditStore(store_path)
        _write_trial(store, _make_trial())
        # Add a trailing newline (common in editors).
        with store_path.open("a", encoding="utf-8") as fh:
            fh.write("\n")
        trials = _read_trials(store)
        assert len(trials) == 1


# ---------------------------------------------------------------------------
# 6. Concurrent writes
# ---------------------------------------------------------------------------


class TestJsonlStoreConcurrentWrites:
    def test_concurrent_appends_dont_corrupt(self, tmp_path: Path) -> None:
        store = JsonlAuditStore(tmp_path / "trials.jsonl")
        n_writers = 8
        trials_per_writer = 10
        barrier = threading.Barrier(n_writers)

        def writer(system: str) -> None:
            barrier.wait()
            for i in range(trials_per_writer):
                _write_trial(
                    store,
                    _make_trial(
                        system=system,
                        trial=i,
                        score=round(i / trials_per_writer, 2),
                    ),
                )

        threads = [threading.Thread(target=writer, args=(f"sys-{j}",)) for j in range(n_writers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        trials = _read_trials(store)
        assert len(trials) == n_writers * trials_per_writer

        # Every line must be valid JSON that round-trips through TrialResult.
        for trial in trials:
            assert isinstance(trial, TrialResult)
            assert trial.system.startswith("sys-")
