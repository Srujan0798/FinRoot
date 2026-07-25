"""Tests for the tool registry — importability, metadata, and schema contracts.

Covers:
* Every tool module under finroot.tools is importable.
* Every concrete tool class has a `name` attribute and a non-empty description.
* Schema contracts for the five named tools (input/output field presence).
"""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path

import pytest

from finroot.tools.base import BaseTool

# ---------------------------------------------------------------------------
# Discover every tool module under finroot/tools/
# ---------------------------------------------------------------------------

_TOOLS_DIR = Path(__file__).resolve().parents[2] / "src" / "finroot" / "tools"

_TOOL_MODULE_NAMES: list[str] = sorted(
    p.stem
    for p in _TOOLS_DIR.glob("*.py")
    if p.stem != "__init__" and p.stem != "base" and not p.stem.startswith("_")
)


def _import_tool_module(name: str):
    return importlib.import_module(f"finroot.tools.{name}")


def _find_tool_classes(module) -> list[type[BaseTool]]:
    """Return every concrete BaseTool subclass defined in *module*."""
    classes: list[type[BaseTool]] = []
    for _name, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, BaseTool) and obj is not BaseTool and obj.__module__ == module.__name__:
            classes.append(obj)
    return classes


# ===========================================================================
# Importability
# ===========================================================================


@pytest.mark.wave1
class TestToolImportability:
    @pytest.mark.parametrize("module_name", _TOOL_MODULE_NAMES, ids=_TOOL_MODULE_NAMES)
    def test_all_tools_importable(self, module_name: str) -> None:
        mod = _import_tool_module(module_name)
        assert mod is not None


# ===========================================================================
# Metadata — name + description
# ===========================================================================


@pytest.mark.wave1
class TestToolMetadata:
    @pytest.mark.parametrize("module_name", _TOOL_MODULE_NAMES, ids=_TOOL_MODULE_NAMES)
    def test_all_tools_have_name(self, module_name: str) -> None:
        mod = _import_tool_module(module_name)
        for cls in _find_tool_classes(mod):
            assert hasattr(cls, "name"), f"{cls.__name__} missing 'name' attribute"
            assert isinstance(cls.name, str), f"{cls.__name__}.name is not a str"
            assert len(cls.name) > 0, f"{cls.__name__}.name is empty"

    @pytest.mark.parametrize("module_name", _TOOL_MODULE_NAMES, ids=_TOOL_MODULE_NAMES)
    def test_all_tools_have_description(self, module_name: str) -> None:
        mod = _import_tool_module(module_name)
        for cls in _find_tool_classes(mod):
            doc = inspect.getdoc(cls)
            assert doc, f"{cls.__name__} has no docstring (description)"
            assert len(doc.strip()) > 0, f"{cls.__name__} docstring is blank"


# ===========================================================================
# Schema contracts — MarketDataTool
# ===========================================================================


@pytest.mark.wave1
class TestMarketDataToolSchema:
    def test_market_data_tool_input_schema(self) -> None:
        from finroot.tools.market import MarketDataInput

        schema = MarketDataInput.model_json_schema()
        props = schema.get("properties", {})
        assert "symbol" in props
        assert "period" in props

    def test_market_data_tool_output_schema(self) -> None:
        from finroot.tools.market import MarketDataOutput

        schema = MarketDataOutput.model_json_schema()
        props = schema.get("properties", {})
        for field in (
            "symbol",
            "currency",
            "prices",
            "latest_price",
            "change_pct",
            "source",
            "citation",
        ):
            assert field in props, f"MarketDataOutput missing field: {field}"

    def test_market_data_tool_instantiation(self) -> None:
        from finroot.tools.market import MarketDataTool

        tool = MarketDataTool(mock=True)
        assert tool.name == "market_data"
        assert isinstance(tool, BaseTool)


# ===========================================================================
# Schema contracts — UserProfileTool
# ===========================================================================


@pytest.mark.wave1
class TestUserProfileToolSchema:
    def test_profile_read_input_schema(self) -> None:
        from finroot.tools.profile import ProfileReadInput

        schema = ProfileReadInput.model_json_schema()
        props = schema.get("properties", {})
        assert "user_id" in props
        assert "fields" in props

    def test_profile_write_input_schema(self) -> None:
        from finroot.tools.profile import ProfileWriteInput

        schema = ProfileWriteInput.model_json_schema()
        props = schema.get("properties", {})
        assert "user_id" in props
        assert "updates" in props

    def test_profile_output_schema(self) -> None:
        from finroot.tools.profile import ProfileOutput

        schema = ProfileOutput.model_json_schema()
        props = schema.get("properties", {})
        for field in ("user_id", "data", "citation"):
            assert field in props, f"ProfileOutput missing field: {field}"

    def test_user_profile_tool_instantiation(self) -> None:
        from finroot.tools.profile import UserProfileTool

        tool = UserProfileTool()
        assert tool.name == "user_profile"
        assert isinstance(tool, BaseTool)


# ===========================================================================
# Schema contracts — TaxRuleTool
# ===========================================================================


@pytest.mark.wave1
class TestTaxRuleToolSchema:
    def test_tax_input_schema(self) -> None:
        from finroot.tools.tax import TaxInput

        schema = TaxInput.model_json_schema()
        props = schema.get("properties", {})
        for field in ("gain", "gain_type", "annual_income", "cess"):
            assert field in props, f"TaxInput missing field: {field}"

    def test_tax_output_schema(self) -> None:
        from finroot.tools.tax import TaxOutput

        schema = TaxOutput.model_json_schema()
        props = schema.get("properties", {})
        for field in ("tax_amount", "effective_rate_pct", "breakdown", "rule_applied", "citation"):
            assert field in props, f"TaxOutput missing field: {field}"

    def test_tax_rule_tool_instantiation(self) -> None:
        from finroot.tools.tax import TaxRuleTool

        tool = TaxRuleTool()
        assert tool.name == "tax_rule"
        assert isinstance(tool, BaseTool)


# ===========================================================================
# Schema contracts — RiskCalculationTool
# ===========================================================================


@pytest.mark.wave1
class TestRiskCalculationToolSchema:
    def test_risk_input_schema(self) -> None:
        from finroot.tools.risk import RiskInput

        schema = RiskInput.model_json_schema()
        props = schema.get("properties", {})
        assert "returns" in props
        assert "confidence" in props

    def test_risk_output_schema(self) -> None:
        from finroot.tools.risk import RiskOutput

        schema = RiskOutput.model_json_schema()
        props = schema.get("properties", {})
        for field in (
            "n_observations",
            "confidence",
            "volatility_annual",
            "var_95",
            "cvar_95",
            "sharpe_ratio",
            "max_drawdown",
            "stress_tests",
            "scenario_analysis",
            "methodology",
            "citation",
        ):
            assert field in props, f"RiskOutput missing field: {field}"

    def test_risk_calculation_tool_instantiation(self) -> None:
        from finroot.tools.risk import RiskCalculationTool

        tool = RiskCalculationTool()
        assert tool.name == "risk_calculation"
        assert isinstance(tool, BaseTool)


# ===========================================================================
# Schema contracts — DocumentParserTool
# ===========================================================================


@pytest.mark.wave1
class TestDocumentParserToolSchema:
    def test_doc_parse_input_schema(self) -> None:
        from finroot.tools.documents import DocParseInput

        schema = DocParseInput.model_json_schema()
        props = schema.get("properties", {})
        assert "content" in props
        assert "doc_type" in props

    def test_doc_parse_output_schema(self) -> None:
        from finroot.tools.documents import DocParseOutput

        schema = DocParseOutput.model_json_schema()
        props = schema.get("properties", {})
        for field in ("doc_type", "extracted", "confidence", "citation"):
            assert field in props, f"DocParseOutput missing field: {field}"

    def test_document_parser_tool_instantiation(self) -> None:
        from finroot.tools.documents import DocumentParserTool

        tool = DocumentParserTool()
        assert tool.name == "document_parser"
        assert isinstance(tool, BaseTool)
