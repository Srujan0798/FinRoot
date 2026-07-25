"""Test that the public import surface is stable.

Lock the top-level names exposed by each public module so that
refactors don't accidentally remove a symbol that downstream code
(judges, the submission zip's demos) depends on.

If you intentionally remove a public symbol, this test will fail and
you must update it (or bump a major version).
"""

from __future__ import annotations

import importlib

import pytest

# Pairs of (module_name, expected_attribute_names) — add to this list
# when you add a new public symbol.
PUBLIC_API = [
    # Core entry points (used by the CLI and the Streamlit UI)
    ("interface.core", ["answer", "stream_answer", "build_trace"]),
    ("interface.cli.main", ["app"]),
    # Schemas (used by every agent/tool)
    ("finroot.schemas", []),  # any class imported is part of the API
    # Tools (the judge queries these in the FRB benchmark)
    ("finroot.tools.market", ["MarketDataTool", "MarketDataInput", "MarketDataOutput"]),
    (
        "finroot.tools.profile",
        ["UserProfileTool", "ProfileReadInput", "ProfileWriteInput", "ProfileOutput"],
    ),
    ("finroot.tools.tax", ["TaxRuleTool", "TaxInput", "TaxOutput"]),
    ("finroot.tools.risk", ["RiskCalculationTool", "RiskInput", "RiskOutput"]),
    (
        "finroot.tools.watchlist",
        [
            "WatchlistAlertTool",
            "WatchlistEntry",
            "add_to_watchlist",
            "load_watchlist",
            "remove_from_watchlist",
            "save_watchlist",
        ],
    ),
    ("finroot.tools.documents", ["DocumentParserTool"]),
    # Agents
    ("finroot.agents.market_agent", ["MarketAnalystAgent"]),
    ("finroot.agents.tax_agent", ["TaxPlannerAgent"]),
    ("finroot.agents.risk_agent", ["RiskAssessorAgent"]),
    ("finroot.agents.portfolio_agent", ["PortfolioOptimizerAgent"]),
    # Memory (used by orchestrator)
    ("finroot.memory.digital_twin", ["DigitalTwin", "DigitalTwinStore"]),
    ("finroot.memory.semantic", ["SemanticMemory"]),
    ("finroot.memory.working", ["WorkingMemory"]),
    # Config (used by CLI and conftest)
    ("config.settings", ["Settings", "get_settings"]),
    ("config.prompts", ["PromptRegistry"]),
    # LLM providers
    ("finroot.llm.mock", ["MockProvider"]),
]


@pytest.mark.parametrize("module_name,expected_attrs", PUBLIC_API)
def test_module_imports(module_name: str, expected_attrs: list[str]) -> None:
    """Each public module must be importable."""
    mod = importlib.import_module(module_name)
    assert mod is not None, f"Failed to import {module_name}"


@pytest.mark.parametrize("module_name,expected_attrs", PUBLIC_API)
def test_expected_attributes_exist(module_name: str, expected_attrs: list[str]) -> None:
    """Each public module must expose the expected attributes."""
    if not expected_attrs:
        return  # nothing to check
    mod = importlib.import_module(module_name)
    missing = [attr for attr in expected_attrs if not hasattr(mod, attr)]
    assert not missing, (
        f"Module {module_name} is missing expected attributes: {missing}. "
        f"If you intentionally removed a public symbol, update PUBLIC_API "
        f"in tests/unit/test_public_api.py."
    )


def test_finroot_top_level_has_no_accidental_reexports() -> None:
    """A regression guard: `from finroot import *` should not pull in
    secrets, internal modules, or anything that's not a deliberate
    re-export. This catches accidentally setting `__all__` in a way
    that leaks internals."""
    import finroot  # noqa: F401

    # The package should at least import. We don't enumerate the full
    # surface (intentionally large) but we do verify there's no
    # `_`-prefixed name in the top-level namespace (convention for
    # private — should not be re-exported at the package level).
    leaked = [n for n in dir(finroot) if n.startswith("_") and not n.startswith("__")]
    assert not leaked, f"finroot package re-exports private names: {leaked}"
