"""WorkingMemory — sliding-window conversation buffer.

This module is the Tier-2 wave-2 task 01 deliverable. It owns *one* concern:
keep the last ``max_turns`` turns of a conversation (user / assistant / tool)
in insertion order, safely, in a form that the rest of the system (MemoryManager
in task 04) can serialise and hand to a LangChain prompt.

Contract reference
------------------
``.specify/specs/wave-2/contracts/memory.contract.md`` § WorkingMemory.

Design notes
------------
* The buffer is a :class:`collections.deque` with ``maxlen=max_turns`` so
  the sliding-window behaviour is delegated to the stdlib (atomic, O(1)).
* A :class:`threading.Lock` guards every public method. The deque is atomic
  per-operation, but the *sequence* ``validate -> append`` is not — the
  lock makes ``add()`` an all-or-nothing operation, which is what the
  contract requires for thread safety.
* The internal turn model is a frozen Pydantic ``BaseModel`` so the buffer
  can never be mutated in place and every field has a static type. The
  *public* API still returns ``list[dict[str, str]]`` per the contract —
  the ``_Turn`` model is an implementation detail.
* ``to_json`` / ``from_json`` is a true round-trip: ``max_turns`` and turn
  order are preserved. ``from_json`` is *strict* — invalid input raises
  ``ValueError`` (FM-11: fail loud, no silent recovery).
"""

from __future__ import annotations

import json
import threading
from collections import deque
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field

Role = Literal["user", "assistant", "tool"]
_ALLOWED_ROLES: Final[frozenset[str]] = frozenset({"user", "assistant", "tool"})


class _Turn(BaseModel):
    """Internal, immutable representation of one conversation turn.

    Public consumers receive plain ``{"role": ..., "content": ...}`` dicts
    from :meth:`WorkingMemory.get_messages`; this model exists so the
    buffer stores typed values and the Pydantic v2 validation gates the
    role/content at the boundary.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    role: Role
    content: str = Field(min_length=0)


class WorkingMemory:
    """Sliding-window conversation buffer. Thread-safe, JSON-serialisable.

    Parameters
    ----------
    max_turns:
        Maximum number of turns to retain. Must be ``>= 1``. Older turns
        are silently dropped (FIFO) once the buffer is full.

    Raises
    ------
    TypeError
        If ``max_turns`` is not an ``int`` (and not a ``bool``, which is
        a subclass of ``int`` in Python but never a sensible size).
    ValueError
        If ``max_turns`` is less than 1.

    Notes
    -----
    The instance is *not* a context manager and does not own any external
    resources; it is safe to construct inline, pass by value, and discard.
    All public methods are safe to call from multiple threads concurrently.
    """

    def __init__(self, max_turns: int = 10) -> None:
        if isinstance(max_turns, bool) or not isinstance(max_turns, int):
            raise TypeError(
                f"max_turns must be int, got {type(max_turns).__name__}"
            )
        if max_turns < 1:
            raise ValueError(f"max_turns must be >= 1, got {max_turns}")
        self._max_turns: int = max_turns
        self._buffer: deque[_Turn] = deque(maxlen=max_turns)
        self._lock: threading.Lock = threading.Lock()

    @property
    def max_turns(self) -> int:
        """Configured maximum buffer size (read-only)."""
        return self._max_turns

    @property
    def size(self) -> int:
        """Current number of turns in the buffer."""
        with self._lock:
            return len(self._buffer)

    def add(self, role: str, content: str) -> None:
        """Append one turn to the buffer.

        If the buffer is already at ``max_turns``, the oldest turn is
        dropped (FIFO sliding window). The ``validate -> append`` pair
        is atomic under the instance lock so a concurrent reader never
        observes an in-flight invalid state.

        Parameters
        ----------
        role:
            ``"user"``, ``"assistant"``, or ``"tool"`` (case-sensitive).
        content:
            Free-form text. Must be a ``str``; empty string is allowed.

        Raises
        ------
        ValueError
            If ``role`` is not one of the three allowed values (FM-11).
        TypeError
            If ``content`` is not a ``str``.
        """
        if not isinstance(content, str):
            raise TypeError(
                f"content must be str, got {type(content).__name__}"
            )
        with self._lock:
            if role not in _ALLOWED_ROLES:
                raise ValueError(
                    f"role must be one of {sorted(_ALLOWED_ROLES)}, got {role!r}"
                )
            self._buffer.append(_Turn(role=role, content=content))

    def get_messages(self) -> list[dict[str, str]]:
        """Return a copy of the buffer in insertion order.

        The returned list is a fresh ``list`` of fresh ``dict`` objects,
        so callers may mutate it freely without affecting the buffer.
        """
        with self._lock:
            return [{"role": t.role, "content": t.content} for t in self._buffer]

    def clear(self) -> None:
        """Remove all turns from the buffer."""
        with self._lock:
            self._buffer.clear()

    def to_json(self) -> str:
        """Serialise the buffer to a compact UTF-8-safe JSON string.

        The payload contains both ``max_turns`` and the ordered ``turns``
        list, so :meth:`from_json` is a true round-trip (capacity and
        order are preserved).
        """
        with self._lock:
            payload = {
                "max_turns": self._max_turns,
                "turns": [
                    {"role": t.role, "content": t.content} for t in self._buffer
                ],
            }
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def from_json(cls, data: str) -> WorkingMemory:
        """Restore a :class:`WorkingMemory` from a JSON string.

        Parameters
        ----------
        data:
            The string previously produced by :meth:`to_json`.

        Returns
        -------
        WorkingMemory
            A new instance with the same ``max_turns`` and turn order
            as the source.

        Raises
        ------
        TypeError
            If ``data`` is not a ``str``.
        ValueError
            If ``data`` is not valid JSON, is not a JSON object, or
            contains a structurally invalid buffer (wrong types, unknown
            role, non-list turns). This is FM-11: fail loud, never
            silently coerce.
        """
        if not isinstance(data, str):
            raise TypeError(f"data must be str, got {type(data).__name__}")
        try:
            payload = json.loads(data)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON: {exc.msg}") from exc
        if not isinstance(payload, dict):
            raise ValueError(
                f"payload must be a JSON object, got {type(payload).__name__}"
            )
        if "max_turns" not in payload or "turns" not in payload:
            raise ValueError(
                "payload must contain 'max_turns' and 'turns' keys"
            )
        max_turns = payload["max_turns"]
        turns = payload["turns"]
        if not isinstance(turns, list):
            raise ValueError(
                f"'turns' must be a list, got {type(turns).__name__}"
            )
        mem = cls(max_turns=max_turns)
        for i, turn in enumerate(turns):
            if not isinstance(turn, dict):
                raise ValueError(
                    f"turn at index {i} must be a dict, got {type(turn).__name__}"
                )
            if "role" not in turn or "content" not in turn:
                raise ValueError(
                    f"turn at index {i} must have 'role' and 'content' keys"
                )
            mem.add(turn["role"], turn["content"])
        return mem


__all__ = ["WorkingMemory", "Role"]
