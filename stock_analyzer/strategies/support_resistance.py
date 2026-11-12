"""Buy near rolling support, sell near rolling resistance.

This is the original repo's single rule, made point-in-time: levels come
from a trailing window instead of the full-period min/max.
"""
from __future__ import annotations

from ..indicators import rolling_resistance, rolling_support
from ..types import Action, MarketSnapshot, Signal
from .base import Strategy, hold


class SupportResistanceStrategy(Strategy):
    name = "support_resistance"

    def __init__(self, window: int = 60, tolerance: float = 0.02):
        self.window = window
        self.tolerance = tolerance
        self.min_history = max(20, window // 2)

    def generate(self, snapshot: MarketSnapshot) -> Signal:
        close = snapshot.history["Close"]
        support = rolling_support(close, self.window).iloc[-1]
        resistance = rolling_resistance(close, self.window).iloc[-1]
        price = snapshot.price
        if price != price or support != support or resistance != resistance:  # NaN guards
            return hold("insufficient history")
        span = max(resistance - support, 1e-9)

        if price <= support * (1 + self.tolerance):
            # stronger the deeper into the zone below the tolerance edge
            strength = min(1.0, (support * (1 + self.tolerance) - price) / (span * 0.1) + 0.3)
            return Signal(Action.BUY, round(strength, 3),
                          f"price {price:.2f} near support {support:.2f}")
        if price >= resistance * (1 - self.tolerance):
            strength = min(1.0, (price - resistance * (1 - self.tolerance)) / (span * 0.1) + 0.3)
            return Signal(Action.SELL, round(strength, 3),
                          f"price {price:.2f} near resistance {resistance:.2f}")
        return hold(f"price {price:.2f} mid-range ({support:.2f}-{resistance:.2f})")
