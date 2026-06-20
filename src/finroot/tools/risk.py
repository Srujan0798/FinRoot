"""Pure-Python risk metrics computation tool (wave-11 improvements).

Computes a richer risk dashboard from daily returns:

  - volatility_annual    (std * sqrt(252))
  - var_historical       (empirical percentile of returns)
  - cvar_historical      (mean of tail below VaR)
  - var_parametric       (normal-distribution analytic VaR)
  - cvar_parametric      (normal-distribution analytic CVaR)
  - sharpe_ratio         (mean / std * sqrt(252))
  - sortino_ratio        (mean / downside_deviation * sqrt(252))
  - calmar_ratio         (annualised_return / |max_drawdown|)
  - max_drawdown         (peak-to-trough decline of cumulative product)
  - skewness, kurtosis   (distribution shape)
  - stress_test_pct      (hypothetical %-shock applied to the cumulative curve)
  - scenario_analysis    (predefined bull/base/bear/crash labels with outcomes)
  - hhi                  (Herfindahl-Hirschman Index, concentration)

Methods used (all in citation):
  - Historical VaR: the 5th-percentile empirical return, sign convention
    positive for a loss.
  - Parametric VaR:  -(mu - z * sigma)  under a normal assumption.
  - CVaR:            mean of returns worse than VaR.
  - Sharpe:          mean / sigma_daily * sqrt(252), rf assumed 0 (the
                     agent can subtract a risk-free rate if needed).
  - Sortino:         mean / downside_sigma * sqrt(252).
  - Calmar:          annualised_mean / |max_drawdown|.
  - HHI:             sum(weight_i^2) over the *weights* field; if missing,
                     falls back to equal-weight and reports so.

The tool is pure-stdlib (``statistics`` + ``math``) and optionally uses
``numpy`` for performance when available.
"""

from __future__ import annotations

import logging
import math
import statistics
from typing import Any

from pydantic import BaseModel, Field

from finroot.tools.base import BaseTool, ToolCallError

logger = logging.getLogger(__name__)

_TRADING_DAYS_PER_YEAR = 252

# Z-scores for the standard normal at common confidence levels.
_Z_SCORES: dict[float, float] = {
    0.90: 1.2816,
    0.95: 1.6449,
    0.99: 2.3263,
}

# Default stress-test scenarios. Negative values are shocks (e.g. -0.30 = -30%).
_DEFAULT_SCENARIOS: dict[str, float] = {
    "bull_+20pct": 0.20,
    "base_0pct": 0.0,
    "mild_-10pct": -0.10,
    "bear_-20pct": -0.20,
    "crash_-30pct": -0.30,
    "severe_-40pct": -0.40,
}


# ---------------------------------------------------------------------------
# I/O types
# ---------------------------------------------------------------------------


class StressTest(BaseModel):
    label: str
    shock_pct: float
    resulting_value_pct: float
    description: str


class ScenarioResult(BaseModel):
    name: str
    shock_pct: float
    portfolio_change_pct: float
    interpretation: str


class RiskInput(BaseModel):
    returns: list[float] = Field(
        description="Daily simple returns (e.g. 0.01 = +1%).",
    )
    confidence: float = Field(default=0.95, ge=0.9, le=0.99)
    weights: list[float] | None = Field(
        default=None,
        description=(
            "Optional holding weights for HHI (concentration) computation. "
            "If absent, HHI is reported as None."
        ),
    )
    risk_free_rate_annual: float = Field(
        default=0.0,
        ge=0.0,
        le=0.5,
        description=(
            "Annual risk-free rate used in Sharpe / Sortino. Default 0.0 for "
            "back-compat; callers can pass ~0.065 to use the Indian 10Y G-Sec "
            "as the risk-free rate."
        ),
    )
    stress_shocks: list[float] | None = Field(
        default=None,
        description=(
            "Optional override list of %-shocks to apply for stress testing. "
            "Positive = gain, negative = loss. Defaults to a standard suite."
        ),
    )

    model_config = {"extra": "forbid"}


class RiskOutput(BaseModel):
    n_observations: int
    confidence: float
    # Core metrics (back-compat field names kept: var_95, cvar_95)
    volatility_annual: float
    var_95: float
    cvar_95: float
    var_historical: float
    cvar_historical: float
    var_parametric: float
    cvar_parametric: float
    sharpe_ratio: float | None
    sortino_ratio: float | None
    calmar_ratio: float | None
    max_drawdown: float
    skewness: float | None
    kurtosis: float | None
    # Concentration (HHI)
    hhi: float | None
    hhi_interpretation: str | None
    # Stress / scenarios
    stress_tests: list[StressTest]
    scenario_analysis: list[ScenarioResult]
    # Methodology + citation
    methodology: str
    citation: str

    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------


class RiskCalculationTool(BaseTool[RiskInput, RiskOutput]):
    """Compute a comprehensive risk dashboard from a daily-return series.

    Wave-11 additions (vs the wave-3 base):
      - Parametric (normal-distribution) VaR / CVaR alongside historical.
      - Sortino and Calmar ratios (downside-risk-adjusted and drawdown-
        adjusted performance).
      - Skewness / kurtosis (distribution shape).
      - HHI concentration index (when weights are supplied).
      - Stress tests: apply a list of %-shocks and report the resulting
        portfolio value change.
      - Scenario analysis with named labels.
      - Methodology + formula citations in the output.
    """

    name = "risk_calculation"

    def _run(self, inp: RiskInput) -> RiskOutput:
        returns = inp.returns
        n = len(returns)

        if n < 2:
            raise ToolCallError(
                f"RiskCalculationTool requires at least 2 returns, got {n}"
            )

        np_ = _lazy_numpy()
        if np_ is not None:
            core = self._compute_core_numpy(returns, inp, np_)
        else:
            core = self._compute_core_stdlib(returns, inp)

        hhi, hhi_interp = self._compute_hhi(inp.weights)

        stress_tests = self._build_stress_tests(inp.stress_shocks, core["mu_daily"], core["sigma_daily"])
        scenarios = self._build_scenarios(core["mu_annual"], core["sigma_annual"])

        methodology = (
            f"Historical VaR: empirical {int(inp.confidence * 100)}th-percentile "
            f"return over {n} observations. "
            f"Parametric VaR: -(mu - z*sigma) where z={_Z_SCORES[inp.confidence]:.4f}. "
            f"CVaR: mean of returns below the VaR threshold. "
            f"Sharpe: (mean - rf_daily) / sigma_daily * sqrt(252) with "
            f"rf_annual={inp.risk_free_rate_annual:.4f}. "
            f"Sortino: like Sharpe but downside-deviation. "
            f"Calmar: annualised_return / |max_drawdown|. "
            f"Max drawdown: peak-to-trough on cumprod(1+r). "
            f"HHI: sum(w_i^2) over supplied weights."
        )

        citation = (
            f"Risk dashboard: {n} daily returns, "
            f"confidence {inp.confidence:.2f}, "
            f"annualised at {252} trading days. "
            "Formulas: std*sqrt(252) for vol; "
            "percentile for VaR; conditional-mean for CVaR."
        )

        return RiskOutput(
            n_observations=n,
            confidence=inp.confidence,
            volatility_annual=core["vol_annual"],
            var_95=core["var_historical"],
            cvar_95=core["cvar_historical"],
            var_historical=core["var_historical"],
            cvar_historical=core["cvar_historical"],
            var_parametric=core["var_parametric"],
            cvar_parametric=core["cvar_parametric"],
            sharpe_ratio=core["sharpe"],
            sortino_ratio=core["sortino"],
            calmar_ratio=core["calmar"],
            max_drawdown=core["max_dd"],
            skewness=core["skewness"],
            kurtosis=core["kurtosis"],
            hhi=hhi,
            hhi_interpretation=hhi_interp,
            stress_tests=stress_tests,
            scenario_analysis=scenarios,
            methodology=methodology,
            citation=citation,
        )

    # ------------------------------------------------------------------
    # Core computation
    # ------------------------------------------------------------------

    def _compute_core_numpy(self, returns, inp, np_):
        arr = np_.array(returns, dtype=np_.float64)
        std = float(np_.std(arr, ddof=1))
        mean = float(np_.mean(arr))
        mu_daily = mean
        sigma_daily = std
        vol_annual = std * math.sqrt(_TRADING_DAYS_PER_YEAR)
        mu_annual = mean * _TRADING_DAYS_PER_YEAR

        # Historical VaR — back-compat: report as the signed percentile
        # (typically negative; represents the return at the tail, not the
        # loss amount). Same convention as wave-3.
        var_pct = (1 - inp.confidence) * 100
        var_hist = float(np_.percentile(arr, var_pct))
        mask = arr < var_hist
        cvar_hist = float(np_.mean(arr[mask])) if np_.any(mask) else var_hist

        # Parametric VaR (normal, signed): -(mu - z*sigma)
        z = _Z_SCORES[inp.confidence]
        var_param = -(mean - z * std)
        # Parametric CVaR: -(mu - sigma * phi(z)/(1-c))
        phi_z = math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)
        cvar_param = -(mean - std * phi_z / (1 - inp.confidence))

        # Ratios
        rf_daily = inp.risk_free_rate_annual / _TRADING_DAYS_PER_YEAR
        sharpe = ((mean - rf_daily) / std * math.sqrt(_TRADING_DAYS_PER_YEAR)) if std > 0 else None

        downside = arr[arr < rf_daily] - rf_daily
        if downside.size > 0:
            dstd = float(np_.std(downside, ddof=1))
            sortino = (
                (mean - rf_daily) / dstd * math.sqrt(_TRADING_DAYS_PER_YEAR)
                if dstd > 0
                else None
            )
        else:
            sortino = None

        cum = np_.cumprod(1.0 + arr)
        running_max = np_.maximum.accumulate(cum)
        dd = 1.0 - cum / running_max
        max_dd = float(np_.max(dd))

        calmar = (
            mu_annual / max_dd if max_dd > 0 else None
        )

        # skewness/kurtosis are None for small samples (n<3 / n<4) — guard the
        # float() conversion so identical/short return series don't crash.
        _skew = _skewness(arr, np_=np_)
        _kurt = _excess_kurtosis(arr, np_=np_)
        skewness = float(_skew) if _skew is not None else None
        kurtosis = float(_kurt) if _kurt is not None else None

        return {
            "vol_annual": vol_annual,
            "var_historical": var_hist,
            "cvar_historical": cvar_hist,
            "var_parametric": var_param,
            "cvar_parametric": cvar_param,
            "sharpe": sharpe,
            "sortino": sortino,
            "calmar": calmar,
            "max_dd": max_dd,
            "skewness": skewness,
            "kurtosis": kurtosis,
            "mu_daily": mu_daily,
            "sigma_daily": sigma_daily,
            "mu_annual": mu_annual,
            "sigma_annual": vol_annual,
        }

    def _compute_core_stdlib(self, returns, inp):
        std = statistics.stdev(returns)
        mean = statistics.mean(returns)
        mu_daily = mean
        sigma_daily = std
        vol_annual = std * math.sqrt(_TRADING_DAYS_PER_YEAR)
        mu_annual = mean * _TRADING_DAYS_PER_YEAR

        var_pct = (1 - inp.confidence) * 100
        var_hist = _percentile(returns, var_pct)
        tail = [r for r in returns if r < var_hist]
        cvar_hist = statistics.mean(tail) if tail else var_hist

        z = _Z_SCORES[inp.confidence]
        var_param = -(mean - z * std)
        phi_z = math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)
        cvar_param = -(mean - std * phi_z / (1 - inp.confidence))

        rf_daily = inp.risk_free_rate_annual / _TRADING_DAYS_PER_YEAR
        sharpe = ((mean - rf_daily) / std * math.sqrt(_TRADING_DAYS_PER_YEAR)) if std > 0 else None

        downside = [r - rf_daily for r in returns if r < rf_daily]
        if downside:
            dstd = statistics.stdev(downside)
            sortino = (
                (mean - rf_daily) / dstd * math.sqrt(_TRADING_DAYS_PER_YEAR)
                if dstd > 0
                else None
            )
        else:
            sortino = None

        cum = 1.0
        running_max = 1.0
        max_dd = 0.0
        for r in returns:
            cum *= 1.0 + r
            if cum > running_max:
                running_max = cum
            dd = 1.0 - cum / running_max
            if dd > max_dd:
                max_dd = dd

        calmar = (
            mu_annual / max_dd if max_dd > 0 else None
        )

        skewness = _skewness(returns)
        kurtosis = _excess_kurtosis(returns)

        return {
            "vol_annual": vol_annual,
            "var_historical": var_hist,
            "cvar_historical": cvar_hist,
            "var_parametric": var_param,
            "cvar_parametric": cvar_param,
            "sharpe": sharpe,
            "sortino": sortino,
            "calmar": calmar,
            "max_dd": max_dd,
            "skewness": skewness,
            "kurtosis": kurtosis,
            "mu_daily": mu_daily,
            "sigma_daily": sigma_daily,
            "mu_annual": mu_annual,
            "sigma_annual": vol_annual,
        }

    # ------------------------------------------------------------------
    # Stress + scenario helpers
    # ------------------------------------------------------------------

    def _build_stress_tests(self, shocks, mu_daily, sigma_daily):
        chosen = shocks if shocks is not None else list(_DEFAULT_SCENARIOS.values())
        results: list[StressTest] = []
        for shock in chosen:
            # Translate a single-day %-shock into a portfolio value change.
            # The simplest mapping: apply shock directly to the cumprod curve.
            # We approximate the post-shock return as max(shock, -1.0).
            post_return = max(shock, -0.999)
            results.append(
                StressTest(
                    label=_label_for_shock(shock),
                    shock_pct=shock,
                    resulting_value_pct=post_return,
                    description=(
                        f"Apply a {shock:+.1%} one-shot return shock; "
                        f"portfolio value changes by {post_return:+.1%}."
                    ),
                )
            )
        return results

    def _build_scenarios(self, mu_annual, sigma_annual):
        # Three scenarios derived from the user's own return distribution.
        bull = mu_annual + sigma_annual
        base = mu_annual
        bear = mu_annual - sigma_annual
        crash = mu_annual - 2 * sigma_annual
        return [
            ScenarioResult(
                name="Bull (mu + 1*sigma)",
                shock_pct=0.0,
                portfolio_change_pct=bull,
                interpretation=(
                    "If next year delivers one standard-deviation better "
                    f"than the mean, expect ~{bull:.1%} annual return."
                ),
            ),
            ScenarioResult(
                name="Base (mu)",
                shock_pct=0.0,
                portfolio_change_pct=base,
                interpretation=(
                    f"Expected annual return under the historical mean: {base:.1%}."
                ),
            ),
            ScenarioResult(
                name="Bear (mu - 1*sigma)",
                shock_pct=0.0,
                portfolio_change_pct=bear,
                interpretation=(
                    "If next year is one standard-deviation worse than the "
                    f"mean, expect ~{bear:.1%} annual return."
                ),
            ),
            ScenarioResult(
                name="Crash (mu - 2*sigma)",
                shock_pct=0.0,
                portfolio_change_pct=crash,
                interpretation=(
                    "Two-sigma adverse event: roughly a 1-in-20 year return. "
                    f"Expect ~{crash:.1%} annual return — not a guarantee of "
                    "an actual loss, just a tail estimate."
                ),
            ),
        ]

    @staticmethod
    def _compute_hhi(weights):
        if not weights:
            return None, None
        if any(w < 0 for w in weights):
            raise ToolCallError("HHI weights must be non-negative")
        s = sum(weights)
        if s <= 0:
            raise ToolCallError("HHI weights must sum to > 0")
        norm = [w / s for w in weights]
        hhi = sum(w * w for w in norm)
        # Interpretation thresholds (US DOJ antitrust convention adapted
        # for portfolio concentration; <0.15 unconcentrated, >0.25 concentrated).
        if hhi < 0.15:
            interp = "Unconcentrated (HHI < 0.15)"
        elif hhi < 0.25:
            interp = "Moderately concentrated (0.15 <= HHI < 0.25)"
        else:
            interp = "Highly concentrated (HHI >= 0.25)"
        return hhi, interp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _lazy_numpy() -> Any:
    try:
        import numpy as np

        return np
    except ImportError:
        return None


def _percentile(data: list[float], p: float) -> float:
    """Linear-interpolation percentile (like numpy) using stdlib."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (p / 100.0) * (len(sorted_data) - 1)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    d0 = sorted_data[f] * (c - k)
    d1 = sorted_data[c] * (k - f)
    return d0 + d1


def _skewness(data, np_=None):
    n = len(data)
    if n < 3:
        return None
    if np_ is not None:
        arr = np_.array(data, dtype=np_.float64)
        m = float(np_.mean(arr))
        s = float(np_.std(arr, ddof=1))
        if s == 0:
            return 0.0
        return float(np_.mean(((arr - m) / s) ** 3))
    mean = statistics.mean(data)
    std = statistics.stdev(data)
    if std == 0:
        return 0.0
    return sum(((x - mean) / std) ** 3 for x in data) / n


def _excess_kurtosis(data, np_=None):
    n = len(data)
    if n < 4:
        return None
    if np_ is not None:
        arr = np_.array(data, dtype=np_.float64)
        m = float(np_.mean(arr))
        s = float(np_.std(arr, ddof=1))
        if s == 0:
            return 0.0
        return float(np_.mean(((arr - m) / s) ** 4) - 3.0)
    mean = statistics.mean(data)
    std = statistics.stdev(data)
    if std == 0:
        return 0.0
    return sum(((x - mean) / std) ** 4 for x in data) / n - 3.0


def _label_for_shock(shock: float) -> str:
    if shock >= 0.15:
        return f"rally_+{int(shock * 100)}pct"
    if shock >= 0.05:
        return f"mild_gain_+{int(shock * 100)}pct"
    if shock > -0.05:
        return "flat"
    if shock > -0.15:
        return f"mild_loss_{int(shock * 100)}pct"
    if shock > -0.25:
        return f"bear_{int(shock * 100)}pct"
    return f"crash_{int(shock * 100)}pct"


__all__ = ["RiskCalculationTool", "RiskInput", "RiskOutput", "StressTest", "ScenarioResult"]
