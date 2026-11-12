"""The SOTA-consult service (backlog item 10).

Flow: the strategy engine produces a candidate signal; this service asks a
strong model to review it with STRUCTURED output (agree/disagree, risks,
confidence). Every call is logged as JSONL so overrides can later be
measured against outcomes (feeds the model-evaluation harness).

The layer is optional: with no provider key configured it reports itself
disabled and the rest of the product works unchanged.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ..config import get_settings
from ..types import Signal
from .providers import LLMProvider, get_provider

SYSTEM = """You are a senior risk-focused investment reviewer.
A systematic strategy has produced a candidate trade signal. Review it
skeptically: check the reasoning against the market context provided,
and look for what the strategy cannot see (events, regime shifts, data gaps).
Reply ONLY with a JSON object:
{"verdict": "agree" | "disagree" | "abstain",
 "confidence": 0.0-1.0,
 "risks": ["..."],
 "rationale": "two sentences max"}"""


@dataclass
class ConsultVerdict:
    symbol: str
    signal_action: str
    verdict: str            # agree | disagree | abstain
    confidence: float
    risks: list[str] = field(default_factory=list)
    rationale: str = ""
    provider: str = ""
    consulted_at: str = ""


class ConsultService:
    def __init__(self, provider: LLMProvider | None = None,
                 log_path: str | None = None, autodetect: bool = True):
        if provider is not None:
            self.provider = provider
        else:
            self.provider = get_provider() if autodetect else None
        self.log_path = Path(log_path or get_settings().consult_log_path)

    @property
    def enabled(self) -> bool:
        return self.provider is not None

    def review(self, symbol: str, signal: Signal, context: dict) -> ConsultVerdict | None:
        """Ask the model to review a candidate signal. Returns None when the
        consult layer is disabled."""
        if not self.enabled:
            return None

        prompt = json.dumps({
            "symbol": symbol,
            "candidate_signal": {
                "action": signal.action.value,
                "strength": signal.strength,
                "reason": signal.reason,
            },
            "market_context": context,
        }, default=str, indent=2)

        raw = self.provider.complete_json(SYSTEM, prompt)
        verdict = ConsultVerdict(
            symbol=symbol,
            signal_action=signal.action.value,
            verdict=str(raw.get("verdict", "abstain")).lower(),
            confidence=float(raw.get("confidence", 0.0)),
            risks=[str(r) for r in raw.get("risks", [])],
            rationale=str(raw.get("rationale", "")),
            provider=self.provider.name,
            consulted_at=datetime.now(timezone.utc).isoformat(),
        )
        self._log(verdict, context)
        return verdict

    def _log(self, verdict: ConsultVerdict, context: dict) -> None:
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a") as fh:
                fh.write(json.dumps({"verdict": asdict(verdict),
                                     "context_keys": sorted(context)}, default=str) + "\n")
        except Exception:
            pass  # logging must never break a run
