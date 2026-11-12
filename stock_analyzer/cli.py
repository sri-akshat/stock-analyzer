"""Command line entry point.

  python -m stock_analyzer.cli backtest AMD --strategy composite --period 2y
  python -m stock_analyzer.cli walkforward AMD --strategy composite --period 4y
  python -m stock_analyzer.cli recommend AMD MSFT NVDA --strategy composite
"""
from __future__ import annotations

import argparse
import json

from .backtest import BacktestEngine, walk_forward
from .data import get_ohlcv
from .recommend import RecommendationEngine
from .strategies import STRATEGIES


def _strategy(name: str):
    cls = STRATEGIES.get(name)
    if cls is None:
        raise SystemExit(f"unknown strategy {name!r}; choices: {', '.join(STRATEGIES)}")
    return cls()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="stock-analyzer")
    sub = parser.add_subparsers(dest="command", required=True)

    p_bt = sub.add_parser("backtest", help="point-in-time backtest of one symbol")
    p_bt.add_argument("symbol")
    p_bt.add_argument("--strategy", default="composite", choices=list(STRATEGIES))
    p_bt.add_argument("--period", default="2y")
    p_bt.add_argument("--market", default=None, help="'NS' for NSE tickers")

    p_wf = sub.add_parser("walkforward", help="walk-forward out-of-sample validation")
    p_wf.add_argument("symbol")
    p_wf.add_argument("--strategy", default="composite", choices=list(STRATEGIES))
    p_wf.add_argument("--period", default="4y")
    p_wf.add_argument("--folds", type=int, default=3)
    p_wf.add_argument("--market", default=None)

    p_rc = sub.add_parser("recommend", help="scan symbols and rank suggestions")
    p_rc.add_argument("symbols", nargs="+")
    p_rc.add_argument("--strategy", default="composite", choices=list(STRATEGIES))
    p_rc.add_argument("--period", default="2y")
    p_rc.add_argument("--market", default=None)
    p_rc.add_argument("--no-consult", action="store_true", help="skip the SOTA consult layer")

    args = parser.parse_args(argv)

    if args.command == "backtest":
        df = get_ohlcv(args.symbol, period=args.period, market=args.market)
        if df.empty:
            print(f"no data for {args.symbol}")
            return 1
        result = BacktestEngine().run(args.symbol, df, _strategy(args.strategy))
        print(json.dumps(result.metrics, indent=2))
        for t in result.trades[-10:]:
            print(f"{t.timestamp.date()}  {t.action.value.upper():4s} {t.quantity:5d} @ {t.price:9.2f}  {t.reason}")
        return 0

    if args.command == "walkforward":
        df = get_ohlcv(args.symbol, period=args.period, market=args.market)
        if df.empty:
            print(f"no data for {args.symbol}")
            return 1
        folds = walk_forward(args.symbol, df, _strategy(args.strategy), n_folds=args.folds)
        for f in folds:
            print(f"fold {f.fold}: train [{f.train_start.date()}..{f.train_end.date()}] "
                  f"-> OOS [{f.test_start.date()}..{f.test_end.date()}] "
                  f"return {f.out_of_sample.metrics.get('total_return_pct')}% "
                  f"sharpe {f.out_of_sample.metrics.get('sharpe')}")
            if f.best_params:
                print(f"  tuned weights: {f.best_params}")
        return 0

    if args.command == "recommend":
        engine = RecommendationEngine(strategies=[_strategy(args.strategy)],
                                      period=args.period)
        if args.no_consult:
            from .consult import ConsultService
            engine.consult = ConsultService(autodetect=False)
        recs = engine.scan(args.symbols, market=args.market)
        if not recs:
            print("no actionable signals today")
            return 0
        for r in recs:
            line = (f"{r.symbol:12s} {r.action.value.upper():4s} "
                    f"strength={r.strength:.2f} score={r.score:.2f} | {r.reason}")
            print(line)
            print(f"  backtest: return {r.backtest.get('total_return_pct')}% "
                  f"sharpe {r.backtest.get('sharpe')} maxDD {r.backtest.get('max_drawdown_pct')}%")
            if r.consult:
                print(f"  SOTA consult: {r.consult['verdict']} "
                      f"(confidence {r.consult['confidence']}) - {r.consult['rationale']}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
