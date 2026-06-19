"""Startup config assertions and banner — fails loud on critical misconfig."""

from __future__ import annotations

import logging
import os

from config.settings import Settings

logger = logging.getLogger("finroot.config")


def assert_settings(settings: Settings) -> None:
    """Validate critical settings at startup.

    Raises ``RuntimeError`` with a descriptive message if any check fails
    (FM-11: fail loud, never silently substitute).
    """
    if settings.llm_provider == "ollama":
        _assert_non_empty("ollama_base_url", settings.ollama_base_url)

    if settings.llm_provider == "groq":
        _assert_non_empty("groq_api_key", settings.groq_api_key)

    if settings.llm_provider == "openai":
        _assert_non_empty("openai_api_key", settings.openai_api_key)

    _ensure_writeable_dir(settings.chroma_dir)
    _ensure_writeable_parent(settings.audit_path)


def print_startup_banner(settings: Settings) -> None:
    """Print a one-line startup banner showing the active config."""
    banner = (
        f"FinRoot | provider={settings.llm_provider} "
        f"ollama={settings.ollama_model}@{settings.ollama_base_url} "
        f"chroma={settings.chroma_dir} audit={settings.audit_path}"
    )
    print(banner)
    logger.info("Startup config: %s", banner)


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------


def _assert_non_empty(name: str, value: str | None) -> None:
    if not value:
        raise RuntimeError(
            f"Required setting '{name}' is empty or None "
            f"for provider {value!r}. Set FINROOT_{name.upper()}=..."
        )


def _ensure_writeable_dir(path: str) -> None:
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(
            f"Cannot create directory '{path}': {exc}"
        ) from exc


def _ensure_writeable_parent(path: str) -> None:
    parent = os.path.dirname(path) or "."
    try:
        os.makedirs(parent, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(
            f"Cannot create parent directory '{parent}' for '{path}': {exc}"
        ) from exc
