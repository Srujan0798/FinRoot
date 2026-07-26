"""Audit trail integrity tests.

The audit trail is hash-chained: each event's hash includes the previous
event's hash, so any tampering is detectable. This module locks that
property at the unit level.

Properties verified:
1. append() returns an event with a non-empty hash
2. Each subsequent event's prev_hash matches the previous event's hash
3. verify_chain() returns True after a sequence of appends
4. Tampering with a stored event invalidates the chain (verify_chain → False)
5. Reordered events are detected
"""

from __future__ import annotations

import json
from pathlib import Path

from finroot.audit import AuditTrail


def test_append_returns_hashed_event(tmp_path: Path) -> None:
    audit = AuditTrail(tmp_path / "audit.jsonl")
    e = audit.append("test.event", {"foo": "bar"})
    assert e.hash, "appended event must have a hash"
    # First event's prev_hash is the "zero hash" (64 zeros), not empty
    # string. This is the standard genesis-event convention in hash chains.
    assert e.prev_hash, "first event must have a prev_hash (genesis marker)"


def test_chain_links_correctly(tmp_path: Path) -> None:
    audit = AuditTrail(tmp_path / "audit.jsonl")
    e1 = audit.append("a", {"n": 1})
    e2 = audit.append("b", {"n": 2})
    e3 = audit.append("c", {"n": 3})
    assert e2.prev_hash == e1.hash, f"e2.prev_hash {e2.prev_hash!r} != e1.hash {e1.hash!r}"
    assert e3.prev_hash == e2.hash, f"e3.prev_hash {e3.prev_hash!r} != e2.hash {e2.hash!r}"


def test_verify_chain_clean(tmp_path: Path) -> None:
    audit = AuditTrail(tmp_path / "audit.jsonl")
    for i in range(5):
        audit.append("event", {"i": i})
    assert audit.verify_chain() is True


def test_tampered_event_invalidates_chain(tmp_path: Path) -> None:
    audit = AuditTrail(tmp_path / "audit.jsonl")
    audit.append("a", {"x": 1})
    audit.append("b", {"x": 2})
    audit.append("c", {"x": 3})
    # Tamper: read the file, modify the second event's payload
    log_path = tmp_path / "audit.jsonl"
    lines = log_path.read_text().splitlines()
    assert len(lines) == 3
    second = json.loads(lines[1])
    second["payload"]["x"] = 999  # change the payload
    lines[1] = json.dumps(second)
    log_path.write_text("\n".join(lines) + "\n")
    # Verify should now fail
    assert audit.verify_chain() is False, (
        "Tampering with an event's payload should invalidate the chain"
    )


def test_reordered_events_detected(tmp_path: Path) -> None:
    audit = AuditTrail(tmp_path / "audit.jsonl")
    audit.append("a", {"x": 1})
    audit.append("b", {"x": 2})
    audit.append("c", {"x": 3})
    # Swap events 1 and 2 in the file
    log_path = tmp_path / "audit.jsonl"
    lines = log_path.read_text().splitlines()
    lines[0], lines[1] = lines[1], lines[0]
    log_path.write_text("\n".join(lines) + "\n")
    assert audit.verify_chain() is False, "Reordering events should break the chain"


def test_truncated_chain_detected(tmp_path: Path) -> None:
    """Fixed (HALL_OF_SHAME Pattern 13): verify_chain_detailed() now compares
    the highest seq seen on disk against ``self._last_seq`` (the highest seq
    this in-process instance has appended/loaded). Deleting the tail event(s)
    is otherwise invisible — the remaining events stay internally consistent
    and the read loop just ends early — so this check is the only thing that
    catches it.
    """
    audit = AuditTrail(tmp_path / "audit.jsonl")
    for i in range(5):
        audit.append("e", {"i": i})
    # Truncate the last event from the file
    log_path = tmp_path / "audit.jsonl"
    lines = log_path.read_text().splitlines()
    log_path.write_text("\n".join(lines[:-1]) + "\n")
    result = audit.verify_chain_detailed()
    assert result.ok is False, "Tail truncation must now be detected"
    assert result.broken_seq == 4
    assert "truncation" in result.reason.lower()
