"""Orchestration: SerpAPI → diagnostic (SWOT) → action plan → build AnalysisReport.

"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from localis.core.errors import CompanyNotFoundError
from localis.core.logging import get_logger
from localis.domain.schemas import (
    ActionPlan,
    AnalysisReport,
    Company,
    Diagnostic,
    Metadata,
    ProgressEvent,
)
from localis.services.llm.router import LLMRouter
from localis.services.parsing import parse_model
from localis.services.serp import SerpClient, SerpResult

logger = get_logger(__name__)


# -- Prompts (JSON-mode) --------------------------------------------------------

SWOT_PROMPT = """Tu es un expert en analyse stratégique d'entreprises.

Entreprise: {company}

Données collectées (Google / SerpAPI):
{context}

Produis une analyse SWOT en JSON strict, respectant EXACTEMENT ce schéma :

{{
  "points_forts":   [{{ "titre": str, "description": str, "impact": "critique"|"majeur"|"modéré"|"faible" }}],
  "points_faibles": [{{ "titre": str, "description": str, "severite": "critique"|"majeur"|"modéré"|"faible", "impact_client": str }}],
  "opportunites":   [{{ "titre": str, "description": str, "potentiel": "très élevé"|"élevé"|"modéré"|"faible" }}],
  "menaces":        [{{ "titre": str, "description": str, "impact": "critique"|"majeur"|"modéré"|"faible" }}]
}}

Contraintes:
- 3 points forts, 3 points faibles, 2 opportunités, 2 menaces minimum.
- Titre court (< 60 caractères), description précise (80–200 caractères).
- Français. Réponds UNIQUEMENT par l'objet JSON, sans texte autour.
"""


PLAN_PROMPT = """Tu es un consultant en stratégie expérimenté. Tu es CONCRET et SPÉCIFIQUE.

Entreprise: {company}
Analyse SWOT déjà produite: {swot}

Produis un plan d'action JSON strict respectant ce schéma :

{{
  "resume_executif": str,
  "court_terme":  [{{ "action": str, "description": str, "priorite": "P0"|"P1"|"P2"|"P3", "delai_jours": int }}],
  "moyen_terme":  [{{ "action": str, "description": str, "priorite": "P0"|"P1"|"P2"|"P3", "delai_mois": int }}],
  "long_terme":   [{{ "action": str, "description": str, "priorite": "P0"|"P1"|"P2"|"P3" }}],
  "kpis":    [{{ "metrique": str, "baseline": str, "cible": str, "frequence_mesure": str }}],
  "risques": [{{ "risque": str, "probabilite": "faible"|"modéré"|"élevé", "impact": "critique"|"majeur"|"modéré"|"faible", "mitigation": str }}]
}}

Contraintes sur les ACTIONS :
- 3 actions court terme (P0-P1), 2 moyen terme, 2 long terme.
- Chaque action nomme un LIVRABLE concret (ex : "Lancer la carte Ramadan avec 4 nouveaux menus", pas "Améliorer l'offre").
- Évite les verbes creux ("optimiser", "améliorer", "renforcer") sans objet précis.

Contraintes sur les KPIs (3 au total, CRITIQUE) :
- Les métriques doivent être SPÉCIFIQUES au secteur de l'entreprise. Interdit : "satisfaction client", "part de marché", "chiffre d'affaires" (trop génériques, sauf si vraiment pertinents).
- Privilégie des indicateurs opérationnels : panier moyen, taux d'abandon panier, NPS, coût d'acquisition (CAC), LTV, taux de ré-achat, délai moyen de livraison, taux d'occupation, couverture géographique, MAU/DAU, taux de conversion, nombre d'avis ≥ 4★, vitesse de préparation, marge brute par produit, etc.
- Chaque KPI inclut une UNITÉ (€, %, jours, minutes, nb/mois, ★/5…) dans baseline ET cible.
- Les 3 KPIs doivent se concentrer sur 3 dimensions DIFFÉRENTES (ex : opération + commercial + produit), pas 3 facettes du même thème.

Contraintes sur les RISQUES (2) :
- Chaque risque est spécifique (pas "concurrence accrue" générique — dis QUELLE concurrence).
- La mitigation est une action, pas un vœu.

Français. Réponds UNIQUEMENT par l'objet JSON, sans texte autour.
"""


# -- Diagnostic service ---------------------------------------------------------


class DiagnosticService:
    def __init__(self, serp: SerpClient, llm: LLMRouter) -> None:
        self._serp = serp
        self._llm = llm

    async def run(self, company: str, city: str | None = None) -> AnalysisReport:
        """Non-streaming variant — runs the pipeline end-to-end and returns the final report."""
        events: list[ProgressEvent] = []
        async for evt in self.run_streaming(company, city=city):
            events.append(evt)
        # Last event should carry the report id; we'll load from the service cache in the API layer.
        # For direct use, rebuild the report from the stream's final payload.
        final = next((e for e in reversed(events) if e.stage == "pdf_ready"), None)
        if final is None or not final.detail or "report" not in final.detail:
            raise RuntimeError("Pipeline completed without a final report payload")
        return AnalysisReport.model_validate(final.detail["report"])

    async def run_streaming(
        self, company: str, city: str | None = None
    ) -> AsyncIterator[ProgressEvent]:
        """Yield ProgressEvent values as the pipeline progresses.

        Stages: queued → serp_started → serp_done → diagnostic_started → diagnostic_done
                → plan_started → plan_done → pdf_ready.

        `city` (optionnel) est ajouté à la requête Google et au contexte LLM pour
        désambiguïser les entreprises locales (ex. "KFC" vs "KFC Tunis").
        """
        t0 = time.monotonic()
        report_id = uuid.uuid4().hex[:12]
        display = f"{company}{f' — {city}' if city else ''}"
        yield ProgressEvent(
            stage="queued", message=f"Analyse de {display}", progress=0.0, report_id=report_id
        )

        # 1. SerpAPI
        yield ProgressEvent(
            stage="serp_started",
            message="Interrogation de Google…",
            progress=0.05,
            report_id=report_id,
        )
        query = f"{company} {city}" if city else company
        serp_result = await self._serp.search(query)

        # Garde-fou : refuser de générer si Google ne renvoie pas assez de signal métier,
        # sinon le LLM invente un rapport (ex. un prénom -> une entreprise fictive).
        confidence, reason = _assess_match(serp_result, company)
        if confidence == "insufficient":
            logger.info("diagnostic.insufficient_match", query=query, reason=reason)
            raise CompanyNotFoundError(
                f"Aucune entreprise trouvée pour « {display} ». "
                f"Vérifiez l'orthographe ou ajoutez une ville. "
                f"(Raison : {reason})"
            )

        yield ProgressEvent(
            stage="serp_done",
            message=f"{len(serp_result.organic_results)} résultats récupérés",
            progress=0.25,
            report_id=report_id,
        )

        # 2. SWOT
        yield ProgressEvent(
            stage="diagnostic_started",
            message="Génération du SWOT…",
            progress=0.30,
            report_id=report_id,
        )
        context = _format_serp_context(serp_result)
        swot_prompt = SWOT_PROMPT.format(company=display, context=context)
        swot_resp = await self._llm.complete_json(swot_prompt)
        diagnostic = parse_model(swot_resp.text, Diagnostic)
        yield ProgressEvent(
            stage="diagnostic_done",
            message="Analyse SWOT prête",
            progress=0.60,
            report_id=report_id,
            detail={"provider": swot_resp.provider, "model": swot_resp.model},
        )

        # 3. Action plan
        yield ProgressEvent(
            stage="plan_started",
            message="Plan d'action en cours…",
            progress=0.65,
            report_id=report_id,
        )
        plan_prompt = PLAN_PROMPT.format(
            company=display,
            swot=diagnostic.model_dump_json(exclude_none=True)[:2000],
        )
        plan_resp = await self._llm.complete_json(plan_prompt)
        plan = parse_model(plan_resp.text, ActionPlan)
        yield ProgressEvent(
            stage="plan_done",
            message="Plan d'action prêt",
            progress=0.90,
            report_id=report_id,
            detail={"provider": plan_resp.provider, "model": plan_resp.model},
        )

        # 4. Assemble report
        report = AnalysisReport(
            id=report_id,
            entreprise=_build_company(serp_result),
            diagnostic=diagnostic,
            plan_action=plan,
            metadonnees=Metadata(
                date_analyse=datetime.now(UTC),
                version_prompt="2.0",
                modele=plan_resp.model,
                provider=plan_resp.provider,  # type: ignore[arg-type]
                temps_reponse_ms=int((time.monotonic() - t0) * 1000),
                id_analyse=report_id,
            ),
        )
        yield ProgressEvent(
            stage="pdf_ready",
            message="Rapport prêt",
            progress=1.0,
            report_id=report_id,
            detail={"report": report.model_dump(mode="json")},
        )


# -- Helpers --------------------------------------------------------------------


# Signaux "business" typiques d'un knowledge-graph Google Business ou d'une fiche entreprise.
_BUSINESS_KG_KEYS = {"address", "phone", "website", "rating", "reviews", "user_reviews", "hours", "type"}


def _assess_match(serp: SerpResult, company: str) -> tuple[str, str]:
    """Détermine si les résultats SerpAPI contiennent assez de signal métier pour l'analyse.

    Retourne ("ok", "") quand l'entreprise semble réellement identifiée, ou
    ("insufficient", raison) pour bloquer la suite du pipeline.

    Heuristique stricte (on préfère refuser que d'inventer) :
      1. Knowledge Graph Google avec titre correspondant au nom.
      2. OU site officiel évident (domaine qui reprend le nom).
      3. OU 4+ mentions organiques dont au moins une sur plateforme métier.
      4. OU 5+ mentions organiques (marque très présente).
    Les prénoms, noms communs et typos tombent hors de toutes ces règles.
    """
    kg = serp.knowledge_graph or {}
    needle = company.strip().lower()
    if not needle:
        return "insufficient", "requête vide"

    # Règle 1 : Knowledge Graph Google avec titre correspondant
    if isinstance(kg, dict) and kg:
        kg_title = str(kg.get("title") or "").lower()
        kg_signals = sum(1 for k in kg if k in _BUSINESS_KG_KEYS)
        if kg_signals >= 2 and (needle in kg_title or kg_title in needle):
            return "ok", ""

    organic = serp.organic_results or []
    if not organic:
        return "insufficient", "aucun résultat Google"

    def _mentions(r: dict) -> bool:
        title = str(r.get("title") or "").lower()
        snippet = str(r.get("snippet") or "").lower()
        link = str(r.get("link") or "").lower()
        return needle in title or needle in snippet or needle in link

    def _domain_matches(r: dict) -> bool:
        """Le domaine ressemble-t-il au nom de l'entreprise (ex. samsung.com pour 'Samsung') ?"""
        link = str(r.get("link") or "").lower()
        compact = needle.replace(" ", "").replace("-", "").replace("'", "")
        return len(compact) >= 4 and compact in link

    matches = [r for r in organic if _mentions(r)]

    # Règle 2 : site officiel évident
    if any(_domain_matches(r) and _mentions(r) for r in organic):
        return "ok", ""

    # Règle 3 : 4+ mentions avec au moins un lien plateforme métier
    business_platforms = (
        "facebook.com",
        "instagram.com",
        "linkedin.com",
        "google.com/maps",
        "tripadvisor",
        "tiktok.com",
        "yelp",
    )
    has_business_link = any(
        any(p in str(r.get("link") or "").lower() for p in business_platforms) for r in matches
    )
    if len(matches) >= 4 and has_business_link:
        return "ok", ""

    # Règle 4 : marque très présente (5+ mentions)
    if len(matches) >= 5:
        return "ok", ""

    return (
        "insufficient",
        f"{len(matches)} mention(s) du nom sur {len(organic)} résultat(s), "
        f"ni fiche Google ni site officiel",
    )


def _format_serp_context(serp: SerpResult, max_results: int = 6) -> str:
    """Render the SerpAPI results as a compact context block for the LLM."""
    lines: list[str] = []
    for i, r in enumerate(serp.organic_results[:max_results], 1):
        title = r.get("title") or ""
        snippet = r.get("snippet") or ""
        if title or snippet:
            lines.append(f"{i}. {title}\n   {snippet}")
    if serp.knowledge_graph:
        kg = serp.knowledge_graph
        kg_bits = [f"{k}: {v}" for k, v in kg.items() if isinstance(v, (str, int, float))][:8]
        if kg_bits:
            lines.append("Knowledge graph: " + "; ".join(kg_bits))
    return "\n\n".join(lines) or "Aucun résultat exploitable."


def _build_company(serp: SerpResult) -> Company:
    kg: dict[str, Any] = serp.knowledge_graph or {}
    return Company(
        id_entreprise=str(kg.get("kgmid") or uuid.uuid4().hex[:8]),
        nom=kg.get("title") or serp.company_name,
        adresse=kg.get("address") or "Adresse non renseignée",
        telephone=kg.get("phone"),
        site_web=kg.get("website"),
        categorie=kg.get("type"),
        note_moyenne=_safe_float(kg.get("rating")),
        nombre_avis=_safe_int(kg.get("user_reviews")),
    )


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


# -- Report store ---------------------------------------------------------------


class ReportStore:
    """File-backed persistence for AnalysisReport. No DB per 'light' community scope."""

    def __init__(self, reports_dir) -> None:
        from pathlib import Path

        self._dir = Path(reports_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def save(self, report: AnalysisReport) -> None:
        path = self._dir / f"{report.id}.json"
        path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        logger.info("report.saved", report_id=report.id, path=str(path))

    def load(self, report_id: str) -> AnalysisReport | None:
        path = self._dir / f"{report_id}.json"
        if not path.exists():
            return None
        return AnalysisReport.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def pdf_path(self, report_id: str):
        return self._dir / f"{report_id}.pdf"
