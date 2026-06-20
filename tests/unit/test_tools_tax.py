"""Tests for TaxRuleTool (wave-3, task 04).

Covers the contract in ``.specify/specs/wave-3/contracts/tools.contract.md``:

* Deterministic tax computation (known values hand-computed)
* Input validation (negative gain, invalid gain_type)
* TTL cache (hit on second call)
* Audit emission
* extra="forbid" guard
"""

from __future__ import annotations

from pathlib import Path
from tempfile import mkdtemp

import pytest
from pydantic import ValidationError

from finroot.audit import AuditTrail
from finroot.tools.base import ToolCallError
from finroot.tools.tax import (
    TaxInput,
    TaxOutput,
    TaxRuleTool,
    ToolError,
)

# ---------------------------------------------------------------------------
# Hand-computed expected values (FY 2024-25 rules)
#
# LTCG_EQUITY:  10% on gains > ₹1L exempt + 4% cess
# STCG_EQUITY:  15% flat + 4% cess
# STCG (other): marginal slab rate + 4% cess
# Surcharge:    10% on base_tax if annual_income > ₹50L
# Cess:         4% on (base_tax + surcharge)
# ---------------------------------------------------------------------------

_LTCG_2L_EXPECTED = 10_400.0  # (2L - 1L) * 10% = 10k + 400 cess
_LTCG_50K_EXPECTED = 0.0      # fully exempt
_STCG_EQ_1L_EXPECTED = 15_600.0  # 1L * 15% = 15k + 600 cess
_STCG_DEBT_8L_EXPECTED = 10_400.0  # 1L * 10% (slab) = 10k + 400 cess


# ---------------------------------------------------------------------------
# Counter subclass (test seam — verify cache layer)
# ---------------------------------------------------------------------------


class _CountingTaxTool(TaxRuleTool):
    """Count how many times ``_run`` is actually invoked (cache misses)."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.run_count = 0

    def _run(self, inp: TaxInput) -> TaxOutput:
        self.run_count += 1
        return super()._run(inp)


# ===========================================================================
# TaxRuleTool — deterministic computation (hand-computed values)
# ===========================================================================


class TestTaxRuleToolComputation:
    def test_ltcg_2l_gain(self) -> None:
        """LTCG ₹2L: exempt ₹1L → tax on ₹1L = ₹10,000 + cess ₹400 = ₹10,400."""
        tool = TaxRuleTool()
        out = tool(TaxInput(gain=200_000, gain_type="LTCG", annual_income=200_000))
        assert out.tax_amount == _LTCG_2L_EXPECTED
        assert out.breakdown["base_tax"] == 10_000.0
        assert out.breakdown["cess"] == 400.0
        assert out.breakdown["surcharge"] == 0.0

    def test_ltcg_50k_gain(self) -> None:
        """LTCG ₹50k: fully exempt → ₹0."""
        tool = TaxRuleTool()
        out = tool(TaxInput(gain=50_000, gain_type="LTCG", annual_income=50_000))
        assert out.tax_amount == _LTCG_50K_EXPECTED
        assert out.breakdown["base_tax"] == 0.0

    def test_stcg_equity_1l(self) -> None:
        """STCG_EQUITY ₹1L: 15% = ₹15,000 + cess ₹600 = ₹15,600."""
        tool = TaxRuleTool()
        out = tool(TaxInput(gain=100_000, gain_type="STCG_EQUITY", annual_income=100_000))
        assert out.tax_amount == _STCG_EQ_1L_EXPECTED
        assert out.breakdown["base_tax"] == 15_000.0
        assert out.breakdown["cess"] == 600.0

    def test_stcg_debt_income_8l(self) -> None:
        """STCG (debt) at income ₹8L: slab 10% = ₹10,000 + cess ₹400."""
        tool = TaxRuleTool()
        out = tool(TaxInput(gain=100_000, gain_type="STCG", annual_income=800_000))
        assert out.tax_amount == _STCG_DEBT_8L_EXPECTED
        assert out.breakdown["base_tax"] == 10_000.0
        assert out.breakdown["cess"] == 400.0

    def test_surcharge_over_50l(self) -> None:
        """Surcharge kicks in when annual_income > ₹50L."""
        tool = TaxRuleTool()
        out = tool(
            TaxInput(gain=1_000_000, gain_type="LTCG", annual_income=6_000_000)
        )
        # Taxable gain = 1M - 100k = 900k; base = 900k * 10% = 90k
        # Surcharge = 90k * 10% = 9k
        # Cess = (90k + 9k) * 4% = 3,960
        assert out.breakdown["base_tax"] == 90_000.0
        assert out.breakdown["surcharge"] == 9_000.0
        assert out.breakdown["cess"] == 3_960.0
        assert out.tax_amount == 102_960.0

    def test_ltcg_zero_gain(self) -> None:
        """Zero gain yields zero tax."""
        tool = TaxRuleTool()
        out = tool(TaxInput(gain=0.0, gain_type="LTCG", annual_income=0))
        assert out.tax_amount == 0.0
        assert out.breakdown["base_tax"] == 0.0

    def test_stcg_equity_surcharge(self) -> None:
        """STCG_EQUITY with income > ₹50L includes surcharge + cess."""
        tool = TaxRuleTool()
        out = tool(
            TaxInput(gain=500_000, gain_type="STCG_EQUITY", annual_income=10_000_000)
        )
        # Base = 500k * 15% = 75k
        # Surcharge = 75k * 10% = 7.5k
        # Cess = (75k + 7.5k) * 4% = 3.3k
        assert out.breakdown["base_tax"] == 75_000.0
        assert out.breakdown["surcharge"] == 7_500.0
        assert out.breakdown["cess"] == 3_300.0
        assert out.tax_amount == 85_800.0

    def test_stcg_debt_income_12l(self) -> None:
        """STCG (debt) at income ₹12L uses 20% slab."""
        tool = TaxRuleTool()
        out = tool(TaxInput(gain=100_000, gain_type="STCG", annual_income=1_200_000))
        # Slab 12L-15L = 20%; base = 100k * 20% = 20k; cess = 800
        assert out.breakdown["base_tax"] == 20_000.0
        assert out.breakdown["cess"] == 800.0
        assert out.tax_amount == 20_800.0

    def test_stcg_debt_income_2l(self) -> None:
        """STCG (debt) at income ₹2L uses 0% slab — zero tax."""
        tool = TaxRuleTool()
        out = tool(TaxInput(gain=100_000, gain_type="STCG", annual_income=200_000))
        assert out.breakdown["base_tax"] == 0.0
        assert out.tax_amount == 0.0

    def test_cess_false_omits_cess(self) -> None:
        """When cess=False, the 4% cess is omitted."""
        tool = TaxRuleTool()
        out = tool(
            TaxInput(gain=100_000, gain_type="STCG_EQUITY", annual_income=100_000, cess=False)
        )
        assert out.breakdown["base_tax"] == 15_000.0
        assert out.breakdown["cess"] == 0.0
        assert out.tax_amount == 15_000.0

    def test_cess_false_with_surcharge(self) -> None:
        """When cess=False but surcharge applies, only surcharge is added."""
        tool = TaxRuleTool()
        out = tool(
            TaxInput(gain=1_000_000, gain_type="LTCG", annual_income=6_000_000, cess=False)
        )
        assert out.breakdown["base_tax"] == 90_000.0
        assert out.breakdown["surcharge"] == 9_000.0
        assert out.breakdown["cess"] == 0.0
        assert out.tax_amount == 99_000.0


# ===========================================================================
# TaxRuleTool — input validation
# ===========================================================================


class TestTaxRuleToolInputValidation:
    def test_negative_gain_raises_tool_error(self) -> None:
        """Negative gain fails loud (FM-11)."""
        tool = TaxRuleTool()
        with pytest.raises((ToolError, ToolCallError), match="Negative gain"):
            tool(TaxInput(gain=-100, gain_type="LTCG", annual_income=100_000))

    def test_invalid_gain_type_raises_validation_error(self) -> None:
        """Pydantic catches invalid Literal value."""
        with pytest.raises(ValidationError):
            TaxInput(gain=100_000, gain_type="UNKNOWN", annual_income=100_000)  # type: ignore[arg-type]

    def test_extra_field_raises_validation_error(self) -> None:
        """extra="forbid" guard."""
        with pytest.raises(ValidationError):
            TaxInput(gain=100_000, gain_type="LTCG", annual_income=100_000, bogus=1)  # type: ignore[call-arg]

    def test_missing_required_field_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            TaxInput()  # type: ignore[call-arg]


# ===========================================================================
# TaxRuleTool — TTL cache
# ===========================================================================


class TestTaxRuleToolCache:
    def test_cache_hit_on_second_call(self) -> None:
        tool = _CountingTaxTool()
        inp = TaxInput(gain=200_000, gain_type="LTCG", annual_income=200_000)
        r1 = tool(inp)
        r2 = tool(inp)
        assert r1 is r2
        assert tool.run_count == 1

    def test_different_inputs_distinct_cache(self) -> None:
        tool = _CountingTaxTool()
        a = TaxInput(gain=200_000, gain_type="LTCG", annual_income=200_000)
        b = TaxInput(gain=100_000, gain_type="STCG_EQUITY", annual_income=100_000)
        tool(a)
        tool(b)
        tool(a)  # cached
        assert tool.run_count == 2

    def test_ttl_is_3600_per_contract(self) -> None:
        assert TaxRuleTool.ttl_seconds == 3600


# ===========================================================================
# TaxRuleTool — audit emission
# ===========================================================================


class TestTaxRuleToolAudit:
    def test_audit_event_emitted_on_call(self) -> None:
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        tool = TaxRuleTool(audit=audit)
        tool(TaxInput(gain=200_000, gain_type="LTCG", annual_income=200_000))
        events = audit.replay()
        assert len(events) == 1
        assert events[0].type == "tool.called"
        assert events[0].payload["tool"] == "tax_rule"

    def test_no_audit_event_when_trail_omitted(self) -> None:
        tool = TaxRuleTool()
        out = tool(TaxInput(gain=200_000, gain_type="LTCG", annual_income=200_000))
        assert out.tax_amount == _LTCG_2L_EXPECTED


# ===========================================================================
# TaxRuleTool — output shape & conventions
# ===========================================================================


class TestTaxRuleToolOutput:
    def test_output_type_and_fields(self) -> None:
        tool = TaxRuleTool()
        out = tool(TaxInput(gain=200_000, gain_type="LTCG", annual_income=200_000))
        assert isinstance(out, TaxOutput)
        assert isinstance(out.tax_amount, float)
        assert isinstance(out.effective_rate_pct, float)
        assert isinstance(out.breakdown, dict)
        assert isinstance(out.rule_applied, str)
        assert isinstance(out.citation, str)

    def test_breakdown_contains_expected_keys(self) -> None:
        tool = TaxRuleTool()
        out = tool(TaxInput(gain=200_000, gain_type="LTCG", annual_income=200_000))
        assert set(out.breakdown.keys()) == {"taxable_gain", "base_tax", "surcharge", "cess"}

    def test_rule_applied_is_human_readable(self) -> None:
        tool = TaxRuleTool()
        out = tool(TaxInput(gain=200_000, gain_type="LTCG", annual_income=200_000))
        assert "LTCG_EQUITY" in out.rule_applied
        assert "Budget 2024" in out.rule_applied

    def test_citation_includes_finance_act(self) -> None:
        tool = TaxRuleTool()
        out = tool(TaxInput(gain=200_000, gain_type="LTCG", annual_income=200_000))
        assert "Income Tax Act 1961" in out.citation
        assert "2024-25" in out.citation

    def test_effective_rate_is_correct(self) -> None:
        tool = TaxRuleTool()
        out = tool(TaxInput(gain=200_000, gain_type="LTCG", annual_income=200_000))
        # Total 10,400 / gain 200,000 = 5.2%
        assert out.effective_rate_pct == pytest.approx(5.2, rel=1e-4)

    def test_deterministic_same_input_same_output(self) -> None:
        tool = TaxRuleTool()
        inp = TaxInput(gain=200_000, gain_type="LTCG", annual_income=200_000)
        r1 = tool(inp)
        r2 = tool(inp)
        assert r1.tax_amount == r2.tax_amount
        assert r1.breakdown == r2.breakdown
        assert r1.rule_applied == r2.rule_applied
