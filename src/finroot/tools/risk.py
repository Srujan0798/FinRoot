"""Pure-Python risk metrics computation tool.

Computes volatility, VaR, CVaR, Sharpe ratio, and max drawdown from
daily returns using stdlib ``statistics`` and ``math``. Optionally uses
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

# ---------------------------------------------------------------------------
# I/O types
# ---------------------------------------------------------------------------


class RiskInput(BaseModel):
    returns: list[float]
    confidence: float = Field(default=0.95, ge=0.9, le=0.99)

    model_config = {"extra": "forbid"}


class RiskOutput(BaseModel):
    volatility_annual: float
    var_95: float
    cvar_95: float
    sharpe_ratio: float | None
    max_drawdown: float
    citation: str

    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------


class RiskCalculationTool(BaseTool[RiskInput, RiskOutput]):
    """Compute risk metrics from a series of daily returns.

    Formulas (all cited in output):
      - volatility_annual = std(returns) * sqrt(252)
      - var_95 = percentile(returns, 5%)       (historical)
      - cvar_95 = mean(returns below var_95)
      - sharpe_ratio = mean(returns) / std(returns) * sqrt(252)
      - max_drawdown = max peak-to-trough decline
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
            vol_annual, var_95, cvar_95, sharpe, max_dd = self._compute_numpy(
                returns, np_
            )
        else:
            vol_annual, var_95, cvar_95, sharpe, max_dd = self._compute_stdlib(returns)

        return RiskOutput(
            volatility_annual=vol_annual,
            var_95=var_95,
            cvar_95=cvar_95,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            citation=f"Computed from {n} daily returns, annualised at 252 trading days",
        )

    # ------------------------------------------------------------------
    # Computation paths
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_numpy(returns: list[float], np_: Any):
        arr = np_.array(returns, dtype=np_.float64)
        std = float(np_.std(arr, ddof=1))
        vol_annual = std * math.sqrt(252)
        var_95 = float(np_.percentile(arr, 5))
        mask = arr < var_95
        cvar_95 = float(np_.mean(arr[mask])) if np_.any(mask) else 0.0
        if std == 0.0:
            sharpe: float | None = None
        else:
            sharpe = float(np_.mean(arr) / std * math.sqrt(252))
        cum = np_.cumprod(1.0 + arr)
        running_max = np_.maximum.accumulate(cum)
        dd = 1.0 - cum / running_max
        max_dd = float(np_.max(dd))
        return vol_annual, var_95, cvar_95, sharpe, max_dd

    @staticmethod
    def _compute_stdlib(returns: list[float]):
        std = statistics.stdev(returns)
        vol_annual = std * math.sqrt(252)
        var_95 = _percentile(returns, 5)
        cvar_values = [r for r in returns if r < var_95]
        cvar_95 = statistics.mean(cvar_values) if cvar_values else 0.0
        if std == 0.0:
            sharpe: float | None = None
        else:
            sharpe = statistics.mean(returns) / std * math.sqrt(252)
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
        return vol_annual, var_95, cvar_95, sharpe, max_dd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _lazy_numpy() -> Any:
    try:
        import numpy as np
        return np
    except ImportError:
        return None


def _percentile(data: list[float], p: int) -> float:
    """Linear-interpolation percentile (like numpy) using stdlib."""
    sorted_data = sorted(data)
    k = (p / 100.0) * (len(sorted_data) - 1)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    d0 = sorted_data[f] * (c - k)
    d1 = sorted_data[c] * (k - f)
    return d0 + d1


__all__ = ["RiskCalculationTool", "RiskInput", "RiskOutput"]
