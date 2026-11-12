# Stock Analyzer

Deploys backtested strategies to **suggest** investments, with an optional
SOTA model consult layer that reviews each candidate signal to maximize
profit and mitigate losses. Recommendations only - nothing here places
real trades.

## What's inside

| Layer | Module | What it does |
| --- | --- | --- |
| Data | `stock_analyzer/data/` | yfinance OHLCV with caching + pacing, NSE support (`.NS`), fundamentals, news (yfinance, Finviz fallback) |
| Indicators | `stock_analyzer/indicators.py` | Causal technicals: SMA/EMA, RSI, MACD, ATR, rolling support/resistance |
| Strategies | `stock_analyzer/strategies/` | Pluggable `Strategy` interface: support/resistance, momentum, mean reversion, composite (technical + sentiment + fundamental votes) |
| Risk | `stock_analyzer/risk/` | Position sizing (2% risk budget, exposure cap, cash), 5% stop losses |
| Backtest | `stock_analyzer/backtest/` | Point-in-time engine (no lookahead, next-open fills), true metrics, walk-forward validation with train-only tuning |
| Consult | `stock_analyzer/consult/` | SOTA model reviews each signal: agree/disagree + risks + confidence, every call logged |
| Recommend | `stock_analyzer/recommend/` | Scans a universe, ranks suggestions by signal strength x backtest evidence |
| Persist | `stock_analyzer/persistence/` | SQLite: signals, consults, decisions, outcomes, paper portfolio |
| Paper | `stock_analyzer/paper.py` | Virtual fills and portfolio tracking before real money |
| Jobs | `stock_analyzer/jobs.py` | `daily_scan` for cron/CI scheduling |
| Eval | `stock_analyzer/evaluation/` | Measures whether SOTA consults beat the raw strategy over time |
| Dashboard | `dashboard/app.py` | Streamlit: signals, history, paper portfolio, backtest explorer |

## Setup

```bash
pip install -e '.[dev]'        # core + tests
pip install -e '.[llm,dashboard,sentiment]'   # optional extras
cp .env.example .env           # fill in keys; never commit .env
```

## Use it

```bash
# point-in-time backtest
python -m stock_analyzer.cli backtest AMD --strategy composite --period 2y

# walk-forward out-of-sample validation (the number to trust)
python -m stock_analyzer.cli walkforward AMD --strategy composite --period 4y

# scan a universe for today's suggestions
python -m stock_analyzer.cli recommend AMD MSFT NVDA

# NSE
python -m stock_analyzer.cli backtest RELIANCE --market NS

# daily job (schedule with cron / GitHub Actions)
python -m stock_analyzer.jobs AMD MSFT NVDA

# dashboard
streamlit run dashboard/app.py
```

## SOTA consult layer

Off by default. Set `OPENAI_API_KEY` (default provider, model `gpt-4o`) or
`SA_LLM_PROVIDER=anthropic` + `ANTHROPIC_API_KEY` in `.env`. Every review
is logged and stored, so `stock_analyzer/evaluation/` can tell you whether
the model's agrees/disagrees actually make money.

## Testing

```bash
pytest -q    # 30 tests, all offline (synthetic data)
```

## Notes

- `legacy/` holds the archived prototype for reference; it is not
  importable and its previously hardcoded API keys have been scrubbed
  (rotate them at the providers - they remain in git history on main).
- Backtests execute at the next bar's open with commission + slippage,
  and support/resistance use trailing windows only. Treat any backtest
  without those properties as fiction.

### CI and coverage

The `Tests and package build` GitHub Actions workflow runs on pushes to `main`
and `feature/**`, and on pull requests to `main`:

- Offline tests on Python 3.10 and 3.12, with coverage for the whole
  `stock_analyzer` package (including branch coverage).
- Coverage tables in the job logs and GitHub job summaries, plus downloadable
  XML and HTML reports under each run's artifacts.
- Source distribution and wheel builds, package metadata checks, and a clean
  wheel-install/import smoke test. Built packages are available as artifacts;
  nothing is published to PyPI.

Run the same coverage check locally:

```bash
pip install -e '.[dev]'
python -m pytest -q --cov=stock_analyzer --cov-branch --cov-report=term-missing --cov-report=html
```

Coverage is reported without a minimum threshold. External data providers,
optional LLM providers, CLI and scheduled-job paths are not fully covered yet.
