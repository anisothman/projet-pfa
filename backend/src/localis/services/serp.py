from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from serpapi import GoogleSearch
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from localis.core.errors import SerpAPIError
from localis.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class SerpResult:
    company_name: str
    organic_results: list[dict[str, Any]]
    knowledge_graph: dict[str, Any]
    related_searches: list[str]
    raw: dict[str, Any]


@dataclass(frozen=True)
class LocalPlace:
    title: str
    address: str | None
    rating: float | None
    reviews: int | None
    phone: str | None
    website: str | None
    place_type: str | None
    thumbnail: str | None
    place_id: str | None


@dataclass(frozen=True)
class LocalSearchResult:
    query: str
    places: list[LocalPlace] = field(default_factory=list)


class SerpClient:
    def __init__(self, api_key: str, hl: str = "fr", gl: str = "tn", num: int = 10) -> None:
        if not api_key:
            raise SerpAPIError("SERP_API_KEY is empty")
        self._api_key = api_key
        self._hl = hl
        self._gl = gl
        self._num = num

    async def search(self, company: str) -> SerpResult:
        raw = await asyncio.to_thread(self._search_sync, company)
        return self._extract(raw, company)

    async def search_local(self, company: str, city: str | None = None) -> LocalSearchResult:
        query = f"{company} {city}" if city else company
        raw = await asyncio.to_thread(self._maps_sync, query)
        return self._extract_local(raw, query)

    @retry(
        retry=retry_if_exception_type(SerpAPIError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def _search_sync(self, company: str) -> dict[str, Any]:
        params = {
            "q": company,
            "hl": self._hl,
            "gl": self._gl,
            "num": self._num,
            "api_key": self._api_key,
        }
        return self._call(params, context=f"search({company!r})")

    @retry(
        retry=retry_if_exception_type(SerpAPIError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def _maps_sync(self, query: str) -> dict[str, Any]:
        params = {
            "engine": "google_maps",
            "q": query,
            "type": "search",
            "hl": self._hl,
            "gl": self._gl,
            "api_key": self._api_key,
        }
        return self._call(params, context=f"maps({query!r})")

    def _call(self, params: dict[str, Any], context: str) -> dict[str, Any]:
        try:
            data = GoogleSearch(params).get_dict()
        except Exception as exc:
            logger.warning("serp.call.failed", context=context, error=str(exc))
            raise SerpAPIError(f"SerpAPI call failed ({context}): {exc}") from exc
        if "error" in data:
            raise SerpAPIError(data["error"])
        return data

    @staticmethod
    def _extract(raw: dict[str, Any], company: str) -> SerpResult:
        organic = [
            {
                "position": r.get("position"),
                "title": r.get("title"),
                "link": r.get("link"),
                "snippet": r.get("snippet"),
                "date": r.get("date"),
            }
            for r in raw.get("organic_results", [])
        ]
        return SerpResult(
            company_name=company,
            organic_results=organic,
            knowledge_graph=raw.get("knowledge_graph") or {},
            related_searches=[
                item.get("query", "")
                for item in raw.get("related_searches", [])
                if item.get("query")
            ],
            raw=raw,
        )

    @staticmethod
    def _extract_local(raw: dict[str, Any], query: str) -> LocalSearchResult:
        places: list[LocalPlace] = []
        place_results = raw.get("place_results")
        if isinstance(place_results, dict) and place_results.get("title"):
            places.append(_local_place(place_results))
        for item in raw.get("local_results") or []:
            if not isinstance(item, dict):
                continue
            places.append(_local_place(item))
        return LocalSearchResult(query=query, places=places)


def _local_place(item: dict[str, Any]) -> LocalPlace:
    return LocalPlace(
        title=str(item.get("title") or "").strip(),
        address=_clean(item.get("address")),
        rating=_safe_float(item.get("rating")),
        reviews=_safe_int(item.get("reviews")),
        phone=_clean(item.get("phone")),
        website=_clean(item.get("website") or item.get("links", {}).get("website") if isinstance(item.get("links"), dict) else item.get("website")),
        place_type=_clean(item.get("type")),
        thumbnail=_clean(item.get("thumbnail")),
        place_id=_clean(item.get("place_id")),
    )


def _clean(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _safe_float(v: Any) -> float | None:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _safe_int(v: Any) -> int | None:
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None
