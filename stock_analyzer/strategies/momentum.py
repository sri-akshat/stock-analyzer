"""Trend-following: golden/death cross with price confirmation."""
from __future__ import annotations

from ..indicators import sma
from ..types import Action, MarketSnapshot, Signal
from .base import Strategy, hold


class MomentumStrategy(Strategy):
    name = "momentum"

    def __init__(self, fast: int = 50, slow: int = 200):
        self.fast = fast
        self.slow = slow
        self.min_history = slow + 5

    def generate(self, snapshot: MarketSnapshot) -> Signal:
        close = snapshot.history["Close"]
        if len(close) < self.slow + 2:
            return hold("insufficient history")
        fast_ma = sma(close, self.fast)
        slow_ma = sma(close, self.slow)
        f_now, s_now = fast_ma.iloc[-1], slow_ma.iloc[-1]
        f_prev, s_prev = fast_ma.iloc[-2], slow_ma.iloc[-2]
        price = snapshot.price

        crossed_up = f_prev <= s_prev and f_now > s_now
        crossed_down = f_prev >= s_prev and f_now < s_now
        gap = abs(f_now - s_now) / max(price, 1e-9)
        strength = round(min(1.0, 0.5 + gap * 20), 3)

        if crossed_up:
            return Signal(Action.BUY, strength,
                          f"MA{self.fast} crossed above MA{self.slow}")
        if crossed_down:
            return Signal(Action.SELL, strength,
                          f"MA{self.fast} crossed below MA{self.slow}")
        if f_now > s_now and price > f_now:
            return Signal(Action.BUY, 0.3, "uptrend continuation")
        if f_now < s_now and price < f_now:
            return Signal(Action.SELL, 0.3, "downtrend continuation")
        return hold("no trend edge")
