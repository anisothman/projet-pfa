"""Gemini client using the new google-genai SDK. Runs the sync SDK call on a thread."""

from __future__ import annotations

import asyncio
import time

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from localis.core.errors import LLMError, LLMQuotaError
from localis.core.logging import get_logger
from localis.services.llm.base import LLMResponse

logger = get_logger(__name__)


class GeminiClient:
    provider = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        if not api_key:
            raise LLMError("GEMINI_API_KEY missing")
        self._client = genai.Client(api_key=api_key)
        self.model = model

    async def complete_json(self, prompt: str) -> LLMResponse:
        start = time.monotonic()
        try:
            resp = await asyncio.to_thread(
                self._client.models.generate_content,
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
        except genai_errors.APIError as exc:
            # Gemini surfaces quota / rate-limit as RESOURCE_EXHAUSTED or 429.
            code = getattr(exc, "code", None)
            status = getattr(exc, "status", "")
            if code == 429 or "RESOURCE_EXHAUSTED" in str(status) or "quota" in str(exc).lower():
                raise LLMQuotaError(f"Gemini quota: {exc}") from exc
            raise LLMError(f"Gemini API error: {exc}") from exc

        latency_ms = int((time.monotonic() - start) * 1000)
        text = resp.text or ""
        logger.info("llm.gemini.ok", model=self.model, latency_ms=latency_ms)
        return LLMResponse(
            text=text, model=self.model, provider=self.provider, latency_ms=latency_ms
        )
