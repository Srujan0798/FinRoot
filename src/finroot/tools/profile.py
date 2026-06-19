"""UserProfileTool — read/write the Digital Twin profile.

Reads from DigitalTwinStore if available (W2), otherwise falls back to
data/samples/twin_profiles.json (G-0b pattern).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, model_validator

from finroot.tools.base import BaseTool, ToolCallError

logger = logging.getLogger(__name__)

_PROFILES_PATH = Path("data/samples/twin_profiles.json")

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ProfileReadInput(BaseModel):
    """Input for reading a user profile."""

    user_id: str
    fields: list[str] | None = None

    model_config = {"extra": "forbid"}


class ProfileWriteInput(BaseModel):
    """Input for writing/updating a user profile."""

    user_id: str
    updates: dict[str, Any]

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def _non_empty_updates(self) -> ProfileWriteInput:
        if not self.updates:
            raise ValueError("updates must be non-empty")
        return self


class ProfileOutput(BaseModel):
    """Output from a profile read/write operation."""

    user_id: str
    data: dict[str, Any]
    citation: str


# ---------------------------------------------------------------------------
# JSON fallback store
# ---------------------------------------------------------------------------


def _load_profiles_json() -> list[dict[str, Any]]:
    """Load profiles from the JSON fallback file."""
    if not _PROFILES_PATH.exists():
        return []
    with open(_PROFILES_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save_profiles_json(profiles: list[dict[str, Any]]) -> None:
    """Persist profiles to the JSON fallback file."""
    _PROFILES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_PROFILES_PATH, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)


def _find_profile(profiles: list[dict[str, Any]], user_id: str) -> dict[str, Any] | None:
    """Find a profile by user_id in the list."""
    for p in profiles:
        if p.get("user_id") == user_id:
            return p
    return None


# ---------------------------------------------------------------------------
# UserProfileTool
# ---------------------------------------------------------------------------


class UserProfileTool(BaseTool[ProfileReadInput | ProfileWriteInput, ProfileOutput]):
    """Read/write the Digital Twin profile.

    Falls back to JSON file if DigitalTwinStore is not yet available (G-0b).
    """

    name = "user_profile"
    ttl_seconds = 3600  # tax/profile cache TTL per contract

    def _run(self, inp: ProfileReadInput | ProfileWriteInput) -> ProfileOutput:
        if isinstance(inp, ProfileReadInput):
            return self._read(inp)
        return self._write(inp)

    def _read(self, inp: ProfileReadInput) -> ProfileOutput:
        """Read a user profile."""
        profile = self._load_profile(inp.user_id)
        if profile is None:
            raise ToolCallError(
                f"UserProfileTool: no profile found for user_id={inp.user_id!r}"
            )
        # Filter fields if requested
        if inp.fields is not None:
            data = {k: v for k, v in profile.items() if k in inp.fields}
        else:
            data = dict(profile)
        return ProfileOutput(
            user_id=inp.user_id,
            data=data,
            citation=f"DigitalTwin profile for {inp.user_id}",
        )

    def _write(self, inp: ProfileWriteInput) -> ProfileOutput:
        """Update a user profile and persist."""
        profile = self._load_profile(inp.user_id)
        if profile is None:
            raise ToolCallError(
                f"UserProfileTool: no profile found for user_id={inp.user_id!r}"
            )
        profile.update(inp.updates)
        self._save_profile(inp.user_id, profile)
        return ProfileOutput(
            user_id=inp.user_id,
            data=dict(profile),
            citation=f"DigitalTwin profile for {inp.user_id}",
        )

    def _load_profile(self, user_id: str) -> dict[str, Any] | None:
        """Try DigitalTwinStore first, fall back to JSON."""
        try:
            from finroot.memory.digital_twin import DigitalTwinStore  # type: ignore[import-untyped]

            store = DigitalTwinStore()
            twin = store.load(user_id)
            return twin.model_dump() if twin is not None else None
        except (ImportError, Exception):
            pass
        # JSON fallback
        profiles = _load_profiles_json()
        return _find_profile(profiles, user_id)

    def _save_profile(self, user_id: str, profile: dict[str, Any]) -> None:
        """Try DigitalTwinStore first, fall back to JSON."""
        try:
            from finroot.memory.digital_twin import (  # type: ignore[import-untyped]
                DigitalTwin,
                DigitalTwinStore,
            )

            store = DigitalTwinStore()
            twin = DigitalTwin(**profile)
            store.save(twin)
            return
        except (ImportError, Exception):
            pass
        # JSON fallback
        profiles = _load_profiles_json()
        existing = _find_profile(profiles, user_id)
        if existing is not None:
            existing.update(profile)
        else:
            profiles.append(profile)
        _save_profiles_json(profiles)


__all__ = [
    "ProfileReadInput",
    "ProfileWriteInput",
    "ProfileOutput",
    "UserProfileTool",
]
