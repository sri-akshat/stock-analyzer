from stock_analyzer.consult.advisor import ConsultVerdict
from stock_analyzer.persistence import Store


def test_store_round_trip(tmp_path):
    store = Store(str(tmp_path / "test.db"))
    sid = store.record_signal("AMD", "composite", "buy", 0.8, "near support",
                              {"sharpe": 0.7, "total_return_pct": 5.2})
    assert sid > 0
    store.record_consult(ConsultVerdict(
        symbol="AMD", signal_action="buy", verdict="agree", confidence=0.7,
        risks=["earnings next week"], rationale="setup is clean", provider="mock"))
    store.record_decision("AMD", "took", signal_id=sid, note="paper trade")

    recent = store.recent_signals()
    assert len(recent) == 1
    assert recent[0]["symbol"] == "AMD"
    assert '"sharpe": 0.7' in recent[0]["backtest_metrics"]
    assert store.consult_agreement() == {"agree": 1}
