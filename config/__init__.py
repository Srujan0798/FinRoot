"""FinRoot configuration: settings loader + prompt registry."""

from config.prompts import PromptRegistry
from config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings", "PromptRegistry"]
