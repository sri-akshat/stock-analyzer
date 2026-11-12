"""LLM providers for the consult layer. Keys come from the environment
only; a provider that has no key is simply unavailable, never crashy.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod

from ..config import get_settings


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    def available(self) -> bool: ...

    @abstractmethod
    def complete_json(self, system: str, prompt: str) -> dict:
        """Return the model's reply parsed as a JSON object."""


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self):
        settings = get_settings()
        self._key = settings.openai_api_key
        self._model = settings.llm_model

    def available(self) -> bool:
        return bool(self._key)

    def complete_json(self, system: str, prompt: str) -> dict:
        from openai import OpenAI  # lazy: the package is an optional extra

        client = OpenAI(api_key=self._key)
        resp = client.chat.completions.create(
            model=self._model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return json.loads(resp.choices[0].message.content)


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self):
        settings = get_settings()
        self._key = settings.anthropic_api_key
        self._model = settings.llm_model

    def available(self) -> bool:
        return bool(self._key)

    def complete_json(self, system: str, prompt: str) -> dict:
        import anthropic

        client = anthropic.Anthropic(api_key=self._key)
        resp = client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(resp.content[0].text)


class MockProvider(LLMProvider):
    """Deterministic provider for tests and offline demos."""

    name = "mock"

    def __init__(self, verdict: str = "agree"):
        self._verdict = verdict
        self.calls: list[str] = []

    def available(self) -> bool:
        return True

    def complete_json(self, system: str, prompt: str) -> dict:
        self.calls.append(prompt)
        return {
            "verdict": self._verdict,
            "confidence": 0.5,
            "risks": ["mock provider - no real analysis"],
            "rationale": "deterministic test double",
        }


def get_provider(name: str | None = None) -> LLMProvider | None:
    settings = get_settings()
    name = name or settings.llm_provider
    providers: dict[str, type[LLMProvider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
    }
    cls = providers.get(name)
    if cls is None:
        return None
    provider = cls()
    return provider if provider.available() else None
