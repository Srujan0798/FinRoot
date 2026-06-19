"""Versioned prompt registry — own-your-prompts for the reasoning pipeline."""

from __future__ import annotations

_DEFAULT_PROMPTS: dict[tuple[str, str], str] = {
    ("router.system", "1.0"): (
        "You are a financial-intent classifier. "
        "Given a user query, classify it into one of: "
        "portfolio, risk, tax, news_impact, cashflow, credit, general. "
        "Reply with a single word."
    ),
    ("reason.analysis", "1.0"): (
        "You are a financial reasoning agent. "
        "Analyse the user's portfolio, cite sources, flag risks, "
        "and assign a confidence level to your recommendation. "
        "If evidence is insufficient, say so."
    ),
    ("summarise.result", "1.0"): (
        "Summarise the following financial analysis for the user. "
        "Highlight key numbers, risks, and your recommended action."
    ),
}


class PromptRegistry:
    """A registry of versioned prompt templates.

    Lookup is by ``(name, version)``.  ``version="latest"`` returns the
    highest-sorted version for that name.
    """

    def __init__(self) -> None:
        self._prompts: dict[tuple[str, str], str] = {}
        self.load_defaults()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_defaults(self) -> None:
        self._prompts.update(_DEFAULT_PROMPTS)

    def register(self, name: str, version: str, template: str) -> None:
        self._prompts[(name, version)] = template

    def get(self, name: str, version: str = "latest") -> str:
        if version == "latest":
            return self._get_latest(name)
        key = (name, version)
        if key not in self._prompts:
            msg = f"Unknown prompt: name={name!r}, version={version!r}"
            raise KeyError(msg)
        return self._prompts[key]

    def list_names(self) -> set[str]:
        return {name for name, _ in self._prompts}

    def versions(self, name: str) -> list[str]:
        return [v for n, v in self._prompts if n == name]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_latest(self, name: str) -> str:
        candidates = [(v, t) for (n, v), t in self._prompts.items() if n == name]
        if not candidates:
            msg = f"Unknown prompt name={name!r} — no versions registered"
            raise KeyError(msg)
        candidates.sort(key=lambda x: x[0])
        return candidates[-1][1]
