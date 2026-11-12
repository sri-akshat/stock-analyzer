"""Weighted combination of sub-strategy scores (backlog item 8).

Sub-strategy signals become scores in [-1, 1] (buy=+strength, sell=-strength),
combined with weights that the walk-forward harness tunes on TRAINING data
only - they are never hardcoded from full-period results.

When the snapshot carries sentiment / fundamentals, those add their own
weighted votes, so all three analyses finally feed one score.
"""
from __future__ import annotations

from ..types import Action, MarketSnapshot, Signal
from .base import Strategy, hold
from .mean_reversion import MeanReversionStrategy
from .momentum import MomentumStrategy
from .support_resistance import SupportResistanceStrategy


def _score(signal: Signal) -> float:
    if signal.action is Action.BUY:
        return signal.strength
    if signal.action is Action.SELL:
        return -signal.strength
    return 0.0


class CompositeStrategy(Strategy):
    name = "composite"

    def __init__(self, weights: dict[str, float] | None = None,
                 buy_threshold: float = 0.25, sell_threshold: float = -0.25):
        self.sub_strategies: list[Strategy] = [
            SupportResistanceStrategy(),
            MomentumStrategy(),
            MeanReversionStrategy(),
        ]
        # sentiment and fundamentals vote alongside the technical strategies
        self.weights = weights or {
            "support_resistance": 1.0,
            "momentum": 1.0,
            "mean_reversion": 0.8,
            "sentiment": 0.5,
            "fundamentals": 0.5,
        }
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.min_history = max(s.min_history for s in self.sub_strategies)

    def _sentiment_score(self, snapshot: MarketSnapshot) -> float:
        if not snapshot.sentiment:
            return 0.0
        polarity = snapshot.sentiment.get("polarity", 0.0) or 0.0
        return max(-1.0, min(1.0, polarity))

    def _fundamental_score(self, snapshot: MarketSnapshot) -> float:
        if not snapshot.fundamentals:
            return 0.0
        pe = snapshot.fundamentals.get("pe_ratio")
        if pe is None:
            return 0.0
        if pe < 15:
            return 0.5
        if pe > 40:
            return -0.5
        return 0.0

    def generate(self, snapshot: MarketSnapshot) -> Signal:
        votes: dict[str, float] = {}
        for strat in self.sub_strategies:
            try:
                votes[strat.name] = _score(strat.generate(snapshot))
            except Exception:
                votes[strat.name] = 0.0  # one bad strategy must not sink the rest
        votes["sentiment"] = self._sentiment_score(snapshot)
        votes["fundamentals"] = self._fundamental_score(snapshot)

        total_w = sum(abs(self.weights.get(k, 0.0)) for k in votes) or 1.0
        score = sum(self.weights.get(k, 0.0) * v for k, v in votes.items()) / total_w

        detail = ", ".join(f"{k}={v:+.2f}" for k, v in votes.items() if v)
        if score >= self.buy_threshold:
            return Signal(Action.BUY, round(min(1.0, score), 3), f"composite {score:+.2f} ({detail})")
        if score <= self.sell_threshold:
            return Signal(Action.SELL, round(min(1.0, -score), 3), f"composite {score:+.2f} ({detail})")
        return hold(f"composite {score:+.2f} inside bands ({detail})")
