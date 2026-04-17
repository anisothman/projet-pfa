"""Shared fixtures — fake LLM clients, canned reports, temp report store."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

# Set stub env vars before anything from localis imports, so that settings.check_keys()
# run during FastAPI lifespan in integration tests doesn't fail.
os.environ.setdefault("OPENAI_API_KEY", "test-openai")
os.environ.setdefault("SERP_API_KEY", "test-serp")
os.environ.setdefault("LOG_LEVEL", "WARNING")

import pytest  # noqa: E402

from localis.core.errors import LLMQuotaError  # noqa: E402
from localis.domain.schemas import (  # noqa: E402
    ActionPlan,
    AnalysisReport,
    Company,
    Diagnostic,
    DiagnosticItem,
    ImpactLevel,
    Metadata,
    ShortTermAction,
)
from localis.services.llm.base import LLMResponse  # noqa: E402


@pytest.fixture(autouse=True, scope="session")
def _clear_settings_cache():
    """Make sure any cached Settings() read env vars set above."""
    from localis.core.config import get_settings

    get_settings.cache_clear()
    yield


@dataclass
class FakeLLMClient:
    """Programmable LLM client for tests. Can raise or return on demand."""

    provider: str = "fake"
    model: str = "fake-1"
    payload: str = "{}"
    raise_exc: Exception | None = None  # persistent — raised on every call
    call_count: int = 0

    async def complete_json(self, prompt: str) -> LLMResponse:
        self.call_count += 1
        if self.raise_exc:
            raise self.raise_exc
        return LLMResponse(
            text=self.payload, model=self.model, provider=self.provider, latency_ms=1
        )


def make_quota_raising_client(provider: str = "openai", permanent: bool = True) -> FakeLLMClient:
    """FakeLLMClient pre-wired to raise LLMQuotaError. `permanent` kept for backward-compat — raises every call now."""
    _ = permanent
    return FakeLLMClient(provider=provider, raise_exc=LLMQuotaError("test quota"))


@pytest.fixture
def sample_report(tmp_path: Path) -> AnalysisReport:
    return AnalysisReport(
        id="abc123",
        entreprise=Company(
            id_entreprise="e1",
            nom="Acme Corp",
            adresse="1 Rue du Test, Tunis",
            note_moyenne=4.3,
            nombre_avis=128,
        ),
        diagnostic=Diagnostic(
            points_forts=[
                DiagnosticItem(
                    titre="Marque forte", description="Notoriété élevée", impact=ImpactLevel.majeur
                )
            ],
            points_faibles=[
                DiagnosticItem(
                    titre="SAV lent",
                    description="Délais de réponse longs",
                    severite=ImpactLevel.modere,
                )
            ],
            opportunites=[DiagnosticItem(titre="E-commerce", description="Canal en croissance")],
            menaces=[DiagnosticItem(titre="Concurrence", description="Nouveaux entrants")],
        ),
        plan_action=ActionPlan(
            resume_executif="Accélérer le digital",
            court_terme=[
                ShortTermAction(
                    action="Réduire SLA SAV",
                    description="Passer à 24h",
                    priorite="P0",
                    delai_jours=30,
                )
            ],
            moyen_terme=[
                ShortTermAction(
                    action="Lancer boutique en ligne",
                    description="MVP",
                    priorite="P1",
                    delai_mois=4,
                )
            ],
            long_terme=[
                ShortTermAction(action="International", description="UE puis MENA", priorite="P2")
            ],
        ),
        metadonnees=Metadata(
            date_analyse=datetime.now(UTC),
            modele="fake-1",
            provider="openai",
            id_analyse="abc123",
        ),
    )
