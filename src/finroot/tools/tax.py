"""Deterministic Indian capital gains tax calculator (FY 2024-25).

No live API. Rules stored in ``data/tax_rules.json``. Every output cites the
rule applied (FM-09: evidence required).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from finroot.audit.trail import AuditTrail
from finroot.tools.base import BaseTool, ToolCallError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Contract types (``tools.contract.md`` § TaxRuleTool)
# ---------------------------------------------------------------------------


class TaxInput(BaseModel):
    """Input for :class:`TaxRuleTool`.

    Mirrors the contract exactly. ``extra="forbid"`` is the typo guard.
    """

    model_config = ConfigDict(extra="forbid")

    gain: float = Field(description="Absolute capital gain in INR")
    gain_type: Literal["LTCG", "STCG", "STCG_EQUITY"] = Field(
        description="Type of capital gain"
    )
    annual_income: float = Field(
        description="Total annual income in INR (used for slab-rate determination)"
    )
    cess: bool = Field(
        default=True,
        description="Whether to add 4% health & education cess",
    )


class TaxOutput(BaseModel):
    """Output of :class:`TaxRuleTool`.

    ``breakdown`` exposes every component of the calculation so the
    orchestrator can render "show your math" explanations.
    """

    model_config = ConfigDict(extra="forbid")

    tax_amount: float
    effective_rate_pct: float
    breakdown: dict[str, float]
    rule_applied: str
    citation: str


class ToolError(ToolCallError):
    """Tool-level failure mode matching the contract convention (FM-11)."""


# ---------------------------------------------------------------------------
# Rule loading helpers
# ---------------------------------------------------------------------------

_RULES_PATH = Path(__file__).resolve().parents[3] / "data" / "tax_rules.json"


def _load_rules() -> dict:
    """Load and parse the tax rules file.

    Returns:
        The parsed JSON dictionary.

    Raises:
        ToolError: if the file is missing or malformed (FM-11).
    """
    path = _RULES_PATH
    if not path.is_file():
        raise ToolError(f"Tax rules file not found: {path}")
    try:
        with open(path, encoding="utf-8") as f:
            return dict(json.load(f))
    except (json.JSONDecodeError, OSError) as exc:
        raise ToolError(f"Failed to load tax rules from {path}: {exc}") from exc


def _find_rule(rules: dict, gain_type: str) -> dict | None:
    """Return the first rule whose ``gain_type`` matches ``gain_type``."""
    for r in rules.get("rules", []):
        if r.get("gain_type") == gain_type:
            return dict(r)
    return None


def _find_slab(slabs: list[dict], income: float) -> dict:
    """Return the income-tax slab that covers ``income``."""
    for s in slabs:
        lo = s["min_income"]
        hi = s.get("max_income")
        if hi is None:
            if income >= lo:
                return dict(s)
        elif lo <= income < hi:
            return dict(s)
    return dict(slabs[-1])


def _build_rule_description(rule: dict, slab_rate: float | None = None) -> str:
    """Human-readable rule description including the Budget citation."""
    rid = rule["id"]
    asset = rule.get("asset_class", "")
    exempt = rule.get("exemption", 0)
    if slab_rate is not None:
        return (
            f"{rid} — {asset} at slab rate {slab_rate * 100:.0f}% "
            f"(Budget 2024)"
        )
    if exempt > 0:
        return (
            f"{rid} — {asset} {rule['rate'] * 100:.0f}% "
            f"over \u20b9{exempt:,} exempt (Budget 2024)"
        )
    return (
        f"{rid} — {asset} {rule['rate'] * 100:.0f}% flat "
        f"(Budget 2024)"
    )


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------


class TaxRuleTool(BaseTool[TaxInput, TaxOutput]):
    """Deterministic Indian capital gains tax calculator (FY 2024-25).

    Rules are loaded from ``data/tax_rules.json`` once at init.  Every
    ``run()`` step-by-step computes the tax and populates ``breakdown``
    with each component.  No external API — always available.
    """

    name = "tax_rule"
    ttl_seconds = 3600  # contract: tax/profile = 3600s
    rate_per_sec = 5.0  # contract: ≤ 10 req/s

    def __init__(self, audit: AuditTrail | None = None) -> None:
        super().__init__(audit=audit)
        self._rules: dict = _load_rules()

    # -- BaseTool ----------------------------------------------------------

    def _run(self, inp: TaxInput) -> TaxOutput:
        # Fail loud on negative gain (FM-11)
        if inp.gain < 0:
            raise ToolError(
                f"Negative gain ({inp.gain}) is not allowed. "
                "Capital gains must be non-negative."
            )

        rule = _find_rule(self._rules, inp.gain_type)
        if rule is None:
            raise ToolError(
                f"Unknown gain_type '{inp.gain_type}'. "
                "Valid types: LTCG, STCG, STCG_EQUITY."
            )

        slabs: list[dict] = self._rules.get("income_tax_slabs", [])

        # -- Step 1: taxable gain (after exemption) ------------------------
        exemption = rule.get("exemption", 0)
        taxable_gain = max(0.0, inp.gain - exemption)

        # -- Step 2: base tax ----------------------------------------------
        slab_rate: float | None = None
        raw_rate = rule.get("rate")
        if raw_rate is not None:
            rate = float(raw_rate)
        else:
            slab = _find_slab(slabs, inp.annual_income)
            slab_rate = float(slab["rate"])
            rate = slab_rate

        base_tax = round(taxable_gain * rate, 2)

        # -- Step 3: surcharge (if income > threshold) ---------------------
        surcharge = 0.0
        surcharge_threshold = rule.get("surcharge_threshold", float("inf"))
        surcharge_rate_val = rule.get("surcharge_rate", 0.0)
        if inp.annual_income > surcharge_threshold and surcharge_rate_val > 0:
            surcharge = round(base_tax * surcharge_rate_val, 2)

        # -- Step 4: health & education cess -------------------------------
        cess_amount = 0.0
        if inp.cess:
            cess_rate_val = rule.get("cess_rate", 0.0)
            cess_amount = round((base_tax + surcharge) * cess_rate_val, 2)

        total = round(base_tax + surcharge + cess_amount, 2)

        effective_rate = (
            round(total / inp.gain * 100, 4) if inp.gain > 0 else 0.0
        )

        meta = self._rules.get("metadata", {})
        return TaxOutput(
            tax_amount=total,
            effective_rate_pct=effective_rate,
            breakdown={
                "taxable_gain": taxable_gain,
                "base_tax": base_tax,
                "surcharge": surcharge,
                "cess": cess_amount,
            },
            rule_applied=_build_rule_description(rule, slab_rate=slab_rate),
            citation=(
                f"Income Tax Act 1961 via Finance Act 2024 \u2014 "
                f"FY {meta.get('financial_year', '2024-25')}, "
                f"regime: {meta.get('regime', 'new')}"
            ),
        )


__all__ = [
    "TaxInput",
    "TaxOutput",
    "TaxRuleTool",
    "ToolError",
]
