"""Distributed tracing for FinRoot pipeline — OpenTelemetry-style spans.

Lightweight tracing that works offline without external services.
Stores spans in memory and optionally flushes to JSONL for analysis.

Usage:
    tracer = get_tracer("finroot")
    with tracer.start_span("classify_intent") as span:
        span.set_attribute("intent", "portfolio")
        # ... do work ...
        span.set_status(SpanStatus.OK)

    # Export for analysis
    tracer.export_jsonl("traces/pipeline.jsonl")
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class SpanStatus(StrEnum):
    """Span status codes (mirrors OpenTelemetry)."""

    OK = "OK"
    ERROR = "ERROR"
    UNSET = "UNSET"


class SpanKind(StrEnum):
    """Span kind (mirrors OpenTelemetry)."""

    INTERNAL = "INTERNAL"
    SERVER = "SERVER"
    CLIENT = "CLIENT"
    PRODUCER = "PRODUCER"
    CONSUMER = "CONSUMER"


class Span:
    """A single trace span — represents a unit of work.

    Attributes are typed key-value pairs for structured analysis.
    """

    def __init__(
        self,
        name: str,
        trace_id: str,
        parent_id: str | None = None,
        kind: SpanKind = SpanKind.INTERNAL,
    ) -> None:
        self.span_id: str = uuid.uuid4().hex[:16]
        self.trace_id: str = trace_id
        self.parent_id: str | None = parent_id
        self.name: str = name
        self.kind: SpanKind = kind
        self.status: SpanStatus = SpanStatus.UNSET
        self.attributes: dict[str, Any] = {}
        self.events: list[dict[str, Any]] = []
        self.start_time: float = time.time()
        self.end_time: float | None = None
        self._started: bool = True

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a typed attribute on the span."""
        self.attributes[key] = value

    def set_status(self, status: SpanStatus, description: str = "") -> None:
        """Set the span status."""
        self.status = status
        if description:
            self.attributes["status_description"] = description

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """Add a timed event to the span."""
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })

    def record_exception(self, exc: Exception) -> None:
        """Record an exception on the span."""
        self.set_status(SpanStatus.ERROR, str(exc))
        self.add_event("exception", {
            "type": type(exc).__name__,
            "message": str(exc),
        })

    def end(self) -> None:
        """End the span."""
        self.end_time = time.time()
        self._started = False

    @property
    def duration_ms(self) -> float | None:
        """Duration in milliseconds."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000

    def to_dict(self) -> dict[str, Any]:
        """Convert span to a serializable dict."""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "kind": self.kind.value,
            "status": self.status.value,
            "attributes": self.attributes,
            "events": self.events,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
        }


class Tracer:
    """Tracer — creates and manages spans for a trace.

    Usage:
        tracer = Tracer("finroot.pipeline")
        with tracer.start_span("classify") as span:
            span.set_attribute("intent", "portfolio")
    """

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.spans: list[Span] = []
        self._current_span: Span | None = None
        self._trace_id: str = uuid.uuid4().hex[:32]

    @contextmanager
    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        parent: Span | None = None,
    ) -> Generator[Span, None, None]:
        """Start a new span as a context manager.

        The span is automatically ended when the context exits.
        If an exception occurs, it's recorded on the span.
        """
        parent_id = parent.span_id if parent else (
            self._current_span.span_id if self._current_span else None
        )

        span = Span(
            name=name,
            trace_id=self._trace_id,
            parent_id=parent_id,
            kind=kind,
        )

        # Link to parent
        if self._current_span:
            span.attributes["parent_span_name"] = self._current_span.name

        self.spans.append(span)
        previous_span = self._current_span
        self._current_span = span

        try:
            yield span
        except Exception as exc:
            span.record_exception(exc)
            raise
        finally:
            span.end()
            self._current_span = previous_span

    @property
    def current_span(self) -> Span | None:
        """Get the currently active span."""
        return self._current_span

    def get_trace_id(self) -> str:
        """Get the current trace ID."""
        return self._trace_id

    def new_trace(self) -> str:
        """Start a new trace and return the trace ID."""
        self._trace_id = uuid.uuid4().hex[:32]
        return self._trace_id

    def export_dict(self) -> dict[str, Any]:
        """Export all spans as a dict."""
        return {
            "tracer": self.name,
            "trace_id": self._trace_id,
            "span_count": len(self.spans),
            "spans": [s.to_dict() for s in self.spans],
            "exported_at": datetime.now(UTC).isoformat(),
        }

    def export_jsonl(self, path: str | Path) -> None:
        """Export spans to a JSONL file (one span per line)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "a", encoding="utf-8") as f:
            for span in self.spans:
                record = {
                    "tracer": self.name,
                    "exported_at": datetime.now(UTC).isoformat(),
                    **span.to_dict(),
                }
                f.write(json.dumps(record, default=str) + "\n")

        logger.info("Exported %d spans to %s", len(self.spans), path)

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the trace."""
        if not self.spans:
            return {"span_count": 0, "total_duration_ms": 0}

        total_duration = sum(s.duration_ms or 0 for s in self.spans)
        error_count = sum(1 for s in self.spans if s.status == SpanStatus.ERROR)

        return {
            "span_count": len(self.spans),
            "total_duration_ms": round(total_duration, 2),
            "error_count": error_count,
            "trace_id": self._trace_id,
            "spans": [
                {
                    "name": s.name,
                    "duration_ms": round(s.duration_ms or 0, 2),
                    "status": s.status.value,
                }
                for s in self.spans
            ],
        }


# ---------------------------------------------------------------------------
# Global tracer instance
# ---------------------------------------------------------------------------

_global_tracer: Tracer | None = None


def get_tracer(name: str = "finroot") -> Tracer:
    """Get or create the global tracer instance."""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = Tracer(name)
    return _global_tracer


def reset_tracer() -> None:
    """Reset the global tracer (useful for tests)."""
    global _global_tracer
    _global_tracer = None


__all__ = [
    "Span",
    "SpanKind",
    "SpanStatus",
    "Tracer",
    "get_tracer",
    "reset_tracer",
]
