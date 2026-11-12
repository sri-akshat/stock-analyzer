"""Environment-based configuration. No secrets live in source control.

Copy .env.example to .env (or export the variables) and fill in keys.
Every setting has a safe default; missing LLM keys simply disable the
consult layer rather than crashing anything.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_dotenv() -> None:
    """Minimal .env loader so we do not depend on python-dotenv."""
    env_path = Path(".env")
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


@dataclass(frozen=True)
class Settings:
    # Data layer
    cache_dir: str = os.getenv("SA_CACHE_DIR", ".cache")
    cache_ttl_minutes: int = int(os.getenv("SA_CACHE_TTL_MINUTES", "60"))
    request_pause_seconds: float = float(os.getenv("SA_REQUEST_PAUSE_SECONDS", "0.4"))

    # Backtest defaults
    initial_capital: float = float(os.getenv("SA_INITIAL_CAPITAL", "100000"))
    commission_rate: float = float(os.getenv("SA_COMMISSION_RATE", "0.001"))  # 0.1%
    slippage_rate: float = float(os.getenv("SA_SLIPPAGE_RATE", "0.0005"))     # 0.05%

    # Risk defaults (overridable per run)
    risk_tolerance: str = os.getenv("SA_RISK_TOLERANCE", "medium")  # low|medium|high
    max_exposure_per_asset: float = float(os.getenv("SA_MAX_EXPOSURE_PER_ASSET", "0.20"))
    stop_loss_pct: float = float(os.getenv("SA_STOP_LOSS_PCT", "0.05"))
    risk_per_trade: float = float(os.getenv("SA_RISK_PER_TRADE", "0.02"))

    # SOTA consult layer (all optional; layer is off when no provider key)
    llm_provider: str = os.getenv("SA_LLM_PROVIDER", "openai")  # openai|anthropic
    llm_model: str = os.getenv("SA_LLM_MODEL", "gpt-4o")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    consult_log_path: str = os.getenv("SA_CONSULT_LOG", ".cache/consults.jsonl")

    # Persistence
    db_path: str = os.getenv("SA_DB_PATH", ".cache/stock_analyzer.db")

    @property
    def consult_enabled(self) -> bool:
        if self.llm_provider == "openai":
            return bool(self.openai_api_key)
        if self.llm_provider == "anthropic":
            return bool(self.anthropic_api_key)
        return False


def get_settings() -> Settings:
    return Settings()
