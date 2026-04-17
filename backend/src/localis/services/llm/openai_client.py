"""OpenAI client using the async SDK. Uses JSON-mode response_format for reliable JSON output."""

from __future__ import annotations

import time

from openai import APIError, AsyncOpenAI, RateLimitError

from localis.core.errors import LLMError, LLMQuotaError
from localis.core.logging import get_logger
from localis.services.llm.base import LLMResponse

logger = get_logger(__name__)


class OpenAIClient:
    provider = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        if not api_key:
            raise LLMError("OPENAI_API_KEY missing")
        self._client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def complete_json(self, prompt: str) -> LLMResponse:
        start = time.monotonic()
        try:
            resp = await self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
        except RateLimitError as exc:
            raise LLMQuotaError(f"OpenAI rate limit / quota: {exc}") from exc
        except APIError as exc:
            # 429 on a non-RateLimitError codepath still means quota.
            if getattr(exc, "status_code", None) == 429:
                raise LLMQuotaError(f"OpenAI 429: {exc}") from exc
            raise LLMError(f"OpenAI API error: {exc}") from exc

        latency_ms = int((time.monotonic() - start) * 1000)
        text = resp.choices[0].message.content or ""
        logger.info("llm.openai.ok", model=self.model, latency_ms=latency_ms)
        return LLMResponse(
            text=text, model=self.model, provider=self.provider, latency_ms=latency_ms
        )
