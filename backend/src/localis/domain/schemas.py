from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class ImpactLevel(StrEnum):
    critique = "critique"
    majeur = "majeur"
    modere = "modéré"
    faible = "faible"


class Potential(StrEnum):
    tres_eleve = "très élevé"
    eleve = "élevé"
    modere = "modéré"
    faible = "faible"


ActionPriority = Literal["P0", "P1", "P2", "P3"]


class Company(BaseModel):
    id_entreprise: str
    nom: str
    adresse: str
    telephone: str | None = None
    site_web: str | None = None
    categorie: str | None = None
    note_moyenne: float | None = Field(default=None, ge=0, le=5)
    nombre_avis: int | None = None


class DiagnosticItem(BaseModel):
    titre: str
    description: str
    impact: ImpactLevel | None = None
    severite: ImpactLevel | None = None
    potentiel: Potential | None = None
    impact_client: str | None = None


class Diagnostic(BaseModel):
    points_forts: list[DiagnosticItem] = Field(default_factory=list)
    points_faibles: list[DiagnosticItem] = Field(default_factory=list)
    opportunites: list[DiagnosticItem] = Field(default_factory=list)
    menaces: list[DiagnosticItem] = Field(default_factory=list)


class ShortTermAction(BaseModel):
    action: str
    description: str
    priorite: ActionPriority | None = None
    delai_jours: int | None = None
    delai_mois: int | None = None


class KPI(BaseModel):
    metrique: str
    baseline: str | float | None = None
    cible: str | float | None = None
    frequence_mesure: str | None = None


class Risk(BaseModel):
    risque: str
    probabilite: str | None = None
    impact: ImpactLevel | None = None
    mitigation: str | None = None


class ActionPlan(BaseModel):
    resume_executif: str | None = None
    court_terme: list[ShortTermAction] = Field(default_factory=list)
    moyen_terme: list[ShortTermAction] = Field(default_factory=list)
    long_terme: list[ShortTermAction] = Field(default_factory=list)
    kpis: list[KPI] | None = None
    risques: list[Risk] | None = None


class Metadata(BaseModel):
    date_analyse: datetime
    version_prompt: str = "2.0"
    modele: str | None = None
    provider: Literal["openai", "gemini"] | None = None
    temps_reponse_ms: int | None = None
    langue: str = "fr"
    id_analyse: str


class AnalysisReport(BaseModel):
    id: str
    entreprise: Company
    diagnostic: Diagnostic
    plan_action: ActionPlan
    metadonnees: Metadata


ProgressStage = Literal[
    "queued",
    "serp_started",
    "serp_done",
    "diagnostic_started",
    "diagnostic_done",
    "plan_started",
    "plan_done",
    "pdf_ready",
    "error",
]


class ProgressEvent(BaseModel):
    stage: ProgressStage
    message: str
    report_id: str | None = None
    progress: float = Field(ge=0, le=1)
    detail: dict[str, object] | None = None


class Candidate(BaseModel):
    id: str
    title: str
    url: str
    snippet: str
    source: str
    address: str | None = None
    rating: float | None = None
    reviews: int | None = None
    phone: str | None = None
    place_type: str | None = None
    thumbnail: str | None = None


class CandidatesResponse(BaseModel):
    query: str
    candidates: list[Candidate]
