"""Walk-forward validation.

Splits history into sequential folds: tune on the train slice, evaluate on
the following test slice, roll forward. Reported metrics are OUT-OF-SAMPLE
only - the number you can argue with.

For the composite strategy, tuning = grid search over sub-strategy weights,
scored by in-sample Sharpe.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass

import pandas as pd

from ..strategies.base import Strategy
from ..strategies.composite import CompositeStrategy
from .engine import BacktestEngine, BacktestResult


@dataclass
class FoldResult:
    fold: int
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    best_params: dict
    in_sample_metrics: dict
    out_of_sample: BacktestResult


def _split_folds(history: pd.DataFrame, n_folds: int):
    """Yield (fold, train_df, test_df) pairs with an expanding train window
    rolling forward through the data."""
    n = len(history)
    fold_size = n // (n_folds + 1)
    for k in range(n_folds):
        train_end = fold_size * (k + 1)
        test_end = min(train_end + fold_size, n)
        if train_end < 60 or test_end - train_end < 20:
            continue
        yield k, history.iloc[:train_end], history.iloc[train_end:test_end]


def _tune_composite(train: pd.DataFrame, symbol: str, engine: BacktestEngine) -> dict:
    grid = [0.5, 1.0, 1.5]
    best_sharpe, best_weights = float("-inf"), None
    for combo in itertools.product(grid, repeat=3):
        weights = {
            "support_resistance": combo[0],
            "momentum": combo[1],
            "mean_reversion": combo[2],
            "sentiment": 0.5,
            "fundamentals": 0.5,
        }
        strat = CompositeStrategy(weights=weights)
        result = engine.run(symbol, train, strat)
        sharpe = result.metrics.get("sharpe", float("-inf"))
        if sharpe > best_sharpe:
            best_sharpe, best_weights = sharpe, weights
    return best_weights or {}


def walk_forward(symbol: str, history: pd.DataFrame, strategy: Strategy,
                 n_folds: int = 3, tune: bool = True,
                 engine: BacktestEngine | None = None) -> list[FoldResult]:
    engine = engine or BacktestEngine()
    folds: list[FoldResult] = []

    for k, train, test in _split_folds(history, n_folds):
        params: dict = {}
        test_strategy = strategy
        if tune and isinstance(strategy, CompositeStrategy):
            params = _tune_composite(train, symbol, engine)
            test_strategy = CompositeStrategy(weights=params)
        in_sample = engine.run(symbol, train, test_strategy)
        out_sample = engine.run(symbol, test, test_strategy)
        folds.append(FoldResult(
            fold=k,
            train_start=train.index[0], train_end=train.index[-1],
            test_start=test.index[0], test_end=test.index[-1],
            best_params=params,
            in_sample_metrics=in_sample.metrics,
            out_of_sample=out_sample,
        ))
    return folds
