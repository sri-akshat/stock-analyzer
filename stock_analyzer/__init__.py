"""stock_analyzer: backtested strategies that suggest investments.

Layers:
    data       - market data, fundamentals, news (cached, rate-limited)
    indicators - causal technical indicators (no lookahead)
    strategies - pluggable Strategy interface producing Signals
    risk       - position sizing, stop losses, exposure limits
    backtest   - point-in-time engine, metrics, walk-forward validation
    consult    - optional SOTA model review of candidate signals
    recommend  - scans a universe and ranks suggestions
    persistence- SQLite store for signals, consults and outcomes
"""

__version__ = "0.2.0"
