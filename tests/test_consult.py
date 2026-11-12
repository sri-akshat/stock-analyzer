import json

from stock_analyzer.consult import ConsultService
from stock_analyzer.consult.providers import MockProvider
from stock_analyzer.types import Action, Signal


def test_consult_disabled_without_provider(tmp_path):
    svc = ConsultService(autodetect=False, log_path=str(tmp_path / "c.jsonl"))
    assert not svc.enabled
    assert svc.review("AMD", Signal(Action.BUY, 0.8, "test"), {}) is None


def test_consult_reviews_and_logs(tmp_path):
    log = tmp_path / "consults.jsonl"
    provider = MockProvider(verdict="disagree")
    svc = ConsultService(provider=provider, log_path=str(log))
    verdict = svc.review("AMD", Signal(Action.BUY, 0.8, "near support"),
                         {"price": 100, "backtest_metrics": {"sharpe": 0.7}})
    assert verdict is not None
    assert verdict.verdict == "disagree"
    assert provider.calls, "provider should have been called"

    lines = log.read_text().strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["verdict"]["verdict"] == "disagree"
    assert record["context_keys"] == ["backtest_metrics", "price"]


def test_consult_log_failure_does_not_crash():
    svc = ConsultService(provider=MockProvider(), log_path="/nonexistent-dir/deep/c.jsonl")
    verdict = svc.review("AMD", Signal(Action.SELL, 0.5, "x"), {})
    assert verdict is not None
