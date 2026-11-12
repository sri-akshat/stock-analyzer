"""Shared typed structures. One MarketSnapshot flows through fetchers,
analyses, strategies and the backtester - no loose dicts, no .iloc hacks.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import pandas as pd


class Action(enum.Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass(frozen=True)
class Signal:
    """A strategy's opinion at one point in time.

    strength: 0.0 to 1.0 conviction. HOLD ignores strength.
    """
    action: Action
    strength: float = 0.0
    reason: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError(f"strength must be in [0, 1], got {self.strength}")


@dataclass
class MarketSnapshot:
    """Everything a strategy may see about one symbol, as of `as_of`.

    history: OHLCV DataFrame containing ONLY rows up to and including
    `as_of` (the backtester guarantees this; live runs use trailing data).
    Indicators must be computed causally from this window.
    """
    symbol: str
    as_of: pd.Timestamp
    history: pd.DataFrame
    sentiment: Optional[dict] = None      # e.g. {"polarity": 0.2, "subjectivity": 0.5}
    fundamentals: Optional[dict] = None   # e.g. {"pe_ratio": 22.5, "market_cap": ...}

    @property
    def price(self) -> float:
        return float(self.history["Close"].iloc[-1])


@dataclass
class Trade:
    symbol: str
    action: Action
    quantity: int
    price: float
    timestamp: pd.Timestamp
    reason: str = ""

    @property
    def value(self) -> float:
        return self.quantity * self.price


@dataclass
class Position:
    symbol: str
    quantity: int
    entry_price: float
    entry_time: pd.Timestamp
    stop_price: Optional[float] = None
