"""Point-in-time backtest engine (backlog item 3).

Guarantees that make results trustworthy:
- A strategy at bar t receives a MarketSnapshot whose history ends at bar
  t. No full-period levels, no future data.
- Signals produced on the close of bar t execute at the OPEN of bar t+1
  (same-bar fills would flatter every strategy).
- Cash AND holdings are tracked; equity is marked to market daily, so open
  positions are never invisible.
- Stops are checked against each bar's low and filled at the stop price.
- Commission and slippage apply to every fill.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from ..config import get_settings
from ..risk import RiskEngine
from ..strategies.base import Strategy
from ..types import Action, MarketSnapshot, Position, Trade
from .metrics import compute_metrics


@dataclass
class BacktestResult:
    symbol: str
    strategy: str
    trades: list[Trade]
    equity_curve: pd.Series          # daily total equity, indexed by date
    metrics: dict = field(default_factory=dict)
    final_position: Position | None = None


class BacktestEngine:
    def __init__(self, risk: RiskEngine | None = None,
                 initial_capital: float | None = None,
                 commission_rate: float | None = None,
                 slippage_rate: float | None = None):
        settings = get_settings()
        self.risk = risk or RiskEngine()
        self.initial_capital = settings.initial_capital if initial_capital is None else initial_capital
        self.commission_rate = settings.commission_rate if commission_rate is None else commission_rate
        self.slippage_rate = settings.slippage_rate if slippage_rate is None else slippage_rate

    def _fill_price(self, raw: float, action: Action) -> float:
        # buys pay a little more, sells receive a little less
        slip = raw * self.slippage_rate
        return raw + slip if action is Action.BUY else raw - slip

    def run(self, symbol: str, history: pd.DataFrame, strategy: Strategy,
            sentiment: dict | None = None, fundamentals: dict | None = None) -> BacktestResult:
        cash = float(self.initial_capital)
        position: Position | None = None
        trades: list[Trade] = []
        equity_points: list[tuple[pd.Timestamp, float]] = []

        start = max(strategy.min_history, 2)
        pending_signal = None  # signal from bar t, executed at open of t+1

        closes = history["Close"]
        for i in range(len(history)):
            row = history.iloc[i]
            ts = history.index[i]

            # 1. execute yesterday's pending signal at today's open
            if pending_signal is not None and i > 0:
                open_price = float(row["Open"])
                if pending_signal.action is Action.BUY and position is None:
                    fill = self._fill_price(open_price, Action.BUY)
                    qty = self.risk.position_size(fill, cash, cash, pending_signal.strength)
                    if qty > 0:
                        cost = qty * fill * (1 + self.commission_rate)
                        if cost <= cash:
                            cash -= cost
                            position = Position(symbol, qty, fill, ts,
                                                stop_price=self.risk.stop_price(fill))
                            trades.append(Trade(symbol, Action.BUY, qty, fill, ts,
                                                pending_signal.reason))
                elif pending_signal.action is Action.SELL and position is not None:
                    fill = self._fill_price(open_price, Action.SELL)
                    cash += position.quantity * fill * (1 - self.commission_rate)
                    trades.append(Trade(symbol, Action.SELL, position.quantity, fill, ts,
                                        pending_signal.reason))
                    position = None
                pending_signal = None

            # 2. stop loss, checked against today's low
            if position is not None and self.risk.check_stop(position, float(row["Low"])):
                fill = self._fill_price(position.stop_price, Action.SELL)
                cash += position.quantity * fill * (1 - self.commission_rate)
                trades.append(Trade(symbol, Action.SELL, position.quantity, fill, ts,
                                    f"stop loss at {position.stop_price:.2f}"))
                position = None

            # 3. mark to market
            equity = cash + (position.quantity * float(row["Close"]) if position else 0.0)
            equity_points.append((ts, equity))

            # 4. generate tomorrow's signal from a point-in-time window
            if i >= start:
                snapshot = MarketSnapshot(
                    symbol=symbol, as_of=ts,
                    history=history.iloc[: i + 1],
                    sentiment=sentiment, fundamentals=fundamentals,
                )
                signal = strategy.generate(snapshot)
                if signal.action is not Action.HOLD:
                    pending_signal = signal

        equity_curve = pd.Series(dict(equity_points)).sort_index()
        result = BacktestResult(symbol=symbol, strategy=strategy.name,
                                trades=trades, equity_curve=equity_curve,
                                final_position=position)
        result.metrics = compute_metrics(equity_curve, trades, self.initial_capital)
        return result
