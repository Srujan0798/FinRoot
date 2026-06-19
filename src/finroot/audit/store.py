"""Append-only JSONL store for the audit backbone.

The store is a deliberately small layer. It does **no** hashing and **no**
schema interpretation — it just persists already-built event dicts to disk,
one per line, and reads them back in order. The tamper-evidence hash chain
lives in :mod:`finroot.audit.trail`; the store's job is to be a boring,
reliable, append-only transport.

Design rules
------------
* **Append-only.** There is no public ``delete`` / ``truncate`` / ``update``.
  Once a line is on disk, it stays. ``AuditTrail`` never re-writes past
  events either (FM-11: never silently repair a broken chain).
* **One event per line, no trailing commas.** Standard JSONL: each line is a
  complete JSON object terminated by ``\n``. Blank lines are skipped on
  read.
* **UTF-8, no BOM.** Stable across platforms.
* **Thread-safe within a process.** A :class:`threading.Lock` guards
  concurrent appends from the same interpreter. Cross-process appends are
  out of scope for now (single-writer assumption is the safest tamper-
  evidence model).
* **Canonical-on-read, not canonical-on-write.** We accept whatever dict the
  caller hands us (the trail's responsibility) and persist it via
  :func:`json.dumps` with ``sort_keys=True`` and ``("," , ":")`` separators
  so the on-disk bytes are stable for the trail's :meth:`AuditTrail.verify_chain`
  recomputation.

This module owns no shared state outside the file itself. The
:class:`JsonlAuditStore` can be created freely; two instances pointing at
the same path will append into the same file (the second writer's open
should not truncate).
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from pathlib import Path


# We use a small `default` that handles datetimes and other primitives the
# trail may pass through. Keep it conservative: if a value isn't representable
# we want the append to fail loud (FM-11), not silently coerce.
def _json_default(obj: object) -> object:  # pragma: no cover - exercised via trail
    from datetime import date, datetime
    from decimal import Decimal

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(
        f"Object of type {type(obj).__name__} is not JSON-serializable for the audit store"
    )


# Canonical JSON encoder options (see G-0c in docs/waves/wave-1-gotchas.md).
# These are the *only* place in the audit pipeline where disk bytes meet the
# hash domain, so keep the knobs here.
_JSON_KW: dict[str, object] = {
    "sort_keys": True,
    "separators": (",", ":"),
    "ensure_ascii": False,
    "default": _json_default,
}

# Genesis prev_hash for the first event in a chain. SHA-256 in hex is 64 chars.
GENESIS_PREV_HASH = "0" * 64


class AuditStoreError(RuntimeError):
    """Base class for store errors (FM-11: fail loud, typed)."""


class AuditStoreIOError(AuditStoreError):
    """Wraps a low-level I/O failure (corrupt line, unreadable file, etc.)."""


class JsonlAuditStore:
    """Append-only JSONL store keyed on a single file path.

    The path's parent directory is created on first write. Reads are
    line-based and streaming-friendly; the store loads the file once per
    ``iter_all`` / ``read_tail`` call (the trail is the only realistic
    caller and it batches reads).
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._lock = threading.Lock()
        # Create parent dir eagerly so append doesn't race with directory
        # creation in concurrent tests.
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # Touch the file so `exists()` is meaningful before the first write.
        if not self._path.exists():
            self._path.touch(mode=0o644)

    # ------------------------------------------------------------------ write

    def append(self, event: dict) -> None:
        """Atomically append ``event`` as one JSONL line.

        Raises:
            AuditStoreIOError: if the line cannot be encoded or written.
        """
        try:
            line = json.dumps(event, **_JSON_KW)
        except (TypeError, ValueError) as e:
            raise AuditStoreIOError(
                f"Failed to JSON-encode audit event for {self._path}: {e}"
            ) from e
        payload = (line + "\n").encode("utf-8")
        with self._lock, self._path.open("ab") as fh:
            fh.write(payload)
            fh.flush()

    # ------------------------------------------------------------------- read

    def iter_all(self) -> Iterator[dict]:
        """Yield every event in insertion order.

        Blank lines and lines that fail to parse raise :class:`AuditStoreIOError`
        — we do not silently skip corruption, because the trail's
        :meth:`verify_chain` is the integrity boundary and it needs the
        raw bytes to be either valid JSON or an explicit failure.
        """
        if not self._path.exists() or self._path.stat().st_size == 0:
            return
        with self._path.open("r", encoding="utf-8") as fh:
            for lineno, raw in enumerate(fh, start=1):
                stripped = raw.strip()
                if not stripped:
                    continue
                try:
                    yield json.loads(stripped)
                except json.JSONDecodeError as e:
                    raise AuditStoreIOError(
                        f"Corrupt JSONL line {lineno} in {self._path}: {e}"
                    ) from e

    def read_all(self) -> list[dict]:
        """Eagerly read every event. Convenience wrapper around :meth:`iter_all`."""
        return list(self.iter_all())

    def read_tail(self, n: int) -> list[dict]:
        """Return the last ``n`` events in insertion order.

        If ``n`` exceeds the file length, returns all events. ``n`` must be
        non-negative; ``0`` returns an empty list.
        """
        if n < 0:
            raise ValueError(f"n must be non-negative, got {n}")
        if n == 0:
            return []
        # Memory-cheap tail: stream and keep a bounded deque.
        from collections import deque

        tail: deque[dict] = deque(maxlen=n)
        for event in self.iter_all():
            tail.append(event)
        return list(tail)

    # ------------------------------------------------------------------ utils

    @property
    def path(self) -> Path:
        """Absolute or relative path of the underlying JSONL file."""
        return self._path

    def exists(self) -> bool:
        """Whether the backing file exists (always true after construction)."""
        return self._path.exists()

    def size_bytes(self) -> int:
        """Size of the file in bytes; ``0`` if missing."""
        if not self._path.exists():
            return 0
        return self._path.stat().st_size


__all__ = [
    "AuditStoreError",
    "AuditStoreIOError",
    "GENESIS_PREV_HASH",
    "JsonlAuditStore",
]
