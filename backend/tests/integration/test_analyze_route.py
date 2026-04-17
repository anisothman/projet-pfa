"""End-to-end test of POST /analyze with mocked SerpAPI and LLM.

Asserts the pipeline produces a valid AnalysisReport and stores it, and that
GET /reports/{id} serves it back. The quota-fallback path is covered by the
router unit tests; this is about wiring.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from localis.api import deps
from localis.main import app
from localis.services.diagnostic import ReportStore
from localis.services.llm.router import LLMRouter
from localis.services.serp import SerpClient, SerpResult
from tests.conftest import FakeLLMClient


class StubSerp(SerpClient):
    def __init__(self) -> None:
        self._api_key = "stub"
        self._hl = "fr"
        self._gl = "tn"
        self._num = 10

    async def search(self, company: str) -> SerpResult:  # type: ignore[override]
        return SerpResult(
            company_name=company,
            organic_results=[
                {
                    "position": 1,
                    "title": f"{company} Official",
                    "snippet": "Leading brand",
                    "link": "https://example.com",
                    "date": None,
                },
                {
                    "position": 2,
                    "title": "Reviews",
                    "snippet": "Mostly positive reviews",
                    "link": "https://rev.test",
                    "date": None,
                },
            ],
            knowledge_graph={
                "title": company,
                "address": "Tunis, TN",
                "rating": 4.4,
                "user_reviews": 2000,
            },
            related_searches=["similar"],
            raw={},
        )


SWOT_JSON = json.dumps(
    {
        "points_forts": [
            {"titre": "Brand", "description": "Strong brand awareness", "impact": "majeur"}
        ],
        "points_faibles": [
            {"titre": "SAV", "description": "Slow response times", "severite": "modéré"}
        ],
        "opportunites": [{"titre": "Digital", "description": "E-commerce growth"}],
        "menaces": [{"titre": "Concurrence", "description": "New entrants"}],
    }
)

PLAN_JSON = json.dumps(
    {
        "resume_executif": "Digitaliser",
        "court_terme": [
            {
                "action": "Fix SAV",
                "description": "Reduce SLA to 24h",
                "priorite": "P0",
                "delai_jours": 30,
            }
        ],
        "moyen_terme": [
            {"action": "E-shop", "description": "Launch MVP", "priorite": "P1", "delai_mois": 4}
        ],
        "long_terme": [{"action": "Go EU", "description": "Expand", "priorite": "P2"}],
        "kpis": [
            {"metrique": "NPS", "baseline": "30", "cible": "55", "frequence_mesure": "mensuel"}
        ],
        "risques": [
            {"risque": "Budget", "probabilite": "modéré", "impact": "majeur", "mitigation": "Phase"}
        ],
    }
)


class ScriptedLLM(FakeLLMClient):
    """Returns SWOT_JSON on 1st call, PLAN_JSON on 2nd."""

    def __init__(self) -> None:
        super().__init__(provider="openai", model="gpt-4o-mini")
        self._responses = [SWOT_JSON, PLAN_JSON]

    async def complete_json(self, prompt: str):
        self.call_count += 1
        from localis.services.llm.base import LLMResponse

        text = self._responses.pop(0) if self._responses else "{}"
        return LLMResponse(text=text, model=self.model, provider=self.provider, latency_ms=1)


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Override singletons with stubs for this test."""
    store = ReportStore(reports_dir=tmp_path)
    serp = StubSerp()
    llm_router = LLMRouter(primary=ScriptedLLM(), fallback=None)

    from localis.services.diagnostic import DiagnosticService
    from localis.services.pdf.builder import PDFReportBuilder

    diag = DiagnosticService(serp=serp, llm=llm_router)

    app.dependency_overrides[deps.get_diagnostic_service] = lambda: diag
    app.dependency_overrides[deps.get_store] = lambda: store
    app.dependency_overrides[deps.get_pdf_builder] = lambda: PDFReportBuilder()

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_analyze_sync_returns_report(client):
    resp = client.post("/analyze", json={"company": "Acme"})
    assert resp.status_code == 200, resp.text
    data: dict[str, Any] = resp.json()

    assert data["entreprise"]["nom"] == "Acme"
    assert len(data["diagnostic"]["points_forts"]) == 1
    assert data["plan_action"]["court_terme"][0]["priorite"] == "P0"
    report_id = data["id"]

    # Report persisted and retrievable.
    resp2 = client.get(f"/reports/{report_id}")
    assert resp2.status_code == 200
    assert resp2.json()["id"] == report_id


def test_get_pdf(client):
    resp = client.post("/analyze", json={"company": "Acme"})
    report_id = resp.json()["id"]

    pdf_resp = client.get(f"/reports/{report_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF-")


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
