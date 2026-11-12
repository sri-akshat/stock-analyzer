"""The pluggable Strategy interface (backlog item 6).

Every strategy implements generate(snapshot) -> Signal and backtests
through the same engine, so any strategy can be deployed the same way.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..types import Action, MarketSnapshot, Signal


class Strategy(ABC):
    name: str = "base"
    #: bars of history a strategy needs before its signals are meaningful
    min_history: int = 60

    @abstractmethod
    def generate(self, snapshot: MarketSnapshot) -> Signal:
        """Produce a signal using ONLY data inside the snapshot."""

    def __repr__(self) -> str:  # pragma: no cover
        return f"{type(self).__name__}(name={self.name!r})"


def hold(reason: str = "") -> Signal:
    return Signal(Action.HOLD, 0.0, reason)
