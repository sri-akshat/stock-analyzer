import numpy as np

from stock_analyzer.consult import ConsultService
from stock_analyzer.consult.providers import MockProvider
from stock_analyzer.persistence import Store
from stock_analyzer.recommend import RecommendationEngine
from stock_analyzer.strategies import SupportResistanceStrategy
from stock_analyzer.types import Action


def _patch_data(monkeypatch, ohlcv):
    closes = [100 + (i % 10) for i in range(120)] + [100.5, 100.1]
    df = ohlcv(closes)
    monkeypatch.setattr("stock_analyzer.recommend.engine.get_ohlcv",
                        lambda *a, **k: df)
    monkeypatch.setattr("stock_analyzer.recommend.engine.get_fundamentals",
                        lambda *a, **k: {"pe_ratio": 12})
    return df


def test_scan_ranks_and_records(monkeypatch, ohlcv, tmp_path):
    _patch_data(monkeypatch, ohlcv)
    store = Store(str(tmp_path / "r.db"))
    engine = RecommendationEngine(
        strategies=[SupportResistanceStrategy()],
        consult=ConsultService(autodetect=False),
        store=store,
    )
    recs = engine.scan(["FAKE"])
    assert len(recs) == 1
    rec = recs[0]
    assert rec.action is Action.BUY
    assert rec.backtest["num_trades"] >= 0
    assert rec.consult is None  # layer disabled
    assert store.recent_signals(), "signal should be persisted"


def test_consult_disagree_penalizes_score(monkeypatch, ohlcv):
    _patch_data(monkeypatch, ohlcv)
    agree = RecommendationEngine(
        strategies=[SupportResistanceStrategy()],
        consult=ConsultService(provider=MockProvider("agree")))
    disagree = RecommendationEngine(
        strategies=[SupportResistanceStrategy()],
        consult=ConsultService(provider=MockProvider("disagree")))
    rec_agree = agree.scan(["FAKE"])[0]
    rec_disagree = disagree.scan(["FAKE"])[0]
    assert rec_disagree.score < rec_agree.score
    assert rec_disagree.consult["verdict"] == "disagree"
