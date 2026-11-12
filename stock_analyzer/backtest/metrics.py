"""Backtest metrics. Max drawdown is true peak-to-trough on the equity
curve; returns are computed on total equity (cash + holdings), not cash.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..types import Action, Trade


def compute_metrics(equity: pd.Series, trades: list[Trade], initial_capital: float) -> dict:
    if equity.empty:
        return {}

    final = float(equity.iloc[-1])
    total_return = (final - initial_capital) / initial_capital

    days = max((equity.index[-1] - equity.index[0]).days, 1)
    cagr = (final / initial_capital) ** (365.0 / days) - 1 if final > 0 else -1.0

    rets = equity.pct_change().dropna()
    sharpe = float(rets.mean() / rets.std() * np.sqrt(252)) if len(rets) > 1 and rets.std() > 0 else 0.0

    # true peak-to-trough drawdown
    running_peak = equity.cummax()
    drawdown = equity / running_peak - 1.0
    max_drawdown = float(drawdown.min())

    # pair buys with the sells that close them to score wins
    wins = losses = 0
    open_buys: list[Trade] = []
    for t in trades:
        if t.action is Action.BUY:
            open_buys.append(t)
        elif t.action is Action.SELL and open_buys:
            entry = open_buys.pop(0)
            if t.price > entry.price:
                wins += 1
            else:
                losses += 1
    closed = wins + losses
    win_rate = wins / closed if closed else None

    return {
        "initial_capital": round(initial_capital, 2),
        "final_equity": round(final, 2),
        "total_return_pct": round(total_return * 100, 2),
        "cagr_pct": round(cagr * 100, 2),
        "sharpe": round(sharpe, 2),
        "max_drawdown_pct": round(max_drawdown * 100, 2),
        "num_trades": len(trades),
        "win_rate_pct": round(win_rate * 100, 1) if win_rate is not None else None,
    }
