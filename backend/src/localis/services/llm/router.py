"""Provider-fallback router — the fix for the unresolved quota bug in commit 000079a.

On LLMQuotaError from the primary, falls through to the secondary. Generic LLMError
(non-quota failures) gets a small number of retries with exponential backoff via tenacity.
If both providers fail, the last exception is raised.
"""

from __future__ import annotations

from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from localis.core.config import Settings
from localis.core.errors import LLMError, LLMQuotaError
from localis.core.logging import get_logger
from localis.services.llm.base import LLMClient, LLMResponse
from localis.services.llm.gemini import GeminiClient
from localis.services.llm.openai_client import OpenAIClient

logger = get_logger(__name__)


class LLMRouter:
    def __init__(self, primary: LLMClient, fallback: LLMClient | None = None) -> None:
        self.primary = primary
        self.fallback = fallback

    @property
    def providers(self) -> list[str]:
        return [self.primary.provider] + ([self.fallback.provider] if self.fallback else [])

    async def complete_json(self, prompt: str) -> LLMResponse:
        try:
            return await _retryable_call(self.primary, prompt)
        except LLMQuotaError as exc:
            if not self.fallback:
                logger.warning("llm.primary.quota.nofallback", provider=self.primary.provider)
                raise
            logger.warning(
                "llm.primary.quota.falling_back",
                primary=self.primary.provider,
                fallback=self.fallback.provider,
                reason=str(exc),
            )
            return await _retryable_call(self.fallback, prompt)
        except LLMError as exc:
            if not self.fallback:
                raise
            logger.warning(
                "llm.primary.error.falling_back",
                primary=self.primary.provider,
                fallback=self.fallback.provider,
                reason=str(exc),
            )
            return await _retryable_call(self.fallback, prompt)


def _is_transient(exc: BaseException) -> bool:
    """Retry transient non-quota LLM errors; let quota errors bubble up so the router can fall over."""
    return isinstance(exc, LLMError) and not isinstance(exc, LLMQuotaError)


@retry(
    retry=retry_if_exception(_is_transient),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
async def _retryable_call(client: LLMClient, prompt: str) -> LLMResponse:
    """Transient LLMError gets retried; LLMQuotaError propagates immediately so router can fall over."""
    return await client.complete_json(prompt)


def build_router(settings: Settings) -> LLMRouter:
    """Construct a router from settings. Picks primary per settings.llm_primary; uses the other as fallback if its key is set."""
    openai_client = (
        OpenAIClient(settings.openai_api_key, model=settings.openai_model)
        if settings.openai_api_key
        else None
    )
    gemini_client = (
        GeminiClient(settings.gemini_api_key, model=settings.gemini_model)
        if settings.gemini_api_key
        else None
    )

    if settings.llm_primary == "openai":
        primary, fallback = openai_client, gemini_client
    else:
        primary, fallback = gemini_client, openai_client

    if primary is None:
        # Requested primary not configured — promote whatever exists.
        primary, fallback = fallback, None
    if primary is None:
        raise LLMError("No LLM provider configured (need OPENAI_API_KEY or GEMINI_API_KEY)")

    logger.info(
        "llm.router.built",
        primary=primary.provider,
        fallback=fallback.provider if fallback else None,
    )
    return LLMRouter(primary=primary, fallback=fallback)
