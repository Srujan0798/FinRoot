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

_GUARANTEE_RE = re.compile(
    r"\b(?:guarantee[ds]?|will\s+definitely|promise[sd]?|certain\s+to|"
    r"risk[- ]?free|can't\s+lose|cannot\s+lose)\b",
    re.IGNORECASE,
)
_NEGATION_BEFORE_GUARANTEE_RE = re.compile(
    r"\b(?:does\s+not|doesn't|don't|no|not|never)\s+\w*\s*guarantee",
    re.IGNORECASE,
)

_SELL_RE = re.compile(r"\b(?:sell|liquidat|exit|close\s+out)\b", re.IGNORECASE)
_TAX_RE = re.compile(r"\b(?:tax|capital\s+gain|loss\s+harvest|tax[- ]?loss)\b", re.IGNORECASE)

_SHORT_TERM_RE = re.compile(
    r"\b(?:short[- ]?term|day[- ]?trad|swing[- ]?trad|quick\s+(?:profit|gain|flip)|"
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
        checks.append(self._check_diversification(text))
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
        """Combine summary + analysis from candidate or final recommendation."""
        rec = state.candidate or state.final
        if rec is None:
            return state.query
        return f"{rec.summary} {rec.analysis}"

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
    def _check_diversification(text: str) -> dict[str, Any]:
        """Detect allocation >40% to a single asset."""
        pct_matches = _PERCENT_RE.findall(text)
        failed = False
        detail = "No concentration violation detected"
        for pct_str in pct_matches:
            pct = float(pct_str)
            if pct > _MAX_SINGLE_ASSET_PCT:
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
        match = _GUARANTEE_RE.search(text)
        # Exclude negated contexts: "does not guarantee", "no guarantee", etc.
        negated = bool(_NEGATION_BEFORE_GUARANTEE_RE.search(text))
        failed = match is not None and not negated
        return {
            "principle": "No guarantees",
            "pass": not failed,
            "detail": (
                f"Contains guarantee language: {match.group()!r}"
                if failed
                else "No guarantee language detected"
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
        """Fail if tool_outputs < 2 and the answer makes specific claims."""
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
