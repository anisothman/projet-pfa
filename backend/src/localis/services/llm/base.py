"""LLM client protocol — a minimal async interface both providers implement.

The router (localis.services.llm.router) depends only on this protocol, not on
any concrete provider, which is what enables seamless fallback.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str
    provider: str
    latency_ms: int


@runtime_checkable
class LLMClient(Protocol):
    """Async JSON-producing LLM client.

    Implementations must raise LLMQuotaError on rate-limit / quota errors so
    the router can trigger provider fallback. Other failures should raise
    LLMError (wrapping the underlying SDK exception).
    """

    provider: str
    model: str

    async def complete_json(self, prompt: str) -> LLMResponse:
        """Send `prompt`, return text the model produced (expected JSON).

        The parsing layer is responsible for extracting JSON from the response.
        """
        ...
