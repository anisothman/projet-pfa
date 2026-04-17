"""Tests for the LLM router — the fix for the unresolved quota bug."""

import pytest

from localis.core.errors import LLMError, LLMQuotaError
from localis.services.llm.router import LLMRouter
from tests.conftest import FakeLLMClient, make_quota_raising_client

pytestmark = pytest.mark.asyncio


async def test_primary_success_no_fallback_called():
    primary = FakeLLMClient(provider="openai", payload='{"ok": true}')
    fallback = FakeLLMClient(provider="gemini", payload='{"ok": false}')
    router = LLMRouter(primary=primary, fallback=fallback)

    resp = await router.complete_json("hi")

    assert resp.text == '{"ok": true}'
    assert primary.call_count == 1
    assert fallback.call_count == 0


async def test_primary_quota_falls_over_to_fallback():
    primary = make_quota_raising_client(permanent=True)
    fallback = FakeLLMClient(provider="gemini", payload='{"via": "gemini"}')
    router = LLMRouter(primary=primary, fallback=fallback)

    resp = await router.complete_json("hi")

    assert resp.text == '{"via": "gemini"}'
    assert primary.call_count == 1
    assert fallback.call_count == 1


async def test_primary_quota_no_fallback_propagates():
    primary = make_quota_raising_client(permanent=True)
    router = LLMRouter(primary=primary, fallback=None)

    with pytest.raises(LLMQuotaError):
        await router.complete_json("hi")


async def test_primary_generic_error_falls_over():
    primary = FakeLLMClient(provider="openai", raise_exc=LLMError("boom"))
    fallback = FakeLLMClient(provider="gemini", payload='{"ok": true}')
    router = LLMRouter(primary=primary, fallback=fallback)

    resp = await router.complete_json("hi")

    assert resp.provider == "gemini"
    assert fallback.call_count == 1


async def test_both_quota_raises_second():
    primary = make_quota_raising_client(provider="openai", permanent=True)
    fallback = make_quota_raising_client(provider="gemini", permanent=True)
    router = LLMRouter(primary=primary, fallback=fallback)

    with pytest.raises(LLMQuotaError):
        await router.complete_json("hi")

    assert primary.call_count == 1
    assert fallback.call_count == 1
