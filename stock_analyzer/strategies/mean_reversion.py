"""RSI mean reversion: buy oversold, sell overbought."""
from __future__ import annotations

from ..indicators import rsi
from ..types import Action, MarketSnapshot, Signal
from .base import Strategy, hold


class MeanReversionStrategy(Strategy):
    name = "mean_reversion"

    def __init__(self, window: int = 14, oversold: float = 30.0, overbought: float = 70.0):
        self.window = window
        self.oversold = oversold
        self.overbought = overbought
        self.min_history = window + 10

    def generate(self, snapshot: MarketSnapshot) -> Signal:
        close = snapshot.history["Close"]
        if len(close) < self.min_history:
            return hold("insufficient history")
        value = float(rsi(close, self.window).iloc[-1])

        if value <= self.oversold:
            strength = round(min(1.0, (self.oversold - value) / self.oversold + 0.4), 3)
            return Signal(Action.BUY, strength, f"RSI {value:.1f} oversold")
        if value >= self.overbought:
            strength = round(min(1.0, (value - self.overbought) / (100 - self.overbought) + 0.4), 3)
            return Signal(Action.SELL, strength, f"RSI {value:.1f} overbought")
        return hold(f"RSI {value:.1f} neutral")
