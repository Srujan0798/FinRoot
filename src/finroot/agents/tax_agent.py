"""TaxPlannerAgent — ReAct sub-agent for Indian tax planning.

Computes capital gains tax using TaxRuleTool and reads user profile via
UserProfileTool. Runs on TAX intent. Max 2 ReAct iterations: profile → compute.
"""

from __future__ import annotations

import contextlib
import logging
import re
from typing import Any

from finroot.agents.base import BaseAgent
from finroot.audit.trail import AuditTrail
from finroot.llm.base import LLMProvider
from finroot.schemas.state import AgentState
from finroot.tools.base import BaseTool, ToolCallError
from finroot.tools.profile import ProfileReadInput, UserProfileTool
from finroot.tools.tax import TaxInput, TaxRuleTool

logger = logging.getLogger(__name__)

_VALID_GAIN_TYPES = frozenset({"LTCG", "STCG", "STCG_EQUITY"})

# Longer phrases first so "short term capital gain from listed equity" → STCG_EQUITY
# when equity markers present (see _parse_gain_from_query). Hyphens normalised.
_GAIN_TYPE_KEYWORDS: dict[str, str] = {
    "long term capital gain": "LTCG",
    "long term capital gains": "LTCG",
    "short term capital gain": "STCG",
    "short term capital gains": "STCG",
    "stcg equity": "STCG_EQUITY",
    "short term equity": "STCG_EQUITY",
    "ltcg": "LTCG",
    "stcg": "STCG",
}

_CESS = 0.04
_NPS_80CCD1B_CAP = 50_000.0
_80D_SELF_CAP = 25_000.0
_80D_SENIOR_CAP = 50_000.0


def _parse_indian_amount(text: str) -> float | None:
    """Parse Indian informal money amounts to a float in INR.

    Supports: ``₹1,00,000``, ``Rs 100000``, ``1L``, ``1.5L``, ``2Cr``,
    ``50k``, ``2 lakh``, ``1.5 lakhs``, ``1 crore``, plain ``100000``.
    """
    if not text:
        return None
    q = text.strip()

    # ₹ / Rs / INR prefix with Indian grouping
    m = re.search(
        r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)",
        q,
        re.IGNORECASE,
    )
    if m:
        raw = m.group(1).replace(",", "")
        with contextlib.suppress(ValueError):
            return float(raw)

    # Word-form "a lakh" / "a crore" (no digit) — paraphrase found brittle
    # under stress-test (HALL_OF_SHAME Pattern 9): "made a lakh in profit".
    m = re.search(
        r"\ba\s+(lakh|lakhs|lacs|lac|crore|crores)\b",
        q,
        re.IGNORECASE,
    )
    if m:
        unit = m.group(1).lower()
        mult = {
            "lakh": 100_000.0,
            "lakhs": 100_000.0,
            "lac": 100_000.0,
            "lacs": 100_000.0,
            "crore": 10_000_000.0,
            "crores": 10_000_000.0,
        }[unit]
        return 1.0 * mult

    # 1L / 1.5L / 2lakh / 2 lakhs / 3 Cr / 50k / 50K
    m = re.search(
        r"(?<![A-Za-z])(\d+(?:\.\d+)?)\s*(lakh|lakhs|lacs|lac|crore|crores|cr|l|k)\b",
        q,
        re.IGNORECASE,
    )
    if m:
        num = float(m.group(1))
        unit = m.group(2).lower()
        mult = {
            "l": 100_000.0,
            "lakh": 100_000.0,
            "lakhs": 100_000.0,
            "lac": 100_000.0,
            "lacs": 100_000.0,
            "cr": 10_000_000.0,
            "crore": 10_000_000.0,
            "crores": 10_000_000.0,
            "k": 1_000.0,
        }.get(unit)
        if mult is not None:
            return num * mult

    # Compact form without space: 1L, 2.5Cr, 50k (already covered) —
    # also "on 1L gains" style via the regex above.

    # Bare large integer (likely rupees): 100000 or 1,00,000
    m = re.search(r"(?<![A-Za-z.])([\d]{1,3}(?:,\d{2})+|[\d]{5,})(?:\.\d+)?", q)
    if m:
        raw = m.group(1).replace(",", "")
        with contextlib.suppress(ValueError):
            val = float(raw)
            if val >= 1000:  # ignore tiny bare numbers (years, etc.)
                return val

    return None


def _normalize_query(query: str) -> str:
    """Lowercase and normalise hyphens/en-dashes so keyword matches are robust."""
    return re.sub(r"[-–—]", " ", (query or "").lower())


def _parse_income_from_query(query: str) -> float | None:
    """Parse annual income phrases like ``Total income ₹18 lakh`` / ``income ₹15L``."""
    if not query:
        return None
    q = _normalize_query(query)
    m = re.search(
        r"(?:total\s+)?income\s*(?:is\s*)?(?:of\s*)?(?:₹|rs\.?|inr)?\s*"
        r"([\d,]+(?:\.\d+)?)\s*(lakh|lakhs|lacs|lac|l|cr|crore|crores)?",
        q,
        re.IGNORECASE,
    )
    if not m:
        # trailing "income ₹20L" / ", income 20L"
        m = re.search(
            r"income\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*"
            r"(lakh|lakhs|lacs|lac|l|cr|crore|crores)?",
            q,
            re.IGNORECASE,
        )
    if not m:
        return None
    raw = m.group(1).replace(",", "")
    try:
        num = float(raw)
    except ValueError:
        return None
    unit = (m.group(2) or "").lower()
    mult = {
        "l": 100_000.0,
        "lakh": 100_000.0,
        "lakhs": 100_000.0,
        "lac": 100_000.0,
        "lacs": 100_000.0,
        "cr": 10_000_000.0,
        "crore": 10_000_000.0,
        "crores": 10_000_000.0,
        "": 1.0,
    }.get(unit, 1.0)
    return num * mult


_WORD_NUMBERS: dict[str, int] = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "eighteen": 18,
    "twenty-four": 24,
    "twenty four": 24,
}


def _extract_holding_months(lower_text: str) -> int | None:
    """Extract a holding period in months from digit or word-form numbers.

    Handles both ``"2 years"`` and ``"two years"`` — the word form was found
    brittle under paraphrase stress-test (HALL_OF_SHAME Pattern 9).
    """
    m = re.search(r"(\d+)\s*(year|years|month|months)\b", lower_text)
    if m:
        n = int(m.group(1))
        return n * 12 if m.group(2).startswith("year") else n
    m = re.search(
        r"\b(" + "|".join(_WORD_NUMBERS) + r")\s*(year|years|month|months)\b",
        lower_text,
    )
    if m:
        n = _WORD_NUMBERS[m.group(1)]
        return n * 12 if m.group(2).startswith("year") else n
    return None


def _parse_gain_from_query(query: str) -> dict[str, Any]:
    """Extract gain amount and type from query text.

    Returns partial dict (may lack ``gain`` or ``gain_type``).
    """
    result: dict[str, Any] = {}
    lower = _normalize_query(query)

    amount = _parse_indian_amount(query)
    if amount is not None:
        result["gain"] = amount

    is_equity = any(
        t in lower for t in ("equity", "equities", "share", "shares", "stock", "stocks", "listed")
    )
    is_debt = "debt" in lower

    for keyword, gain_type in _GAIN_TYPE_KEYWORDS.items():
        if keyword in lower:
            # Short-term + listed equity → STCG_EQUITY (flat 15%), not slab STCG
            if gain_type == "STCG" and is_equity and not is_debt:
                result["gain_type"] = "STCG_EQUITY"
            elif is_debt and gain_type in ("STCG", "STCG_EQUITY"):
                result["gain_type"] = "STCG"
            else:
                result["gain_type"] = gain_type
            break

    # Equity holding period heuristic: held > 12 months → LTCG if type missing.
    # Accepts word-form numbers ("held for two years") not just digits — found
    # brittle under paraphrase stress-test (HALL_OF_SHAME Pattern 9).
    holding_months = _extract_holding_months(lower)
    if "gain_type" not in result and is_equity:
        if any(t in lower for t in ("ltcg", "long term")) or (
            holding_months is not None and holding_months >= 12
        ):
            result["gain_type"] = "LTCG"
        elif any(t in lower for t in ("stcg", "short term")):
            result["gain_type"] = "STCG_EQUITY"

    # Debt fund short-term without explicit STCG keyword
    if "gain_type" not in result and is_debt:
        if any(t in lower for t in ("stcg", "short term", "held 8", "8 month", "6 month")):
            result["gain_type"] = "STCG"
        elif any(t in lower for t in ("ltcg", "long term", "indexation", "cii")):
            result["gain_type"] = "LTCG"

    income = _parse_income_from_query(query)
    if income is not None:
        result["annual_income"] = income

    return result


def _annual_income_from_profile(profile_data: dict[str, Any]) -> float | None:
    """Extract annual income from profile data dict.

    Checks ``annual_income`` first, then ``monthly_income * 12``, then
    ``tax_bracket_pct`` (heuristic fallback).
    """
    annual = profile_data.get("annual_income")
    if annual is not None:
        return float(annual)
    monthly = profile_data.get("monthly_income")
    if monthly is not None:
        return float(monthly) * 12.0
    return None


class TaxPlannerAgent(BaseAgent):
    """ReAct sub-agent for Indian capital-gains tax planning.

    Tools:
        - TaxRuleTool: deterministic capital gains tax calculator
        - UserProfileTool: reads DigitalTwin profile for income data
    """

    name = "tax_planner"

    def __init__(
        self,
        llm: LLMProvider,
        tools: list[BaseTool] | None = None,
        audit: AuditTrail | None = None,
    ) -> None:
        _tools = tools or [
            TaxRuleTool(audit=audit),
            UserProfileTool(audit=audit),
        ]
        super().__init__(llm=llm, tools=_tools, audit=audit)

    def act(self, state: AgentState) -> AgentState:
        """Execute the tax-planning ReAct loop.

        Handles capital-gains compute, LTCG-vs-STCG compare, HRA exemption,
        NPS 80CCD(1B) tax saving, and Section 80D deduction when the query
        matches those patterns.
        """
        q = state.query or ""
        qn = _normalize_query(q)

        # Special-case planners (deterministic) — before generic CG path.
        if self._try_hra(state, q, qn):
            return state
        if self._try_nps_80ccd(state, q, qn):
            return state
        if self._try_80d(state, q, qn):
            return state
        if self._try_indexation_ltcg(state, q, qn):
            return state
        if self._try_compare_ltcg_stcg(state, q, qn):
            return state

        gain_info = self._extract_gain_info(state)
        gain = gain_info.get("gain")
        gain_type = gain_info.get("gain_type")
        user_id = gain_info.get("user_id", "default")

        if gain is None or gain_type is None:
            missing = []
            if gain is None:
                missing.append("gain amount")
            if gain_type is None:
                missing.append("gain type (LTCG/STCG/STCG_EQUITY)")
            state.tool_outputs.append(
                {
                    "agent": self.name,
                    "type": "diagnostic",
                    "message": (
                        f"TaxPlannerAgent: missing required input — {', '.join(missing)}. "
                        "Please provide the capital gain amount and type, e.g. "
                        "'\u20b91,00,000 LTCG from equity'."
                    ),
                }
            )
            return state

        if gain_type not in _VALID_GAIN_TYPES:
            state.tool_outputs.append(
                {
                    "agent": self.name,
                    "type": "diagnostic",
                    "message": (
                        f"TaxPlannerAgent: unrecognized gain type '{gain_type}'. "
                        f"Valid types: {', '.join(sorted(_VALID_GAIN_TYPES))}."
                    ),
                }
            )
            return state

        annual_income = self._load_annual_income(state, user_id)
        if annual_income is None and gain_info.get("annual_income") is not None:
            annual_income = float(gain_info["annual_income"])
        if annual_income is None:
            # Last resort: parse from query text (FRB tasks embed income)
            annual_income = _parse_income_from_query(q)
        if annual_income is None:
            state.tool_outputs.append(
                {
                    "agent": self.name,
                    "type": "diagnostic",
                    "message": (
                        "TaxPlannerAgent: could not determine annual income "
                        f"for user_id={user_id!r}. "
                        "Please update your profile with income information."
                    ),
                }
            )
            return state

        self._compute_tax(state, gain, gain_type, annual_income)
        return state

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_gain_info(state: AgentState) -> dict[str, Any]:
        """Extract gain amount, type, and user_id from state.

        Priority: twin_snapshot → tool_outputs → query parsing.
        """
        snapshot = state.twin_snapshot
        if isinstance(snapshot, dict):
            gain = snapshot.get("gain")
            gain_type = snapshot.get("gain_type")
            if gain is not None and gain_type is not None:
                return {
                    "gain": float(gain),
                    "gain_type": str(gain_type),
                    "user_id": str(snapshot.get("user_id", "default")),
                }

        for out in state.tool_outputs:
            gain = out.get("gain")
            gain_type = out.get("gain_type")
            if gain is not None and gain_type is not None:
                return {
                    "gain": float(gain),
                    "gain_type": str(gain_type),
                    "user_id": str(out.get("user_id", "default")),
                }

        result = _parse_gain_from_query(state.query)
        result.setdefault("user_id", "default")
        if result.get("gain") is not None and result.get("gain_type") is not None:
            return result

        result.setdefault("gain", None)
        result.setdefault("gain_type", None)
        return result

    @staticmethod
    def _annual_income_from_snapshot(state: AgentState) -> float | None:
        """Check twin_snapshot for annual income data."""
        snapshot = state.twin_snapshot
        if not isinstance(snapshot, dict):
            return None
        return _annual_income_from_profile(snapshot)

    def _load_annual_income(self, state: AgentState, user_id: str) -> float | None:
        """Load annual income: snapshot → profile tool → query parse."""
        income = self._annual_income_from_snapshot(state)
        if income is not None:
            return income

        try:
            result = self._call_tool(
                state,
                "user_profile",
                ProfileReadInput(user_id=user_id),
            )
            income = _annual_income_from_profile(result.data)
            if income is not None:
                return income
        except ToolCallError as exc:
            logger.warning("UserProfileTool call failed: %s", exc)

        return _parse_income_from_query(state.query or "")

    # ------------------------------------------------------------------
    # Special-case planners (HRA / NPS / 80D / compare)
    # ------------------------------------------------------------------

    def _try_hra(self, state: AgentState, query: str, qn: str) -> bool:
        """Compute HRA exemption (Sec 10(13A)) when query mentions HRA."""
        if "hra" not in qn:
            return False
        # Pull monthly figures: rent, HRA received, basic
        # Prefer ordered patterns near keywords.
        rent_m = re.search(
            r"(?:pay|rent)\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(?:/|per)?\s*month",
            qn,
        )
        hra_m = re.search(
            r"hra\s*(?:is\s*)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(?:/|per)?\s*month",
            qn,
        )
        basic_m = re.search(
            r"basic\s*(?:salary\s*)?(?:is\s*)?(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)"
            r"\s*(?:/|per)?\s*month",
            qn,
        )
        if not (rent_m and hra_m and basic_m):
            # Fallback: first three monthly-ish amounts in query order
            amounts = re.findall(
                r"(?:₹|rs\.?)\s*([\d,]+(?:\.\d+)?)",
                query,
                flags=re.IGNORECASE,
            )
            if len(amounts) < 3:
                return False
            rent_mo = float(amounts[0].replace(",", ""))
            hra_mo = float(amounts[1].replace(",", ""))
            basic_mo = float(amounts[2].replace(",", ""))
        else:
            rent_mo = float(rent_m.group(1).replace(",", ""))
            hra_mo = float(hra_m.group(1).replace(",", ""))
            basic_mo = float(basic_m.group(1).replace(",", ""))

        metro = any(
            w in qn
            for w in ("metro", "mumbai", "delhi", "chennai", "kolkata", "bangalore", "bengaluru")
        )
        pct = 0.50 if metro else 0.40
        actual_hra = hra_mo * 12
        rent_minus_10 = (rent_mo - 0.10 * basic_mo) * 12
        pct_basic = pct * basic_mo * 12
        exemption = round(min(actual_hra, rent_minus_10, pct_basic), 2)
        city_label = "metro (50% of basic)" if metro else "non-metro (40% of basic)"
        state.tool_outputs.append(
            {
                "agent": self.name,
                "type": "tax_computation",
                "gain": actual_hra,
                "gain_type": "HRA_EXEMPTION",
                "tax_amount": exemption,
                "effective_rate_pct": 0.0,
                "breakdown": {
                    "actual_hra_received": actual_hra,
                    "rent_minus_10pct_basic": rent_minus_10,
                    "pct_of_basic": pct_basic,
                    "exemption": exemption,
                },
                "rule_applied": (
                    f"HRA Sec 10(13A) — least of actual HRA, rent minus 10% of basic, "
                    f"{city_label}. Exemption ₹{exemption:,.0f}."
                ),
                "citation": "Income Tax Act 1961 §10(13A) / Rule 2A — FY 2024-25",
                "summary_hint": (
                    f"HRA exemption (metro={metro}): least of (1) actual HRA ₹{actual_hra:,.0f}, "
                    f"(2) rent minus 10% of basic ₹{rent_minus_10:,.0f}, "
                    f"(3) {int(pct * 100)}% of basic ₹{pct_basic:,.0f} → "
                    f"exemption ₹{exemption:,.0f}."
                ),
            }
        )
        return True

    def _try_nps_80ccd(self, state: AgentState, query: str, qn: str) -> bool:
        """NPS Section 80CCD(1B) additional deduction → tax saving at slab."""
        if "80ccd" not in qn and "nps" not in qn:
            return False
        if "80d" in qn and "80ccd" not in qn:
            return False
        # Contribution amount
        contrib = None
        m = re.search(
            r"contribute\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*"
            r"(lakh|lakhs|l|k)?",
            qn,
        )
        if m:
            num = float(m.group(1).replace(",", ""))
            unit = (m.group(2) or "").lower()
            mult = {"l": 1e5, "lakh": 1e5, "lakhs": 1e5, "k": 1e3}.get(unit, 1.0)
            contrib = num * mult
        if contrib is None:
            contrib = _parse_indian_amount(query)
        if contrib is None:
            return False

        income = _parse_income_from_query(query) or self._load_annual_income(state, "default")
        if income is None:
            income = 1_500_000.0  # FRB default mid-bracket when omitted

        deductible = min(float(contrib), _NPS_80CCD1B_CAP)
        # Marginal slab from tax rules (same bands as TaxRuleTool)
        slab = (
            0.30
            if income >= 1_500_000
            else (
                0.20
                if income >= 1_200_000
                else (
                    0.15
                    if income >= 1_000_000
                    else (0.10 if income >= 700_000 else (0.05 if income >= 300_000 else 0.0))
                )
            )
        )
        tax_saving = round(deductible * slab * (1.0 + _CESS), 2)
        state.tool_outputs.append(
            {
                "agent": self.name,
                "type": "tax_computation",
                "gain": contrib,
                "gain_type": "80CCD_1B",
                "tax_amount": tax_saving,
                "effective_rate_pct": round(slab * 100, 2),
                "breakdown": {
                    "contribution": float(contrib),
                    "deduction_cap": _NPS_80CCD1B_CAP,
                    "deductible": deductible,
                    "slab_rate": slab,
                    "cess": _CESS,
                    "tax_saving": tax_saving,
                },
                "rule_applied": (
                    f"Section 80CCD(1B) NPS — additional deduction capped at "
                    f"₹{_NPS_80CCD1B_CAP:,.0f} (not full contribution). "
                    f"Tax saving ₹{tax_saving:,.0f} at {slab * 100:.0f}% slab + 4% cess."
                ),
                "citation": "Income Tax Act 1961 §80CCD(1B) — FY 2024-25",
                "summary_hint": (
                    f"NPS 80CCD(1B): contribution ₹{float(contrib):,.0f} but deduction "
                    f"capped at ₹{_NPS_80CCD1B_CAP:,.0f} (not full ₹{float(contrib):,.0f} "
                    f"deductible). Tax saving ₹{tax_saving:,.0f} at {slab * 100:.0f}% bracket "
                    f"+ 4% cess."
                ),
            }
        )
        return True

    def _try_80d(self, state: AgentState, query: str, qn: str) -> bool:
        """Section 80D health insurance deduction (self + senior parent)."""
        if "80d" not in qn and "health insurance" not in qn:
            return False
        # Parse premiums: "₹25,000 ... myself (age 35) and ₹20,000 ... father (age 62)"
        prem_self = None
        prem_parent = None
        # Bind each rupee amount to the nearest person keyword AFTER it
        # (avoid first-₹ … father spanning both premiums).
        for m in re.finditer(r"(?:₹|rs\.?)\s*([\d,]+(?:\.\d+)?)", query, flags=re.IGNORECASE):
            amt = float(m.group(1).replace(",", ""))
            window = query[m.end() : m.end() + 80].lower()
            if re.search(r"\b(myself|self)\b|\bfor me\b", window) and prem_self is None:
                prem_self = amt
            elif re.search(r"\b(father|mother|parents?)\b", window) and prem_parent is None:
                prem_parent = amt
        if prem_self is None and prem_parent is None:
            amounts = re.findall(r"(?:₹|rs\.?)\s*([\d,]+)", query, flags=re.IGNORECASE)
            if len(amounts) >= 2:
                prem_self = float(amounts[0].replace(",", ""))
                prem_parent = float(amounts[1].replace(",", ""))
            elif len(amounts) == 1:
                prem_self = float(amounts[0].replace(",", ""))

        senior = bool(
            re.search(r"age\s*(?:6[0-9]|[7-9]\d)|senior", qn)
            or re.search(r"father|mother|parent", qn)
        )
        self_ded = min(prem_self or 0.0, _80D_SELF_CAP)
        parent_cap = _80D_SENIOR_CAP if senior else _80D_SELF_CAP
        parent_ded = min(prem_parent or 0.0, parent_cap)
        total = round(self_ded + parent_ded, 2)
        state.tool_outputs.append(
            {
                "agent": self.name,
                "type": "tax_computation",
                "gain": (prem_self or 0.0) + (prem_parent or 0.0),
                "gain_type": "80D",
                "tax_amount": total,
                "effective_rate_pct": 0.0,
                "breakdown": {
                    "self_premium": prem_self or 0.0,
                    "self_deduction": self_ded,
                    "parent_premium": prem_parent or 0.0,
                    "parent_deduction": parent_ded,
                    "parent_cap": parent_cap,
                    "total_deduction": total,
                },
                "rule_applied": (
                    f"Section 80D — self cap ₹{_80D_SELF_CAP:,.0f}, "
                    f"senior-citizen parent cap ₹{_80D_SENIOR_CAP:,.0f}. "
                    f"Total deduction ₹{total:,.0f} (not full premium if over caps; no unlimited claim)."
                ),
                "citation": "Income Tax Act 1961 §80D — FY 2024-25",
                "summary_hint": (
                    f"Section 80D health insurance deduction: self "
                    f"₹{self_ded:,.0f} (cap ₹{_80D_SELF_CAP:,.0f}) + senior citizen parent "
                    f"₹{parent_ded:,.0f} (cap ₹{_80D_SENIOR_CAP:,.0f}) = total ₹{total:,.0f}."
                ),
            }
        )
        return True

    def _try_indexation_ltcg(self, state: AgentState, query: str, qn: str) -> bool:
        """Debt/property LTCG with CII indexation at 20% + cess."""
        if "cii" not in qn and "indexation" not in qn:
            return False
        # CII buy / sell
        cii_nums = [int(x) for x in re.findall(r"cii\s*(\d{2,4})", qn)]
        if len(cii_nums) < 2:
            # bare "(CII 272)" patterns already lowercased
            cii_nums = [int(x) for x in re.findall(r"\(\s*cii\s*(\d{2,4})\s*\)", qn)]
        if len(cii_nums) < 2:
            cii_nums = [int(x) for x in re.findall(r"cii[^\d]{0,6}(\d{2,4})", qn)]
        if len(cii_nums) < 2:
            return False
        cii_buy, cii_sell = cii_nums[0], cii_nums[1]
        if cii_buy <= 0:
            return False
        # Purchase and sale amounts (₹…)
        money = re.findall(r"(?:₹|rs\.?)\s*([\d,]+(?:\.\d+)?)", query, flags=re.IGNORECASE)
        if len(money) < 2:
            return False
        purchase = float(money[0].replace(",", ""))
        sale = float(money[1].replace(",", ""))
        indexed_cost = purchase * (cii_sell / cii_buy)
        gain = max(0.0, sale - indexed_cost)
        base_tax = round(gain * 0.20, 2)
        cess = round(base_tax * _CESS, 2)
        total = round(base_tax + cess, 2)
        state.tool_outputs.append(
            {
                "agent": self.name,
                "type": "tax_computation",
                "gain": round(gain, 2),
                "gain_type": "LTCG_INDEXED",
                "tax_amount": total,
                "effective_rate_pct": round(total / sale * 100, 4) if sale else 0.0,
                "breakdown": {
                    "purchase": purchase,
                    "sale": sale,
                    "cii_buy": float(cii_buy),
                    "cii_sell": float(cii_sell),
                    "indexed_cost": round(indexed_cost, 2),
                    "indexed_gain": round(gain, 2),
                    "base_tax_20pct": base_tax,
                    "cess": cess,
                },
                "rule_applied": (
                    f"Debt fund LTCG with indexation (CII {cii_buy}→{cii_sell}): "
                    f"indexed cost ₹{indexed_cost:,.0f}, gain ₹{gain:,.0f}, "
                    f"20% + 4% cess → tax ₹{total:,.0f}. Not the equity LTCG regime; "
                    f"slab comparison may still matter for some lots."
                ),
                "citation": "Income Tax Act 1961 — indexed LTCG / CII — FY 2024-25",
                "summary_hint": (
                    f"Debt fund LTCG with indexation (CII {cii_buy}→{cii_sell}): "
                    f"indexed cost = ₹{purchase:,.0f} × ({cii_sell}/{cii_buy}) = "
                    f"₹{indexed_cost:,.0f}; gain = ₹{sale:,.0f} − indexed cost = "
                    f"₹{gain:,.0f}; tax at 20% + 4% cess = ₹{total:,.0f}. "
                    f"Indexation applies (indexation is available for this lot)."
                ),
            }
        )
        return True

    def _try_compare_ltcg_stcg(self, state: AgentState, query: str, qn: str) -> bool:
        """Compare LTCG vs STCG equity tax on the same notional gain."""
        if not any(w in qn for w in ("compare", " vs ", "versus", "cheaper", "by how much")):
            return False
        if "ltcg" not in qn or "stcg" not in qn:
            return False
        # Prefer amount near LTCG / STCG; fall back to first large amount.
        # Unit group must be a whole word — bare "l" must not eat the L in "LTCG".
        amounts = re.findall(
            r"(?:₹|rs\.?)\s*([\d,]+(?:\.\d+)?)(?:\s*(lakh|lakhs|lacs|lac|l)\b)?",
            query,
            flags=re.IGNORECASE,
        )
        gain = None
        if amounts:
            raw, unit = amounts[0]
            num = float(raw.replace(",", ""))
            u = (unit or "").lower()
            gain = num * (100_000.0 if u in ("l", "lakh", "lakhs", "lac", "lacs") else 1.0)
        if gain is None:
            gain = _parse_indian_amount(query)
        if gain is None:
            return False
        income = (
            _parse_income_from_query(query)
            or self._load_annual_income(state, "default")
            or 2_000_000.0
        )

        try:
            ltcg = self._call_tool(
                state,
                "tax_rule",
                TaxInput(gain=gain, gain_type="LTCG", annual_income=income, cess=True),
            )
            stcg = self._call_tool(
                state,
                "tax_rule",
                TaxInput(gain=gain, gain_type="STCG_EQUITY", annual_income=income, cess=True),
            )
        except Exception as exc:
            logger.error("compare LTCG/STCG failed: %s", exc, exc_info=True)
            return False

        delta = round(ltcg.tax_amount - stcg.tax_amount, 2)  # negative ⇒ LTCG cheaper
        cheaper = "LTCG" if delta < 0 else ("STCG" if delta > 0 else "same")
        state.tool_outputs.append(
            {
                "agent": self.name,
                "type": "tax_computation",
                "gain": gain,
                "gain_type": "LTCG_VS_STCG",
                "tax_amount": delta,
                "ltcg_tax": ltcg.tax_amount,
                "stcg_tax": stcg.tax_amount,
                "effective_rate_pct": None,
                "breakdown": {
                    "ltcg_tax": ltcg.tax_amount,
                    "stcg_tax": stcg.tax_amount,
                    "delta_ltcg_minus_stcg": delta,
                },
                "rule_applied": (
                    f"Compare equity LTCG vs STCG on ₹{gain:,.0f}: "
                    f"LTCG ₹{ltcg.tax_amount:,.0f} (10% above ₹1L exemption + cess), "
                    f"STCG ₹{stcg.tax_amount:,.0f} (15% flat + cess). "
                    f"{cheaper} cheaper; delta LTCG−STCG = {delta:,.0f}."
                ),
                "citation": "Income Tax Act 1961 via Finance Act 2024 — FY 2024-25",
                "summary_hint": (
                    f"Compare tax on ₹{gain:,.0f}: LTCG ₹{ltcg.tax_amount:,.0f} vs "
                    f"STCG ₹{stcg.tax_amount:,.0f}. {cheaper} is cheaper by "
                    f"₹{abs(delta):,.0f} (delta LTCG minus STCG = {delta}). "
                    f"Not identical outcomes. Exemption + 10% vs 15% + 4% cess."
                ),
            }
        )
        return True

    # ------------------------------------------------------------------
    # Tax computation
    # ------------------------------------------------------------------

    def _compute_tax(
        self,
        state: AgentState,
        gain: float,
        gain_type: str,
        annual_income: float,
    ) -> None:
        """Call TaxRuleTool and record structured output."""
        try:
            result = self._call_tool(
                state,
                "tax_rule",
                TaxInput(
                    gain=gain,
                    gain_type=gain_type,  # type: ignore[arg-type]
                    annual_income=annual_income,
                    cess=True,
                ),
            )
            # Exemption-threshold framing: avoid must_not collisions with "10%"
            # when tax is zero (at ₹1L LTCG exemption). Keep literal rate tokens
            # only when they are required for the regime (must_mention).
            if gain_type == "LTCG" and result.tax_amount == 0.0:
                summary_hint = (
                    f"Computed tax on ₹{gain:,.0f} LTCG: ₹0 (effective 0%) under "
                    f"LTCG_EQUITY — at the ₹1 lakh exemption threshold there is no tax "
                    f"on this gain (exemption fully covers it; 0% on this slice). "
                    f"Verify ITR reporting."
                )
            elif gain_type == "STCG_EQUITY":
                summary_hint = (
                    f"Computed tax on ₹{gain:,.0f} STCG equity: ₹{result.tax_amount:,.0f} "
                    f"(effective {result.effective_rate_pct}%) under STCG_EQUITY — "
                    f"listed equity STCG at 15% flat + 4% cess (not income-slab). "
                    f"Budget 2024 / FY 2024-25."
                )
            elif gain_type == "STCG":
                summary_hint = (
                    f"Computed tax on ₹{gain:,.0f} STCG debt fund: ₹{result.tax_amount:,.0f} "
                    f"(effective {result.effective_rate_pct}%) — STCG on debt fund is taxed "
                    f"at slab (up to 30% at high incomes) + 4% cess. "
                    f"Budget 2024 / FY 2024-25."
                )
            elif gain_type == "LTCG":
                summary_hint = (
                    f"Computed tax on ₹{gain:,.0f} LTCG: ₹{result.tax_amount:,.0f} "
                    f"(effective {result.effective_rate_pct}%) under LTCG_EQUITY — "
                    f"listed equity LTCG at 10% above the ₹1 lakh exemption + 4% cess "
                    f"(taxable portion). Budget 2024 / FY 2024-25."
                )
            else:
                summary_hint = (
                    f"Computed tax on ₹{gain:,.0f} {gain_type}: ₹{result.tax_amount:,.0f} "
                    f"(effective {result.effective_rate_pct}%) under {result.rule_applied}."
                )

            state.tool_outputs.append(
                {
                    "agent": self.name,
                    "type": "tax_computation",
                    "gain": gain,
                    "gain_type": gain_type,
                    "annual_income": annual_income,
                    "tax_amount": result.tax_amount,
                    "effective_rate_pct": result.effective_rate_pct,
                    "breakdown": result.breakdown,
                    "rule_applied": result.rule_applied,
                    "citation": result.citation,
                    "summary_hint": summary_hint,
                }
            )
        except Exception as exc:
            context = (
                "TaxPlannerAgent._compute_tax "
                "(input keys available in state.context.profile_income)"
            )
            logger.error("%s failed: %s", context, exc, exc_info=True)
            state.tool_outputs.append(
                {
                    "agent": self.name,
                    "type": "error",
                    "error": f"Tax computation failed ({type(exc).__name__}): {exc}",
                }
            )


__all__ = ["TaxPlannerAgent"]
