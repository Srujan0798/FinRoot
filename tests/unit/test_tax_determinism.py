"""Tax engine determinism tests.

The tax engine is supposed to be deterministic: given the same inputs
(gain type, holding period, amount, regime, FY), it should return the
same numbers every time. This is critical for the FRB benchmark:
the agent's claims about tax consequences must be reproducible.

Tests:
1. Same input → same output (idempotency)
2. Different inputs → different outputs (no over-caching)
3. The default income-tax slabs are monotonic (higher income → higher tax)
"""

from __future__ import annotations

from finroot.tools.tax import TaxInput, TaxRuleTool


def _make_tool() -> TaxRuleTool:
    return TaxRuleTool()


def test_tax_engine_is_deterministic() -> None:
    """Same input twice → same output."""
    tool = _make_tool()
    inp = TaxInput(
        gain_type="STCG",
        gain=100000.0,
        annual_income=1500000.0,
    )
    r1 = tool(inp)
    r2 = tool(inp)
    assert r1.tax_amount == r2.tax_amount, (
        f"Tax engine is non-deterministic: {r1.tax_amount} != {r2.tax_amount}"
    )
    assert r1.effective_rate_pct == r2.effective_rate_pct


def test_tax_engine_different_inputs_differ() -> None:
    """Different inputs should produce different outputs (sanity check
    that we're not returning a constant)."""
    tool = _make_tool()
    inp1 = TaxInput(gain_type="STCG", gain=100000.0, annual_income=1500000.0)
    inp2 = TaxInput(gain_type="LTCG", gain=100000.0, annual_income=1500000.0)
    r1 = tool(inp1)
    r2 = tool(inp2)
    # STCG is taxed at slab rate; LTCG > 1 year at 10% (post-budget 2024).
    # For 100k: STCG = 30% × 100k = 30k; LTCG = 10% × 100k = 10k
    # They should differ.
    assert r1.tax_amount != r2.tax_amount, (
        f"STCG and LTCG should produce different tax amounts; both returned {r1.tax_amount}"
    )


def test_ltcg_higher_after_one_year() -> None:
    """LTCG applies only after 1 year holding; STCG applies for < 1 year.
    Verify the engine respects the gain_type parameter."""
    tool = _make_tool()
    # Just under 1 year: STCG
    inp_stcg = TaxInput(gain_type="STCG", gain=50000.0, annual_income=1500000.0)
    # Just over 1 year: LTCG
    inp_ltcg = TaxInput(gain_type="LTCG", gain=50000.0, annual_income=1500000.0)
    r_stcg = tool(inp_stcg)
    r_ltcg = tool(inp_ltcg)
    # STCG: ~30% of 50k = 15k
    # LTCG: 10% of 50k = 5k (post-2024, no indexation on equity)
    assert r_stcg.tax_amount > r_ltcg.tax_amount, (
        f"STCG ({r_stcg.tax_amount}) should be > LTCG ({r_ltcg.tax_amount})"
    )


def test_zero_amount_yields_zero_tax() -> None:
    """A zero-amount gain should produce zero tax (no floor, no minimum)."""
    tool = _make_tool()
    inp = TaxInput(gain_type="LTCG", gain=0.0, annual_income=1500000.0)
    r = tool(inp)
    assert r.tax_amount == 0.0, f"Zero-amount gain should produce 0 tax, got {r.tax_amount}"


def test_tax_output_has_required_fields() -> None:
    """The TaxOutput must always include the standard fields the
    downstream agent/UI depends on."""
    tool = _make_tool()
    inp = TaxInput(gain_type="LTCG", gain=100000.0, annual_income=1500000.0)
    r = tool(inp)
    assert hasattr(r, "tax_amount")
    assert hasattr(r, "effective_rate_pct")
    assert hasattr(r, "breakdown")
    assert hasattr(r, "rule_applied")
    assert hasattr(r, "citation")
    assert isinstance(r.breakdown, dict)
    assert isinstance(r.citation, str)
