"""WatchlistAlertTool — check watchlist price alerts.

Reads/writes JSON files at data/watchlists/{user_id}.json.
No external API — fully local persistence.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from finroot.tools.base import BaseTool

logger = logging.getLogger(__name__)

_WATCHLISTS_DIR = Path("data/watchlists")

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class WatchlistEntry(BaseModel):
    """A single watchlist alert entry."""

    symbol: str
    target_price: float
    direction: Literal["above", "below"]
    alert_message: str

    model_config = {"extra": "forbid"}


class AlertCheckInput(BaseModel):
    """Input for checking watchlist alerts."""

    user_id: str
    current_prices: dict[str, float]

    model_config = {"extra": "forbid"}


class AlertCheckOutput(BaseModel):
    """Output from a watchlist alert check."""

    triggered: list[WatchlistEntry]
    citation: str


# ---------------------------------------------------------------------------
# Persistence helpers (module-level, not BaseTool subclasses)
# ---------------------------------------------------------------------------


def _watchlist_path(user_id: str) -> Path:
    return _WATCHLISTS_DIR / f"{user_id}.json"


def load_watchlist(user_id: str) -> list[WatchlistEntry]:
    """Load a user's watchlist. Returns empty list if file absent."""
    path = _watchlist_path(user_id)
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        raw: list[dict[str, Any]] = json.load(f)
    return [WatchlistEntry.model_validate(entry) for entry in raw]


def save_watchlist(user_id: str, entries: list[WatchlistEntry]) -> None:
    """Persist a user's watchlist."""
    path = _watchlist_path(user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([e.model_dump() for e in entries], f, indent=2, ensure_ascii=False)


def add_to_watchlist(user_id: str, entry: WatchlistEntry) -> None:
    """Add an entry to the user's watchlist (persists)."""
    entries = load_watchlist(user_id)
    # Replace if same symbol already exists
    entries = [e for e in entries if e.symbol != entry.symbol]
    entries.append(entry)
    save_watchlist(user_id, entries)


def remove_from_watchlist(user_id: str, symbol: str) -> None:
    """Remove a symbol from the user's watchlist (persists)."""
    entries = load_watchlist(user_id)
    entries = [e for e in entries if e.symbol != symbol]
    save_watchlist(user_id, entries)


# ---------------------------------------------------------------------------
# WatchlistAlertTool
# ---------------------------------------------------------------------------


class WatchlistAlertTool(BaseTool[AlertCheckInput, AlertCheckOutput]):
    """Check watchlist price alerts for a user."""

    name = "watchlist_alert"
    ttl_seconds = 0  # no caching — prices are real-time

    def _run(self, inp: AlertCheckInput) -> AlertCheckOutput:
        entries = load_watchlist(inp.user_id)
        triggered: list[WatchlistEntry] = []

        for entry in entries:
            current = inp.current_prices.get(entry.symbol)
            if current is None:
                continue  # symbol not in current_prices, skip
            if (entry.direction == "above" and current >= entry.target_price) or (
                entry.direction == "below" and current <= entry.target_price
            ):
                triggered.append(entry)

        return AlertCheckOutput(
            triggered=triggered,
            citation=(
                f"Watchlist check for {inp.user_id}, "
                f"{len(entries)} symbols evaluated"
            ),
        )


__all__ = [
    "WatchlistEntry",
    "AlertCheckInput",
    "AlertCheckOutput",
    "WatchlistAlertTool",
    "add_to_watchlist",
    "remove_from_watchlist",
    "load_watchlist",
    "save_watchlist",
]
