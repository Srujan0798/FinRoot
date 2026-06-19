"""Abstract base for every FinRoot tool.

Provides, by construction:

* TTL cache (``ttl_seconds``, default 300 s)
* Token-bucket rate limiter (``rate_per_sec``, default 5.0)
* Retry with exponential backoff (``max_retries``, default 3;
  ``base_delay``, default 1 s)
* Audit-trail emission on every call (both success and failure)
* **Loud failure**: a failing ``_run`` propagates as
  :class:`ToolCallError` — no synthetic data, no silent fallback.

Subclasses implement :meth:`_run` with their actual logic.
"""

from __future__ import annotations

import hashlib
import logging
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Generic, TypeVar

from finroot.audit.trail import AuditTrail

logger = logging.getLogger(__name__)

In = TypeVar("In")
Out = TypeVar("Out")


class ToolCallError(RuntimeError):
    """A tool call failed after exhausting all retries.

    Never silent (FM-11). The message includes the tool name and the last
    underlying exception so callers can surface actionable errors.
    """


class BaseTool(ABC, Generic[In, Out]):
    """Abstract base for every FinRoot tool.

    Usage::

        class YFinanceTool(BaseTool[str, dict]):
            name = "yfinance"
            def _run(self, inp: str) -> dict:
                ...
    """

    # -- subclass must set these -------------------------------------------
    name: str

    # -- tunables ----------------------------------------------------------
    ttl_seconds: int = 300
    """How long a cached result stays valid, in seconds."""

    rate_per_sec: float = 5.0
    """Maximum sustained call rate (tokens per second)."""

    max_retries: int = 3
    """Number of *additional* attempts after the first failure."""

    base_delay: float = 1.0
    """Initial backoff delay in seconds (doubles each attempt)."""

    def __init__(self, audit: AuditTrail | None = None) -> None:
        self._audit = audit
        self._cache: OrderedDict[str, tuple[float, Out]] = OrderedDict()
        # Token-bucket state
        self._tokens: float = self.rate_per_sec
        self._last_refill: float = time.monotonic()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def __call__(self, inp: In) -> Out:
        """Execute the tool: cache -> rate-limit -> retry loop -> audit.

        Args:
            inp: typed input for the tool.

        Returns:
            Typed output from the tool (possibly from cache).

        Raises:
            ToolCallError: if all retries are exhausted.
        """
        key = self._cache_key(inp)

        # 1. Cache hit within TTL -> return immediately
        cached = self._cache_get(key)
        if cached is not None:
            return cached

        # 2. Rate-limit: wait for a token
        self._consume_token()

        # 3. Execute with retry + exponential backoff
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                result = self._run(inp)
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "Tool %r attempt %d/%d failed: %s",
                    self.name, attempt + 1, self.max_retries + 1, exc,
                )
                if attempt < self.max_retries:
                    time.sleep(self.base_delay * (2**attempt))
                continue

            # 4. Cache & audit on success
            self._cache_set(key, result)
            self._emit_audit("tool.called", inp, result)
            return result

        # All retries exhausted — fail loud (FM-11, FM-09)
        self._emit_audit("tool.failed", inp, last_exc)
        raise ToolCallError(
            f"Tool {self.name!r} failed after {self.max_retries + 1} "
            f"attempt(s): {last_exc}"
        ) from last_exc

    @abstractmethod
    def _run(self, inp: In) -> Out:
        """Subclass implements the actual tool logic.

        Raises on bad input (loud). Never returns synthetic or hallucinated
        financial data (FM-11).
        """

    # ------------------------------------------------------------------
    # Cache internals
    # ------------------------------------------------------------------

    def _cache_key(self, inp: In) -> str:
        raw = str(inp) if inp is not None else "<None>"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _cache_get(self, key: str) -> Out | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        ts, value = entry
        if time.monotonic() - ts <= self.ttl_seconds:
            self._cache.move_to_end(key)
            return value
        del self._cache[key]
        return None

    def _cache_set(self, key: str, value: Out) -> None:
        self._cache[key] = (time.monotonic(), value)

    # ------------------------------------------------------------------
    # Token-bucket rate limiter
    # ------------------------------------------------------------------

    def _consume_token(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.rate_per_sec, self._tokens + elapsed * self.rate_per_sec)
        self._last_refill = now
        if self._tokens < 1.0:
            time.sleep((1.0 - self._tokens) / self.rate_per_sec)
            self._tokens = 0.0
        else:
            self._tokens -= 1.0

    # ------------------------------------------------------------------
    # Audit emission
    # ------------------------------------------------------------------

    def _emit_audit(self, event_type: str, inp: In, result_or_error: object) -> None:
        if self._audit is None:
            return
        try:
            self._audit.append(event_type, {
                "tool": self.name,
                "input": str(inp) if inp is not None else None,
                "output": str(result_or_error)[:500],
            })
        except Exception as exc:
            logger.warning("Audit append failed (non-blocking): %s", exc)


__all__ = ["BaseTool", "ToolCallError"]
