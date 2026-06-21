"""Rooted Prudence Principles — the 'do no harm' gate (wave-5, task 03).

A checklist of 7 financial safety principles. Checks 1-4 and 7 are critical
(all must pass for ``compliant=True``); checks 5-6 are warnings only.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

from finroot.schemas.state import AgentState

# ---------------------------------------------------------------------------
# Pydantic models (contract §3)
# ---------------------------------------------------------------------------

class PrudentialVerdict(BaseModel):
    """Result of the prudence checklist."""

    compliant: bool
    checks: list[dict[str, Any]]
    warning: str | None = None


# ---------------------------------------------------------------------------
# Patterns (compiled once, case-insensitive)
# ---------------------------------------------------------------------------

_EMERGENCY_FUND_RE = re.compile(
    r"emergency\s*(?:fund|savings|reserve|cash)|rainy[- ]?day\s*fund",
    re.IGNORECASE,
)
_INVEST_VERB_RE = re.compile(
    r"\b(?:invest|put|move|transfer|allocate|deploy|use)\b.*?\b(?:in|into|to|for)\b",
    re.IGNORECASE,
)
# Proximity pattern: an invest verb acting *on* the emergency fund. Matches
# "put my entire emergency fund", "invest the emergency savings", or
# "emergency fund into <asset>" — but NOT protective advice like
# "before investing, keep 6 months in your emergency fund" (verb far from fund,
# or "in" precedes the fund rather than following it).
_EMERGENCY_FUND_INVEST_RE = re.compile(
    r"\b(?:invest|put|move|transfer|allocate|deploy|dump|pour)\w*\s+"
    r"(?:my\s+|the\s+|all\s+|entire\s+|whole\s+|a\s+)*"
    r"(?:\w+\s+){0,2}?emergency\s*(?:fund|savings|reserve|cash)"
    r"|emergency\s*(?:fund|savings|reserve|cash)\s+(?:\w+\s+){0,2}?(?:into|in\s+(?:a|an|the|some|stock|equit|small|crypto))",
    re.IGNORECASE,
)

_PERCENT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")
# A percentage only counts as a concentration signal when near allocation words.
_ALLOCATION_CONTEXT_RE = re.compile(
    r"\b(?:allocat[eion]|portfolio|weight|holding|concentrat|single\s+(?:stock|asset)|"
    r"in\s+(?:one|a\s+single)|exposure|invest(?:ed|ing)?\s+\d|put\s+\d)\b",
    re.IGNORECASE,
)
# …but never when it's clearly a tax/rate/exemption figure.
_NON_ALLOCATION_CONTEXT_RE = re.compile(
    r"\b(?:tax|cess|ltcg|stcg|slab|exemption|hra|surcharge|rate|gst|tds|"
    r"interest|yield|coupon|inflation|of\s+basic|return\s+of)\b",
    re.IGNORECASE,
)

_GUARANTEE_RE = re.compile(
    r"\b(?:guarantee[ds]?|will\s+definitely|promise[sd]?|certain\s+to|"
    r"risk[- ]?free|can't\s+lose|cannot\s+lose)\b",
    re.IGNORECASE,
)
_NEGATION_BEFORE_GUARANTEE_RE = re.compile(
    r"\b(?:does\s+not|doesn't|don't|no|not|never)\s+\w*\s*guarantee|"
    r"""['"]guarantee[ds]?['"]|"""
    r"(?:not|never)\s+guarantee",
    re.IGNORECASE,
)

_SELL_RE = re.compile(r"\b(?:sell|liquidat|exit|close\s+out)\b", re.IGNORECASE)
_TAX_RE = re.compile(r"\b(?:tax|capital\s+gain|loss\s+harvest|tax[- ]?loss)\b", re.IGNORECASE)

_SHORT_TERM_RE = re.compile(
    r"\b(?:short[- ]?term|day[- ]?trad\w*|swing[- ]?trad\w*|quick\s+(?:profit|gain|flip)|"
    r"in\s+and\s+out|within\s+(?:days?|weeks?))\b",
    re.IGNORECASE,
)

_CONSERVATIVE_RE = re.compile(
    r"\b(?:conservative|low[- ]?risk|safe|stable|capital\s+preservation|defensive)\b",
    re.IGNORECASE,
)
_AGGRESSIVE_RE = re.compile(
    r"\b(?:aggressive|high[- ]?risk|speculative|volatile|leverag|penny\s+stock|"
    r"all[- ]?in|yolo|meme\s+stock)\b",
    re.IGNORECASE,
)

_LONG_HORIZON_RE = re.compile(
    r"\b(?:long[- ]?term|long[- ]?horizon|10\s*(?:\+|plus)\s*year|decade|retire|retirement)\b",
    re.IGNORECASE,
)

# Thresholds
_MAX_SINGLE_ASSET_PCT = 40.0
_MIN_TOOL_OUTPUTS = 2


# ---------------------------------------------------------------------------
# PrudentialVerifier
# ---------------------------------------------------------------------------

class PrudentialVerifier:
    """Financial prudence checklist — the 'do no harm' gate."""

    def verify(self, state: AgentState) -> PrudentialVerdict:
        """Run all 7 checks against the current state and return a verdict."""

        text = self._extract_text(state)
        twin = state.twin_snapshot
        tool_count = len(state.tool_outputs)

        checks: list[dict[str, Any]] = []

        # 1. Emergency fund (critical) — check the recommendation AND the query
        #    separately so a query that *proposes* investing the fund is caught,
        #    without cross-contaminating protective advice.
        checks.append(self._check_emergency_fund(text, state.query))
        # 2. Diversification (critical)
        checks.append(self._check_diversification(text, state.query))
        # 3. Risk match (critical)
        checks.append(self._check_risk_match(text, twin))
        # 4. No guarantees (critical)
        checks.append(self._check_no_guarantees(text))
        # 5. Tax awareness (warning)
        checks.append(self._check_tax_awareness(text))
        # 6. Horizon match (warning)
        checks.append(self._check_horizon_match(text, twin))
        # 7. Insufficient evidence (critical)
        checks.append(self._check_evidence(tool_count, text))

        critical_indices = {0, 1, 2, 3, 6}
        compliant = all(
            c["pass"] for i, c in enumerate(checks) if i in critical_indices
        )

        warning = None
        if not compliant:
            warning = "This advice may not be suitable for your profile"

        return PrudentialVerdict(
            compliant=compliant,
            checks=checks,
            warning=warning,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_text(state: AgentState) -> str:
        """Extract the recommendation text (summary) from candidate or final.
        
        Only checks the summary (actual advice given to user), not the analysis
        (educational context). The analysis may contain words like "speculative"
        in a descriptive/educational sense, not as advice.
        """
        rec = state.candidate or state.final
        if rec is None:
            return state.query
        return getattr(rec, "summary", "") or str(rec)

    @staticmethod
    def _check_emergency_fund(text: str, query: str = "") -> dict[str, Any]:
        # Check the recommendation text and the user's query *separately* with a
        # proximity pattern (invest verb acting on the fund) so we catch a query
        # that proposes the violation without false-positiving on protective
        # advice that merely mentions keeping an emergency fund.
        failed_rec = _EMERGENCY_FUND_INVEST_RE.search(text) is not None
        failed_query = bool(query) and _EMERGENCY_FUND_INVEST_RE.search(query) is not None
        failed = failed_rec or failed_query
        return {
            "principle": "Emergency fund first",
            "pass": not failed,
            "detail": (
                "Answer recommends investing emergency fund"
                if failed_rec
                else (
                    "Query proposes investing the emergency fund — agent must refuse / caveat"
                    if failed_query
                    else "No emergency-fund violation detected"
                )
            ),
        }

    @staticmethod
    def _check_diversification(text: str, query: str = "") -> dict[str, Any]:
        """Detect allocation >40% to a single asset.

        Only checks the recommendation text (not the user's query) to avoid
        false positives when the user describes their current allocation.
        """
        # Remove query text from the recommendation text to avoid false positives
        # when the user describes their current allocation (e.g., "80% in one stock").
        rec_text = text
        if query and query in rec_text:
            rec_text = rec_text.replace(query, "")

        failed = False
        detail = "No concentration violation detected"
        # Only flag a >40% figure when it sits in an ALLOCATION context. Tax
        # answers are full of non-allocation percentages (rates, exemptions,
        # cess, HRA "50% of basic") that must NOT trip the concentration gate.
        for m in _PERCENT_RE.finditer(rec_text):
            pct = float(m.group(1))
            if pct <= _MAX_SINGLE_ASSET_PCT:
                continue
            window = rec_text[max(0, m.start() - 45): m.end() + 45].lower()
            if _ALLOCATION_CONTEXT_RE.search(window) and not _NON_ALLOCATION_CONTEXT_RE.search(window):
                failed = True
                detail = f"Recommends {pct}% allocation to single asset (>40% limit)"
                break
        return {
            "principle": "Diversification",
            "pass": not failed,
            "detail": detail,
        }

    @staticmethod
    def _check_risk_match(text: str, twin: dict) -> dict[str, Any]:
        """Fail if user is conservative but advice is aggressive."""
        risk_tolerance = twin.get("risk_tolerance", "").lower()
        user_conservative = risk_tolerance in ("conservative", "low", "very_low")

        advice_aggressive = bool(_AGGRESSIVE_RE.search(text))
        failed = user_conservative and advice_aggressive

        return {
            "principle": "Risk match",
            "pass": not failed,
            "detail": (
                f"Conservative investor (risk_tolerance={risk_tolerance!r}) "
                "received aggressive advice"
                if failed
                else "Advice risk level is compatible with user profile"
            ),
        }

    @staticmethod
    def _check_no_guarantees(text: str) -> dict[str, Any]:
        # Find all guarantee-like terms and check if each is negated.
        # Fail if ANY guarantee term appears without negation nearby.
        failed_terms = []
        for m in _GUARANTEE_RE.finditer(text):
            term = m.group()
            start = m.start()
            # Check if this specific occurrence is negated
            # Look at window before the match for negation words
            window = text[max(0, start - 30):start]
            if _NEGATION_BEFORE_GUARANTEE_RE.search(window):
                continue  # this occurrence is negated
            failed_terms.append(term)

        failed = len(failed_terms) > 0
        return {
            "principle": "No guarantees",
            "pass": not failed,
            "detail": (
                f"Contains non-negated guarantee language: {', '.join(set(failed_terms))!r}"
                if failed
                else "No non-negated guarantee language detected"
            ),
        }

    @staticmethod
    def _check_tax_awareness(text: str) -> dict[str, Any]:
        """WARN (not critical) if sell recommended without tax mention."""
        has_sell = bool(_SELL_RE.search(text))
        has_tax = bool(_TAX_RE.search(text))
        failed = has_sell and not has_tax
        return {
            "principle": "Tax awareness",
            "pass": not failed,
            "detail": (
                "Sell recommendation without tax consideration"
                if failed
                else "Tax considerations present or no sell recommended"
            ),
        }

    @staticmethod
    def _check_horizon_match(text: str, twin: dict) -> dict[str, Any]:
        """WARN if short-term advice for long-horizon investor."""
        horizon = twin.get("horizon", "").lower()
        user_long = horizon in ("long", "long_term", "10+ years", "retirement")

        advice_short = bool(_SHORT_TERM_RE.search(text))
        failed = user_long and advice_short

        return {
            "principle": "Horizon match",
            "pass": not failed,
            "detail": (
                f"Long-horizon investor (horizon={horizon!r}) "
                "received short-term trading advice"
                if failed
                else "Advice horizon is compatible with user profile"
            ),
        }

    @staticmethod
    def _check_evidence(tool_count: int, text: str) -> dict[str, Any]:
        """Fail if tool_outputs < 2 and the answer makes specific financial claims."""
        # Skip evidence check for greetings and informational responses
        is_greeting = any(w in text.lower() for w in (
            "hello", "i'm finroot", "i can help", "ask me a specific",
            "sovereign financial reasoning assistant",
        ))
        if is_greeting:
            return {
                "principle": "Insufficient evidence",
                "pass": True,
                "detail": "Greeting/informational response — evidence check not applicable",
            }
        has_specific_content = bool(re.search(r"\d", text))
        failed = tool_count < _MIN_TOOL_OUTPUTS and has_specific_content
        return {
            "principle": "Insufficient evidence",
            "pass": not failed,
            "detail": (
                f"Only {tool_count} tool output(s) for a specific recommendation "
                f"(minimum {_MIN_TOOL_OUTPUTS} required)"
                if failed
                else f"Evidence count ({tool_count}) meets minimum threshold"
            ),
        }


__all__ = ["PrudentialVerifier", "PrudentialVerdict"]
