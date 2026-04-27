"""Financial calculation tools for Economist agent."""
from __future__ import annotations

import random
import math
from pydantic import BaseModel


class MarginScenario(BaseModel):
    name: str
    cost_per_unit: float
    market_price: float
    volume_units: int


class MarginResult(BaseModel):
    scenario: str
    margin_pct: float
    margin_rub_per_unit: float
    revenue_annual: float
    profit_annual: float


CALC_MARGIN_TOOL = {
    "name": "calc_margin",
    "description": "Calculate margin and profitability. Runs Monte Carlo for price volatility.",
    "input_schema": {
        "type": "object",
        "properties": {
            "cost_per_unit": {"type": "number"},
            "market_price": {"type": "number"},
            "volume_units_annual": {"type": "integer"},
            "cost_volatility_pct": {"type": "number", "default": 10},
            "price_volatility_pct": {"type": "number", "default": 5},
            "simulations": {"type": "integer", "default": 1000},
        },
        "required": ["cost_per_unit", "market_price", "volume_units_annual"],
    },
}


def calc_margin(
    cost_per_unit: float,
    market_price: float,
    volume_units_annual: int,
    cost_volatility_pct: float = 10.0,
    price_volatility_pct: float = 5.0,
    simulations: int = 1000,
) -> dict:
    """Monte Carlo margin calculation."""
    margins = []
    for _ in range(simulations):
        c = cost_per_unit * (1 + random.gauss(0, cost_volatility_pct / 100))
        p = market_price * (1 + random.gauss(0, price_volatility_pct / 100))
        margins.append((p - c) / p * 100 if p > 0 else 0)

    base_margin = (market_price - cost_per_unit) / market_price * 100 if market_price > 0 else 0
    return {
        "base_margin_pct": round(base_margin, 2),
        "margin_rub_per_unit": round(market_price - cost_per_unit, 2),
        "revenue_annual": round(market_price * volume_units_annual, 2),
        "profit_annual": round((market_price - cost_per_unit) * volume_units_annual, 2),
        "mc_p10_margin_pct": round(sorted(margins)[int(simulations * 0.10)], 2),
        "mc_p50_margin_pct": round(sorted(margins)[int(simulations * 0.50)], 2),
        "mc_p90_margin_pct": round(sorted(margins)[int(simulations * 0.90)], 2),
    }
