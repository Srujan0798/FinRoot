"""Hash-chained audit backbone for FinRoot.

Public surface
--------------
* :class:`AuditTrail` — the append/verify/replay API (see :mod:`.trail`).
* :class:`ChainVerification` — structured verify result.
* :class:`AuditTrailError` and :class:`AuditChainBroken` — typed failure modes.
* :data:`GENESIS_HASH` — the prev_hash sentinel for the first event in a chain.
* :class:`JsonlAuditStore` — the underlying JSONL transport (exposed for tests
  and admin tools; the trail is the recommended user-facing surface).

Everything else in :mod:`finroot.audit` is implementation detail.
"""

from __future__ import annotations

from finroot.audit.store import (
    GENESIS_PREV_HASH,
    AuditStoreError,
    AuditStoreIOError,
    JsonlAuditStore,
)
from finroot.audit.trail import (
    GENESIS_HASH,
    AuditChainBroken,
    AuditTrail,
    AuditTrailError,
    ChainVerification,
)

__all__ = [
    "AuditChainBroken",
    "AuditStoreError",
    "AuditStoreIOError",
    "AuditTrail",
    "AuditTrailError",
    "ChainVerification",
    "GENESIS_HASH",
    "GENESIS_PREV_HASH",
    "JsonlAuditStore",
]
