"""Tests for :mod:`finroot.memory.working` (wave-2, task 01).

Covers
------
* Construction validation (max_turns bounds, type, bool guard).
* ``add`` happy path + role/content validation (FM-11).
* Sliding-window behaviour (FIFO drop when buffer full).
* ``get_messages`` returns fresh copies.
* ``clear`` empties the buffer.
* ``to_json`` / ``from_json`` round-trip preserves order and capacity.
* ``from_json`` failure modes (bad JSON, wrong shapes, unknown role).
* Thread safety: concurrent ``add`` calls do not lose messages or
  corrupt the buffer (no torn appends, no over-capacity buffer).
"""

from __future__ import annotations

import json
import threading
from typing import Any

import pytest
from pydantic import ValidationError

from finroot.memory import WorkingMemory
from finroot.memory.working import _ALLOWED_ROLES, _Turn

# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_default_max_turns_is_ten() -> None:
    mem = WorkingMemory()
    assert mem.max_turns == 10
    assert mem.size == 0
    assert mem.get_messages() == []


def test_custom_max_turns_accepted() -> None:
    mem = WorkingMemory(max_turns=3)
    assert mem.max_turns == 3


@pytest.mark.parametrize("bad", [0, -1, -100])
def test_max_turns_must_be_at_least_one(bad: int) -> None:
    with pytest.raises(ValueError, match="max_turns must be >= 1"):
        WorkingMemory(max_turns=bad)


@pytest.mark.parametrize("bad", [1.5, "10", None, [], {}])
def test_max_turns_must_be_int(bad: Any) -> None:
    with pytest.raises(TypeError, match="max_turns must be int"):
        WorkingMemory(max_turns=bad)


def test_max_turns_rejects_bool() -> None:
    """``bool`` is a subclass of ``int``; we must reject it explicitly."""
    with pytest.raises(TypeError, match="max_turns must be int"):
        WorkingMemory(max_turns=True)


# ---------------------------------------------------------------------------
# add / get_messages
# ---------------------------------------------------------------------------


def test_add_and_get_in_insertion_order() -> None:
    mem = WorkingMemory()
    mem.add("user", "hi")
    mem.add("assistant", "hello")
    mem.add("tool", "ping")
    assert mem.get_messages() == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
        {"role": "tool", "content": "ping"},
    ]


def test_empty_string_content_is_allowed() -> None:
    mem = WorkingMemory()
    mem.add("user", "")
    assert mem.get_messages() == [{"role": "user", "content": ""}]


@pytest.mark.parametrize("bad_role", ["system", "User", "ASSISTANT", "", "agent", "human"])
def test_add_rejects_unknown_role(bad_role: str) -> None:
    mem = WorkingMemory()
    with pytest.raises(ValueError, match="role must be one of"):
        mem.add(bad_role, "x")
    assert mem.get_messages() == []  # failed add must not mutate the buffer


def test_add_rejects_non_string_content() -> None:
    mem = WorkingMemory()
    with pytest.raises(TypeError, match="content must be str"):
        mem.add("user", 42)  # type: ignore[arg-type]
    assert mem.get_messages() == []


# ---------------------------------------------------------------------------
# Sliding window
# ---------------------------------------------------------------------------


def test_sliding_window_drops_oldest_turn() -> None:
    mem = WorkingMemory(max_turns=3)
    for i in range(5):
        mem.add("user", f"m{i}")
    msgs = mem.get_messages()
    assert len(msgs) == 3
    assert [m["content"] for m in msgs] == ["m2", "m3", "m4"]


def test_sliding_window_drops_oldest_with_mixed_roles() -> None:
    mem = WorkingMemory(max_turns=2)
    mem.add("user", "a")
    mem.add("assistant", "b")
    mem.add("tool", "c")
    mem.add("user", "d")
    assert mem.get_messages() == [
        {"role": "tool", "content": "c"},
        {"role": "user", "content": "d"},
    ]


def test_sliding_window_with_max_turns_one() -> None:
    mem = WorkingMemory(max_turns=1)
    mem.add("user", "first")
    mem.add("assistant", "second")
    mem.add("tool", "third")
    assert mem.get_messages() == [{"role": "tool", "content": "third"}]


# ---------------------------------------------------------------------------
# get_messages immutability / fresh copy
# ---------------------------------------------------------------------------


def test_get_messages_returns_fresh_list() -> None:
    mem = WorkingMemory()
    mem.add("user", "hi")
    snapshot = mem.get_messages()
    snapshot.clear()
    snapshot.append({"role": "user", "content": "tampered"})
    # the buffer must be unaffected
    assert mem.get_messages() == [{"role": "user", "content": "hi"}]


def test_get_messages_returns_fresh_dicts() -> None:
    mem = WorkingMemory()
    mem.add("user", "hi")
    snapshot = mem.get_messages()
    snapshot[0]["content"] = "tampered"
    snapshot[0]["role"] = "tool"
    assert mem.get_messages() == [{"role": "user", "content": "hi"}]


# ---------------------------------------------------------------------------
# clear
# ---------------------------------------------------------------------------


def test_clear_empties_buffer() -> None:
    mem = WorkingMemory()
    mem.add("user", "a")
    mem.add("assistant", "b")
    assert mem.size == 2
    mem.clear()
    assert mem.size == 0
    assert mem.get_messages() == []


def test_clear_on_empty_buffer_is_noop() -> None:
    mem = WorkingMemory()
    mem.clear()
    assert mem.get_messages() == []


def test_buffer_reusable_after_clear() -> None:
    mem = WorkingMemory(max_turns=2)
    mem.add("user", "a")
    mem.add("assistant", "b")
    mem.clear()
    mem.add("tool", "c")
    assert mem.get_messages() == [{"role": "tool", "content": "c"}]


# ---------------------------------------------------------------------------
# to_json / from_json round-trip
# ---------------------------------------------------------------------------


def test_to_json_round_trip_preserves_order_and_capacity() -> None:
    mem = WorkingMemory(max_turns=7)
    for role, content in [
        ("user", "hi"),
        ("assistant", "hello"),
        ("tool", '{"k": 1}'),
        ("user", "thanks"),
    ]:
        mem.add(role, content)
    blob = mem.to_json()
    restored = WorkingMemory.from_json(blob)
    assert restored.max_turns == 7
    assert restored.get_messages() == mem.get_messages()


def test_to_json_round_trip_on_empty_buffer() -> None:
    mem = WorkingMemory(max_turns=4)
    blob = mem.to_json()
    restored = WorkingMemory.from_json(blob)
    assert restored.max_turns == 4
    assert restored.get_messages() == []


def test_to_json_round_trip_after_sliding_window_dropped_turns() -> None:
    """Round-trip must reflect the *current* buffer, not the original history."""
    mem = WorkingMemory(max_turns=2)
    for i in range(5):
        mem.add("user", f"m{i}")
    restored = WorkingMemory.from_json(mem.to_json())
    assert restored.max_turns == 2
    assert [m["content"] for m in restored.get_messages()] == ["m3", "m4"]


def test_to_json_is_valid_json() -> None:
    mem = WorkingMemory(max_turns=2)
    mem.add("user", "hello")
    payload = json.loads(mem.to_json())
    assert payload == {
        "max_turns": 2,
        "turns": [{"role": "user", "content": "hello"}],
    }


def test_to_json_preserves_unicode() -> None:
    mem = WorkingMemory()
    mem.add("user", "namaste 🙏 ₹")
    restored = WorkingMemory.from_json(mem.to_json())
    assert restored.get_messages()[0]["content"] == "namaste 🙏 ₹"


# ---------------------------------------------------------------------------
# from_json failure modes (FM-11: fail loud)
# ---------------------------------------------------------------------------


def test_from_json_rejects_non_string_input() -> None:
    with pytest.raises(TypeError, match="data must be str"):
        WorkingMemory.from_json(b'{"max_turns": 1, "turns": []}')  # type: ignore[arg-type]


def test_from_json_rejects_invalid_json() -> None:
    with pytest.raises(ValueError, match="invalid JSON"):
        WorkingMemory.from_json("{not json")


def test_from_json_rejects_non_object_payload() -> None:
    with pytest.raises(ValueError, match="payload must be a JSON object"):
        WorkingMemory.from_json(json.dumps([1, 2, 3]))


def test_from_json_rejects_missing_keys() -> None:
    with pytest.raises(ValueError, match="must contain 'max_turns' and 'turns' keys"):
        WorkingMemory.from_json(json.dumps({"max_turns": 3}))


def test_from_json_rejects_non_list_turns() -> None:
    with pytest.raises(ValueError, match="'turns' must be a list"):
        WorkingMemory.from_json(json.dumps({"max_turns": 3, "turns": "nope"}))


def test_from_json_rejects_turn_without_role() -> None:
    blob = json.dumps({"max_turns": 3, "turns": [{"content": "x"}]})
    with pytest.raises(ValueError, match="must have 'role' and 'content' keys"):
        WorkingMemory.from_json(blob)


def test_from_json_rejects_unknown_role() -> None:
    blob = json.dumps(
        {"max_turns": 3, "turns": [{"role": "system", "content": "x"}]}
    )
    with pytest.raises(ValueError, match="role must be one of"):
        WorkingMemory.from_json(blob)


def test_from_json_rejects_non_dict_turn() -> None:
    blob = json.dumps({"max_turns": 3, "turns": ["nope"]})
    with pytest.raises(ValueError, match="turn at index 0 must be a dict"):
        WorkingMemory.from_json(blob)


def test_from_json_rejects_bad_max_turns_in_payload() -> None:
    """``from_json`` propagates the ``__init__`` validation for max_turns."""
    blob = json.dumps({"max_turns": 0, "turns": []})
    with pytest.raises(ValueError, match="max_turns must be >= 1"):
        WorkingMemory.from_json(blob)


# ---------------------------------------------------------------------------
# Internal model sanity (catches silent contract drift in _Turn)
# ---------------------------------------------------------------------------


def test_internal_turn_is_frozen() -> None:
    t = _Turn(role="user", content="x")
    with pytest.raises(ValidationError):
        t.role = "tool"  # type: ignore[misc]


def test_internal_turn_rejects_unknown_role() -> None:
    with pytest.raises(ValidationError):
        _Turn(role="system", content="x")  # type: ignore[arg-type]


def test_allowed_roles_constant() -> None:
    assert set(_ALLOWED_ROLES) == {"user", "assistant", "tool"}


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------


def test_concurrent_adds_do_not_lose_messages_within_capacity() -> None:
    """With 8 threads × 50 adds = 400 messages into a buffer of size 1000,
    the buffer must end with exactly 400 messages in *some* valid order.
    """
    mem = WorkingMemory(max_turns=1000)
    threads: list[threading.Thread] = []
    barrier = threading.Barrier(8)

    def worker(tid: int) -> None:
        barrier.wait()  # release all threads at the same instant
        for i in range(50):
            mem.add("user", f"t{tid}-i{i}")

    for tid in range(8):
        t = threading.Thread(target=worker, args=(tid,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    msgs = mem.get_messages()
    assert len(msgs) == 400
    # every message must be one of the 8*50 produced — none invented, none lost
    produced = {f"t{tid}-i{i}" for tid in range(8) for i in range(50)}
    assert {m["content"] for m in msgs} == produced


def test_concurrent_adds_respect_max_turns() -> None:
    """With 4 threads × 100 adds = 400 messages into a buffer of size 50,
    the buffer must end at exactly 50 messages and the lock must keep
    the deque from ever exceeding ``max_turns``.
    """
    mem = WorkingMemory(max_turns=50)
    barrier = threading.Barrier(4)

    def worker(tid: int) -> None:
        barrier.wait()
        for i in range(100):
            mem.add("user", f"t{tid}-i{i}")
            assert mem.size <= 50  # lock + deque maxlen ⇒ invariant holds

    threads = [
        threading.Thread(target=worker, args=(tid,)) for tid in range(4)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert mem.size == 50


def test_concurrent_reads_during_writes_never_observe_torn_state() -> None:
    """While writers are appending, readers must never see a buffer that
    violates the ``role ∈ allowed`` invariant (no half-appended turn).
    """
    mem = WorkingMemory(max_turns=500)
    stop = threading.Event()
    errors: list[str] = []
    lock = threading.Lock()

    def writer() -> None:
        i = 0
        while not stop.is_set():
            role = ("user", "assistant", "tool")[i % 3]
            mem.add(role, f"m{i}")
            i += 1

    def reader() -> None:
        for _ in range(200):
            for m in mem.get_messages():
                if m["role"] not in _ALLOWED_ROLES:
                    with lock:
                        errors.append(f"torn role: {m!r}")
                if not isinstance(m["content"], str):
                    with lock:
                        errors.append(f"torn content: {m!r}")

    writers = [threading.Thread(target=writer) for _ in range(2)]
    readers = [threading.Thread(target=reader) for _ in range(2)]
    for t in writers + readers:
        t.start()
    for t in readers:
        t.join()  # readers finish their 200-iter loop quickly
    stop.set()  # now tell writers to stop
    for t in writers:
        t.join()

    assert errors == []
