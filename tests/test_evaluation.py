from stock_analyzer.consult.advisor import ConsultVerdict
from stock_analyzer.evaluation import performance_report, record_outcome
from stock_analyzer.persistence import Store


def test_performance_report_splits_by_verdict(tmp_path):
    store = Store(str(tmp_path / "e.db"))
    s1 = store.record_signal("AMD", "composite", "buy", 0.8, "r1")
    s2 = store.record_signal("MSFT", "composite", "buy", 0.7, "r2")
    store.record_consult(ConsultVerdict("AMD", "buy", "agree", 0.9, [], "ok", "mock"))
    store.record_consult(ConsultVerdict("MSFT", "buy", "disagree", 0.8, ["risk"], "no", "mock"))
    record_outcome(store, "AMD", s1, pnl_pct=5.0)
    record_outcome(store, "MSFT", s2, pnl_pct=-3.0)

    report = performance_report(store)
    assert report["by_strategy"]["composite"]["n"] == 2
    assert report["by_consult_verdict"]["agree"]["avg_pnl_pct"] == 5.0
    assert report["by_consult_verdict"]["disagree"]["avg_pnl_pct"] == -3.0
