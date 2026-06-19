"""Tests for the hash-chained audit backbone (wave-1, task 03).

Covers:
* Append 3 events → verify_chain returns True.
* Tamper with one event's payload on disk → verify_chain returns False.
* replay(last_n) returns the tail in order.
* Edge cases: genesis hash, empty chain, single event, seq discontinuity.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from finroot.audit import (
    GENESIS_HASH,
    AuditTrail,
    AuditTrailError,
    JsonlAuditStore,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_trail(tmp_path: Path) -> AuditTrail:
    """Create an AuditTrail in a temp directory."""
    return AuditTrail(tmp_path / "audit.jsonl")


def _tamper_payload(path: Path, target_seq: int, new_value: str = "TAMPERED") -> None:
    """Mutate one event's payload on disk to simulate tampering."""
    lines = path.read_text(encoding="utf-8").splitlines()
    tampered_lines: list[str] = []
    for line in lines:
        if not line.strip():
            continue
        event = json.loads(line)
        if event.get("seq") == target_seq:
            event["payload"]["tampered"] = new_value
            tampered_lines.append(json.dumps(event, sort_keys=True, separators=(",", ":")))
        else:
            tampered_lines.append(line)
    path.write_text("\n".join(tampered_lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Core chain tests
# ---------------------------------------------------------------------------

class TestAuditTrailAppend:
    """Test append and basic properties."""

    def test_append_returns_event(self, tmp_path: Path) -> None:
        trail = _make_trail(tmp_path)
        event = trail.append("test.event", {"key": "value"})
        assert event.type == "test.event"
        assert event.payload == {"key": "value"}
        assert event.seq == 0
        assert event.prev_hash == GENESIS_HASH
        assert len(event.hash) == 64

    def test_append_seq_monotonic(self, tmp_path: Path) -> None:
        trail = _make_trail(tmp_path)
        e0 = trail.append("a", {})
        e1 = trail.append("b", {})
        e2 = trail.append("c", {})
        assert e0.seq == 0
        assert e1.seq == 1
        assert e2.seq == 2

    def test_append_chains_prev_hash(self, tmp_path: Path) -> None:
        trail = _make_trail(tmp_path)
        e0 = trail.append("a", {})
        e1 = trail.append("b", {})
        assert e1.prev_hash == e0.hash

    def test_append_rejects_empty_type(self, tmp_path: Path) -> None:
        trail = _make_trail(tmp_path)
        with pytest.raises(AuditTrailError, match="non-empty string"):
            trail.append("", {"x": 1})

    def test_append_rejects_whitespace_type(self, tmp_path: Path) -> None:
        trail = _make_trail(tmp_path)
        with pytest.raises(AuditTrailError, match="non-empty string"):
            trail.append("   ", {"x": 1})

    def test_append_rejects_non_dict_payload(self, tmp_path: Path) -> None:
        trail = _make_trail(tmp_path)
        with pytest.raises(AuditTrailError, match="must be a dict"):
            trail.append("test", "not a dict")  # type: ignore[arg-type]


class TestVerifyChain:
    """Test hash chain verification."""

    def test_empty_chain_verifies_true(self, tmp_path: Path) -> None:
        trail = _make_trail(tmp_path)
        assert trail.verify_chain() is True

    def test_single_event_verifies_true(self, tmp_path: Path) -> None:
        trail = _make_trail(tmp_path)
        trail.append("test", {"a": 1})
        assert trail.verify_chain() is True

    def test_three_events_verify_true(self, tmp_path: Path) -> None:
        trail = _make_trail(tmp_path)
        trail.append("event.one", {"x": 1})
        trail.append("event.two", {"y": 2})
        trail.append("event.three", {"z": 3})
        assert trail.verify_chain() is True

    def test_tamper_detects_broken_chain(self, tmp_path: Path) -> None:
        """The critical tamper-evidence test: mutate payload → verify flips to False."""
        trail = _make_trail(tmp_path)
        trail.append("event.one", {"x": 1})
        trail.append("event.two", {"y": 2})
        trail.append("event.three", {"z": 3})
        # Verify clean chain first
        assert trail.verify_chain() is True
        # Tamper with event at seq=1
        _tamper_payload(trail.path, target_seq=1)
        # Reload trail from disk
        trail2 = AuditTrail(trail.path)
        assert trail2.verify_chain() is False

    def test_verify_detailed_returns_broken_seq(self, tmp_path: Path) -> None:
        trail = _make_trail(tmp_path)
        trail.append("a", {"x": 1})
        trail.append("b", {"y": 2})
        _tamper_payload(trail.path, target_seq=1)
        trail2 = AuditTrail(trail.path)
        result = trail2.verify_chain_detailed()
        assert result.ok is False
        assert result.broken_seq is not None
        assert result.reason is not None

    def test_chain_verification_bool(self, tmp_path: Path) -> None:
        trail = _make_trail(tmp_path)
        trail.append("a", {})
        ok = trail.verify_chain_detailed()
        assert bool(ok) is True


class TestReplay:
    """Test replay returning events in order."""

    def test_replay_all_events(self, tmp_path: Path) -> None:
        trail = _make_trail(tmp_path)
        trail.append("a", {"n": 1})
        trail.append("b", {"n": 2})
        trail.append("c", {"n": 3})
        events = trail.replay()
        assert len(events) == 3
        assert [e.type for e in events] == ["a", "b", "c"]
        assert [e.seq for e in events] == [0, 1, 2]

    def test_replay_last_n(self, tmp_path: Path) -> None:
        trail = _make_trail(tmp_path)
        trail.append("a", {})
        trail.append("b", {})
        trail.append("c", {})
        events = trail.replay(last_n=2)
        assert len(events) == 2
        assert events[0].type == "b"
        assert events[1].type == "c"

    def test_replay_last_n_zero(self, tmp_path: Path) -> None:
        trail = _make_trail(tmp_path)
        trail.append("a", {})
        assert trail.replay(last_n=0) == []

    def test_replay_last_n_larger_than_chain(self, tmp_path: Path) -> None:
        trail = _make_trail(tmp_path)
        trail.append("a", {})
        trail.append("b", {})
        events = trail.replay(last_n=100)
        assert len(events) == 2

    def test_replay_last_n_negative_raises(self, tmp_path: Path) -> None:
        trail = _make_trail(tmp_path)
        with pytest.raises(ValueError, match="non-negative"):
            trail.replay(last_n=-1)

    def test_replay_empty_chain(self, tmp_path: Path) -> None:
        trail = _make_trail(tmp_path)
        assert trail.replay() == []


class TestJsonlStore:
    """Test the underlying JSONL store directly."""

    def test_store_append_read_all(self, tmp_path: Path) -> None:
        store = JsonlAuditStore(tmp_path / "test.jsonl")
        store.append({"a": 1})
        store.append({"b": 2})
        events = store.read_all()
        assert len(events) == 2
        assert events[0]["a"] == 1
        assert events[1]["b"] == 2

    def test_store_read_tail(self, tmp_path: Path) -> None:
        store = JsonlAuditStore(tmp_path / "test.jsonl")
        store.append({"a": 1})
        store.append({"b": 2})
        store.append({"c": 3})
        tail = store.read_tail(2)
        assert len(tail) == 2
        assert tail[0]["b"] == 2
        assert tail[1]["c"] == 3

    def test_store_read_tail_zero(self, tmp_path: Path) -> None:
        store = JsonlAuditStore(tmp_path / "test.jsonl")
        store.append({"a": 1})
        assert store.read_tail(0) == []

    def test_store_read_tail_negative_raises(self, tmp_path: Path) -> None:
        store = JsonlAuditStore(tmp_path / "test.jsonl")
        with pytest.raises(ValueError, match="non-negative"):
            store.read_tail(-1)

    def test_store_exists(self, tmp_path: Path) -> None:
        store = JsonlAuditStore(tmp_path / "test.jsonl")
        assert store.exists() is True

    def test_store_size_bytes(self, tmp_path: Path) -> None:
        store = JsonlAuditStore(tmp_path / "test.jsonl")
        assert store.size_bytes() == 0
        store.append({"a": 1})
        assert store.size_bytes() > 0
