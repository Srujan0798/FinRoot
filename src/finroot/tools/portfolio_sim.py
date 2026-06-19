"""Monte Carlo portfolio simulation tool.

Simulates portfolio value paths over a given horizon using normally
distributed daily returns. Pure stdlib ``random`` + ``math``; no external
deps required.
"""

from __future__ import annotations

import logging
import math
import os
import random
from typing import Any

from pydantic import BaseModel, Field

from finroot.tools.base import BaseTool, ToolCallError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# I/O types
# ---------------------------------------------------------------------------


class SimInput(BaseModel):
    holdings: list[dict[str, Any]]
    horizon_years: int = Field(ge=1, le=30)
    scenarios: int = Field(default=1000, ge=100, le=10000)

    model_config = {"extra": "forbid"}


class SimOutput(BaseModel):
    expected_return: float
    p10_return: float
    p90_return: float
    probability_of_loss: float
    citation: str

    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------


class PortfolioSimulatorTool(BaseTool[SimInput, SimOutput]):
    """Monte Carlo portfolio simulation.

    Generates ``scenarios`` random paths over ``horizon_years * 252`` days.
    Each daily return is drawn from a normal distribution with default
    parameters μ=0.0008, σ=0.012.
    """

    name = "portfolio_simulator"
    _DEFAULT_MU = 0.0008
    _DEFAULT_SIGMA = 0.012

    def __init__(
        self,
        audit: Any = None,
        mock: bool = False,
    ) -> None:
        super().__init__(audit=audit)
        self.mock = mock or os.environ.get("FINROOT_LLM_PROVIDER", "").lower() == "mock"

    def _run(self, inp: SimInput) -> SimOutput:
        # Validate holdings
        if not inp.holdings:
            raise ToolCallError("PortfolioSimulatorTool requires at least one holding")

        for h in inp.holdings:
            if "weight" not in h or not isinstance(h["weight"], (int, float)):
                raise ToolCallError(
                    f"Each holding must have a numeric 'weight' field; got {h}"
                )
            if h["weight"] <= 0:
                raise ToolCallError(
                    f"Holdings weight must be positive; got {h['weight']}"
                )

        total_weight = sum(h["weight"] for h in inp.holdings)
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(
                "Holdings weights sum to %.4f (expected ~1.0)", total_weight
            )

        n_days = inp.horizon_years * 252
        n_scenarios = inp.scenarios

        if self.mock:
            random.seed(42)

        mu = self._DEFAULT_MU
        sigma = self._DEFAULT_SIGMA

        final_values: list[float] = []
        for _ in range(n_scenarios):
            value = 1.0
            for _ in range(n_days):
                value *= 1.0 + random.gauss(mu, sigma)
            final_values.append(value)

        sorted_final = sorted(final_values)
        median_val = _percentile_from_sorted(sorted_final, 50)
        p10_val = _percentile_from_sorted(sorted_final, 10)
        p90_val = _percentile_from_sorted(sorted_final, 90)
        loss_count = sum(1 for v in final_values if v < 1.0)

        expected_return = median_val / 1.0 - 1.0
        p10_return = p10_val / 1.0 - 1.0
        p90_return = p90_val / 1.0 - 1.0
        prob_loss = loss_count / n_scenarios

        return SimOutput(
            expected_return=round(expected_return, 6),
            p10_return=round(p10_return, 6),
            p90_return=round(p90_return, 6),
            probability_of_loss=round(prob_loss, 6),
            citation=(
                f"Monte Carlo simulation: {n_scenarios} paths, "
                f"{inp.horizon_years}-year horizon"
            ),
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _percentile_from_sorted(sorted_data: list[float], p: int) -> float:
    """Linear-interpolation percentile from a pre-sorted list."""
    n = len(sorted_data)
    if n == 0:
        return 0.0
    k = (p / 100.0) * (n - 1)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    d0 = sorted_data[f] * (c - k)
    d1 = sorted_data[c] * (k - f)
    return d0 + d1


__all__ = ["PortfolioSimulatorTool", "SimInput", "SimOutput"]
