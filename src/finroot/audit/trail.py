"""Hash-chained audit trail — the tamper-evident backbone.

The :class:`AuditTrail` is the only thing in the system that decides what
"an audit event" is on disk. It composes:

* the :class:`~finroot.schemas.audit.AuditEvent` Pydantic model (shape, owned by task 02),
* a :class:`~finroot.audit.store.JsonlAuditStore` (transport, owned by this module),
* the canonical-JSON + SHA-256 hash chain (logic, owned by this module).

Hash construction (frozen by the contract)
------------------------------------------
For event :math:`E_i`::

    canonical_payload_i = json.dumps(payload_i, sort_keys=True, separators=(",", ":"))
    hash_i = sha256_hex(prev_hash_i || canonical_payload_i || ts_iso_i || str(seq_i))

with ``prev_hash_0 = "0" * 64`` (the genesis sentinel). The concatenation
order is the contract — do not change it (would break every existing
chain). The on-disk JSONL file is append-only and one event per line;
old events are never rewritten.

The :class:`AuditTrail` instance itself is single-writer and process-
local. It re-validates the entire chain on every :meth:`verify_chain`
call (cheap up to tens of thousands of events; for longer chains we can
add a streaming verifier later). The :meth:`replay` method returns the
most recent events in insertion order — exactly the data the rest of the
agent (critic, UI audit tab, replay harness) needs.
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from finroot.audit.store import GENESIS_PREV_HASH, JsonlAuditStore
from finroot.schemas.audit import AuditEvent

# Re-export the genesis sentinel so callers don't need to reach into ``store``
# (which would also be fine, but the trail is the public surface).
GENESIS_HASH = GENESIS_PREV_HASH

# Canonical JSON for hash computation: must match G-0c in
# docs/waves/wave-1-gotchas.md. We deliberately do NOT use the store's
# encoder here so that hash inputs are independent of any future changes
# to the on-disk format. Today they happen to be identical; the indirection
# keeps the contract explicit.
_HASH_JSON_KW: dict[str, Any] = {
    "sort_keys": True,
    "separators": (",", ":"),
    "ensure_ascii": False,
}


class AuditTrailError(RuntimeError):
    """Base class for audit-trail errors (FM-11: typed failure)."""


class AuditChainBroken(AuditTrailError):
    """The chain failed :meth:`AuditTrail.verify_chain`.

    Carries the seq number of the first broken event (or ``None`` if the
    failure was a file/parse error) so callers can build human-readable
    reports without re-scanning the log.
    """

    def __init__(self, broken_seq: int | None, reason: str) -> None:
        super().__init__(f"audit chain broken at seq={broken_seq}: {reason}")
        self.broken_seq = broken_seq
        self.reason = reason


class ChainVerification:
    """Structured result of :meth:`AuditTrail.verify_chain_detailed`.

    The simple :meth:`AuditTrail.verify_chain` is a thin wrapper that
    returns ``result.ok`` so the contract interface stays ``-> bool``.
    """

    __slots__ = ("ok", "broken_seq", "reason", "checked")

    def __init__(
        self,
        ok: bool,
        broken_seq: int | None = None,
        reason: str | None = None,
        checked: int = 0,
    ) -> None:
        self.ok = ok
        self.broken_seq = broken_seq
        self.reason = reason
        self.checked = checked

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return (
            f"ChainVerification(ok={self.ok!r}, broken_seq={self.broken_seq!r}, "
            f"reason={self.reason!r}, checked={self.checked})"
        )

    def __bool__(self) -> bool:  # makes `if result: ...` work
        return self.ok


def _canonical_payload(payload: Mapping[str, Any]) -> str:
    """Return the canonical-JSON string used as the hash input for a payload.

    Sort keys, compact separators, UTF-8 (no ``\\uXXXX`` escaping for non-ASCII
    characters). The output is byte-stable across processes and platforms, which
    is the entire point of canonicalization (G-0c).
    """
    try:
        return json.dumps(dict(payload), **_HASH_JSON_KW)
    except (TypeError, ValueError) as e:
        raise AuditTrailError(
            f"audit payload is not JSON-serializable in canonical form: {e}"
        ) from e


def _compute_hash(prev_hash: str, canonical_payload: str, ts: datetime, seq: int) -> str:
    """Compute ``sha256_hex(prev_hash || canonical_payload || ts_iso || seq)``."""
    # ``prev_hash`` is already hex-normalized to lowercase by AuditEvent's
    # validator; we still pass it through ``.lower()`` defensively in case a
    # caller constructs a chain manually.
    material = (
        prev_hash.lower()
        + canonical_payload
        + ts.isoformat()
        + str(seq)
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


class AuditTrail:
    """Append-only, hash-chained audit log backed by a JSONL file.

    Example
    -------
    >>> from pathlib import Path
    >>> trail = AuditTrail(Path("/tmp/audit.jsonl"))
    >>> e1 = trail.append("task.dispatched", {"task": "01"})
    >>> e2 = trail.append("tool.called", {"tool": "yfinance", "ticker": "AAPL"})
    >>> trail.verify_chain()
    True
    >>> len(trail.replay())
    2
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._store = JsonlAuditStore(self._path)
        self._lock = threading.Lock()
        # Cache the head of the chain so append is O(1). On construction we
        # read once; subsequent appends update the cache in-memory. We do
        # *not* re-verify here — the trail is open, and verify_chain is the
        # explicit integrity check the caller asks for.
        self._last_seq: int = -1
        self._last_hash: str = GENESIS_HASH
        self._head_loaded: bool = False

    # ----------------------------------------------------------------- basics

    @property
    def path(self) -> Path:
        """Path of the underlying JSONL file."""
        return self._path

    @property
    def store(self) -> JsonlAuditStore:
        """Underlying JSONL store (exposed for tests and admin tools)."""
        return self._store

    def __len__(self) -> int:
        """Number of events currently in the chain (``O(n)``; iterates the file)."""
        return self.chain_length

    @property
    def chain_length(self) -> int:
        """Number of events currently in the chain (``O(n)``)."""
        return sum(1 for _ in self._store.iter_all())

    def _ensure_head(self) -> None:
        """Load the chain head from disk into the in-memory cache.

        Idempotent. Called from :meth:`append` (and from any other reader
        that needs the head without paying the cost twice). The cache is
        the trail's private optimization; on-disk bytes are the truth.
        """
        if self._head_loaded:
            return
        last_event: AuditEvent | None = None
        # We could track size and tail, but for a foundation trail the
        # simplest correct path is one full scan on first append. The file
        # is small in practice (tens of events per session, not millions).
        for raw in self._store.iter_all():
            try:
                event = AuditEvent.model_validate(raw)
            except ValidationError as e:
                raise AuditTrailError(
                    f"audit file {self._path} contains a malformed event: {e}"
                ) from e
            last_event = event
        if last_event is not None:
            self._last_seq = last_event.seq
            self._last_hash = last_event.hash
        self._head_loaded = True

    # ------------------------------------------------------------------ append

    def append(self, type: str, payload: dict) -> AuditEvent:
        """Append one event to the chain and return it.

        Args:
            type: stable event-type identifier (e.g. ``"tool.called"``).
            payload: JSON-serializable dict. Will be canonicalized for hashing.

        Returns:
            The persisted :class:`~finroot.schemas.audit.AuditEvent`.

        Raises:
            AuditTrailError: on type/payload validation failure or a serialization
                problem. A failed append does **not** partially write — either the
                event is fully on disk and in the chain, or nothing changed.
        """
        if not isinstance(type, str) or not type or not type.strip():
            raise AuditTrailError("audit event type must be a non-empty string")
        if not isinstance(payload, dict):
            raise AuditTrailError(
                f"audit event payload must be a dict, got {payload.__class__.__name__}"
            )

        canonical = _canonical_payload(payload)
        with self._lock:
            self._ensure_head()
            ts = datetime.now(UTC)
            seq = self._last_seq + 1
            prev_hash = self._last_hash
            digest = _compute_hash(prev_hash, canonical, ts, seq)

            event = AuditEvent(
                ts=ts,
                seq=seq,
                type=type.strip(),
                payload=dict(payload),
                prev_hash=prev_hash,
                hash=digest,
            )

            # Persist AFTER constructing the event so Pydantic validates the
            # full shape (hash length, hex check, etc.) before we touch disk.
            # If model construction raises, nothing is written; if the store
            # raises, the in-memory head hasn't been advanced.
            self._store.append(event.model_dump(mode="json"))
            self._last_seq = seq
            self._last_hash = digest
            return event

    # ---------------------------------------------------------------- verify

    def verify_chain(self) -> bool:
        """Recompute and validate the entire hash chain.

        Returns:
            ``True`` iff every event's stored hash matches a fresh
            recomputation and each event's ``prev_hash`` matches the
            previous event's ``hash``. ``False`` on the first mismatch.

        This is the integrity boundary of the system. It is **never**
        silent: callers that want the *which seq broke* detail should use
        :meth:`verify_chain_detailed` or read :attr:`last_verification`.
        """
        return self.verify_chain_detailed().ok

    def verify_chain_detailed(self) -> ChainVerification:
        """Like :meth:`verify_chain` but returns the seq number and reason
        of the first broken event (or a parse / IO error).

        Use this for the UI audit tab, the smoke test, and the eval harness.
        """
        prev_hash = GENESIS_HASH
        expected_seq = 0
        checked = 0

        try:
            events = self._store.read_all()
        except Exception as e:  # JsonlStore error → wrap
            result = ChainVerification(
                ok=False, broken_seq=None, reason=f"store read failed: {e}", checked=0
            )
            self._last_verification = result
            return result

        for raw in events:
            try:
                event = AuditEvent.model_validate(raw)
            except ValidationError as e:
                result = ChainVerification(
                    ok=False,
                    broken_seq=expected_seq,
                    reason=f"event at expected seq={expected_seq} failed schema validation: {e}",
                    checked=checked,
                )
                self._last_verification = result
                return result

            # 1) sequencing — defends against insertions / deletions
            if event.seq != expected_seq:
                result = ChainVerification(
                    ok=False,
                    broken_seq=event.seq,
                    reason=(
                        f"seq discontinuity: expected {expected_seq}, "
                        f"found {event.seq} (possible insertion or deletion)"
                    ),
                    checked=checked,
                )
                self._last_verification = result
                return result

            # 2) prev_hash linkage — the chain link itself
            if event.prev_hash.lower() != prev_hash.lower():
                result = ChainVerification(
                    ok=False,
                    broken_seq=event.seq,
                    reason=(
                        f"prev_hash mismatch at seq={event.seq}: "
                        f"expected {prev_hash[:12]}..., got {event.prev_hash[:12]}..."
                    ),
                    checked=checked,
                )
                self._last_verification = result
                return result

            # 3) recompute the hash and compare to the stored value — the
            # actual tamper-evidence check.
            try:
                canonical = _canonical_payload(event.payload)
            except AuditTrailError as e:
                result = ChainVerification(
                    ok=False,
                    broken_seq=event.seq,
                    reason=f"payload at seq={event.seq} not canonicalizable: {e}",
                    checked=checked,
                )
                self._last_verification = result
                return result

            recomputed = _compute_hash(event.prev_hash, canonical, event.ts, event.seq)
            if recomputed != event.hash.lower():
                result = ChainVerification(
                    ok=False,
                    broken_seq=event.seq,
                    reason=(
                        f"hash mismatch at seq={event.seq}: "
                        f"stored {event.hash[:12]}... != recomputed {recomputed[:12]}..."
                    ),
                    checked=checked,
                )
                self._last_verification = result
                return result

            prev_hash = event.hash
            expected_seq += 1  # noqa: SIM113 — used for seq validation, not index
            checked += 1

        result = ChainVerification(ok=True, checked=checked)
        self._last_verification = result
        return result

    @property
    def last_verification(self) -> ChainVerification | None:
        """Result of the most recent :meth:`verify_chain_detailed` call, or
        ``None`` if verification has not been run yet in this process."""
        return getattr(self, "_last_verification", None)

    # ------------------------------------------------------------------ replay

    def replay(self, last_n: int | None = None) -> list[AuditEvent]:
        """Return the most recent events in insertion order.

        Args:
            last_n: number of events to return from the tail. ``None`` (the
                default) returns the entire chain. ``0`` returns ``[]``.

        Returns:
            A list of :class:`~finroot.schemas.audit.AuditEvent` ordered by ``seq``
            ascending. Malformed lines raise :class:`AuditTrailError` — the
            audit pipeline never silently drops data (FM-11).
        """
        if last_n is not None and last_n < 0:
            raise ValueError(f"last_n must be non-negative or None, got {last_n}")
        raw_events = (
            self._store.read_tail(last_n) if last_n is not None else self._store.read_all()
        )
        events: list[AuditEvent] = []
        for raw in raw_events:
            try:
                events.append(AuditEvent.model_validate(raw))
            except ValidationError as e:
                raise AuditTrailError(
                    f"audit file {self._path} contains a malformed event: {e}"
                ) from e
        return events


__all__ = [
    "AuditChainBroken",
    "AuditTrail",
    "AuditTrailError",
    "ChainVerification",
    "GENESIS_HASH",
]
