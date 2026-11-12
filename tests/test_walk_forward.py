import numpy as np

from stock_analyzer.backtest import walk_forward
from stock_analyzer.strategies import CompositeStrategy, SupportResistanceStrategy


def test_walk_forward_returns_out_of_sample_folds(ohlcv):
    rng = np.random.default_rng(7)
    closes = 100 + np.cumsum(rng.normal(0, 1, 400))
    df = ohlcv(closes)
    folds = walk_forward("TEST", df, SupportResistanceStrategy(), n_folds=3)
    assert len(folds) >= 2
    for fold in folds:
        assert fold.train_end < fold.test_start  # no overlap
        assert "sharpe" in fold.out_of_sample.metrics


def test_walk_forward_tunes_composite_on_train_only(ohlcv):
    rng = np.random.default_rng(3)
    closes = 100 + np.cumsum(rng.normal(0.05, 1, 600))
    df = ohlcv(closes)
    folds = walk_forward("TEST", df, CompositeStrategy(), n_folds=2, tune=True)
    assert folds
    for fold in folds:
        assert fold.best_params  # tuning produced weights
        assert set(fold.best_params) >= {"support_resistance", "momentum", "mean_reversion"}
