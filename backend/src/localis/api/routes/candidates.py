from __future__ import annotations

import hashlib
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from localis.api.deps import _serp_singleton
from localis.core.errors import LocalisError
from localis.core.logging import get_logger
from localis.domain.schemas import Candidate, CandidatesResponse
from localis.services.serp import LocalPlace, SerpClient, SerpResult

logger = get_logger(__name__)
router = APIRouter(tags=["candidates"])

_AGGREGATOR_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "youtube.com",
    "wikipedia.org",
    "glovo.com",
    "tripadvisor.com",
    "yelp.com",
    "foursquare.com",
}


class CandidatesRequest(BaseModel):
    company: str = Field(min_length=2, max_length=120)
    city: str | None = Field(default=None, max_length=80)


def get_serp() -> SerpClient:
    return _serp_singleton()


@router.post("/candidates", response_model=CandidatesResponse)
async def list_candidates(
    payload: CandidatesRequest,
    serp: SerpClient = Depends(get_serp),
) -> CandidatesResponse:
    company = payload.company.strip()
    city = (payload.city or "").strip() or None
    if not company:
        raise HTTPException(status_code=400, detail="Nom d'entreprise requis")

    query = f"{company} {city}" if city else company
    try:
        local = await serp.search_local(company, city)
    except LocalisError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    candidates = [_candidate_from_place(p) for p in local.places if p.title]

    if not candidates:
        try:
            web = await serp.search(query)
        except LocalisError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        candidates = _extract_web_candidates(web, company)

    logger.info("candidates.found", query=query, count=len(candidates), source="maps" if local.places else "web")
    return CandidatesResponse(query=query, candidates=candidates[:6])


def _candidate_from_place(place: LocalPlace) -> Candidate:
    parts = [p for p in (place.place_type, place.address) if p]
    snippet = " · ".join(parts) or "Fiche Google Maps"
    url = place.website or (f"https://www.google.com/maps/place/?q=place_id:{place.place_id}" if place.place_id else "")
    source = _domain(url) if url else "google.com/maps"
    return Candidate(
        id=_hash(f"maps::{place.place_id or place.title}::{place.address or ''}"),
        title=place.title,
        url=url,
        snippet=snippet,
        source=source or "google.com/maps",
        address=place.address,
        rating=place.rating,
        reviews=place.reviews,
        phone=place.phone,
        place_type=place.place_type,
        thumbnail=place.thumbnail,
    )


def _extract_web_candidates(serp: SerpResult, company: str) -> list[Candidate]:
    needle = company.lower()
    seen_domains: set[str] = set()
    seen_titles: set[str] = set()
    out: list[Candidate] = []

    kg = serp.knowledge_graph or {}
    if isinstance(kg, dict) and kg.get("title"):
        kg_url = str(kg.get("website") or "")
        domain = _domain(kg_url) if kg_url else "knowledge-graph"
        snippet_parts = [
            str(kg.get("type") or ""),
            str(kg.get("address") or ""),
        ]
        out.append(
            Candidate(
                id=_hash(f"kg::{kg.get('title')}::{kg_url}"),
                title=str(kg["title"]),
                url=kg_url or "",
                snippet=" · ".join(p for p in snippet_parts if p) or "Fiche Google",
                source=domain,
                address=_str_or_none(kg.get("address")),
                rating=_float_or_none(kg.get("rating")),
            )
        )
        seen_domains.add(domain)
        seen_titles.add(str(kg["title"]).lower())

    for r in serp.organic_results:
        title = str(r.get("title") or "").strip()
        url = str(r.get("link") or "").strip()
        snippet = str(r.get("snippet") or "").strip()
        if not title or not url:
            continue

        domain = _domain(url)
        if domain in seen_domains:
            if domain in _AGGREGATOR_DOMAINS or title.lower() in seen_titles:
                continue

        haystack = f"{title} {snippet}".lower()
        if needle not in haystack and needle not in url.lower():
            continue

        out.append(
            Candidate(
                id=_hash(f"{domain}::{title}"),
                title=title,
                url=url,
                snippet=snippet[:200] if snippet else domain,
                source=domain,
            )
        )
        seen_domains.add(domain)
        seen_titles.add(title.lower())

        if len(out) >= 6:
            break

    return out


def _domain(url: str) -> str:
    try:
        host = urlparse(url).hostname or ""
    except ValueError:
        return ""
    return host.removeprefix("www.")


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:10]


def _str_or_none(v) -> str | None:
    return str(v).strip() or None if v else None


def _float_or_none(v) -> float | None:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None
