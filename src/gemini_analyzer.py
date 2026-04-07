"""
Gemini Analyzer - Generation des plans d'action et rating
Responsable: Maram
Sprint 3 - Ajout du rating IA
"""

import os
import re
import json
from google import genai
from config import GEMINI_API_KEY
from logger_config import logger

# Client Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

# ══════════════════════════════════════════════════════════════════════════════
# ANALYSE SWOT / DIAGNOSTIC
# ══════════════════════════════════════════════════════════════════════════════
def prompt_diagnostic(company_data: dict) -> str:
    """
    Génère une analyse SWOT complète pour une entreprise.

    Args:
        company_data : Données structurées issues de SerpAPI (sprint 1)
                       Clés attendues : company_name, results (liste de snippets)

    Returns:
        Texte de l'analyse SWOT généré par Gemini
    """
    company_name = company_data.get("company_name", company_data.get("company", "l'entreprise"))

    # Préparer les extraits de recherche (max 8 pour rester dans les limites)
    results = company_data.get("results", company_data.get("organic_results", []))
    snippets = ""
    for i, r in enumerate(results[:4], 1):
        title   = r.get("title", "")
        snippet = r.get("snippet", "")
        if title or snippet:
            snippets += f"{i}. {title}\n   {snippet}\n\n"

    if not snippets:
        snippets = "Aucune donnée de recherche disponible."

    prompt = f"""Analyse SWOT de {company_name} (max 300 mots).

Données :
{snippets}

Réponds avec cette structure :
POINTS FORTS:
1. [Titre] : [1 phrase]
2. [Titre] : [1 phrase]
3. [Titre] : [1 phrase]

POINTS FAIBLES:
1. [Titre] : [1 phrase]
2. [Titre] : [1 phrase]

OPPORTUNITÉS:
1. [Titre] : [1 phrase]
2. [Titre] : [1 phrase]

MENACES:
1. [Titre] : [1 phrase]
2. [Titre] : [1 phrase]

CONCLUSION:
[2 phrases max]
"""

    logger.info(f"[DIAGNOSTIC] Génération SWOT pour {company_name}...")
    try:
        result = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        logger.info(f"[DIAGNOSTIC OK] {company_name} → {len(result.text)} caractères")
        return result.text
    except Exception as e:
        logger.error(f"[DIAGNOSTIC ERREUR] {company_name}: {e}")
        return f"Erreur lors de la génération du diagnostic pour {company_name}: {e}"


# ══════════════════════════════════════════════════════════════════════════════
# PLAN D'ACTION STRATÉGIQUE
# ══════════════════════════════════════════════════════════════════════════════
def prompt_plan_action(company_data: dict, swot_analysis: str = None) -> str:
    """
    Génère un plan d'action stratégique détaillé.

    Args:
        company_data  : Données structurées de l'entreprise
        swot_analysis : Analyse SWOT préalable (optionnel, enrichit le plan)

    Returns:
        Texte du plan d'action généré par Gemini
    """
    company_name = company_data.get("company_name", company_data.get("company", "l'entreprise"))

    # Contexte SWOT si disponible
    swot_section = ""
    if swot_analysis:
        swot_section = f"""
    ============================================================
    ANALYSE SWOT PREALABLE (a utiliser pour le plan d'action) :
    ============================================================
    {swot_analysis}
    ============================================================

    IMPORTANT: Base ton plan d'action sur les points faibles et opportunites
    identifies dans le SWOT ci-dessus.
    """

    prompt = f"""
    Tu es un expert en strategie d'entreprise et consultant senior.

    Voici les donnees collectees sur l'entreprise :
    {json.dumps(company_data, ensure_ascii=False, indent=2)[:3000]}
    {swot_section}

    Sur la base de ces donnees, genere un plan d'action detaille et structure.

    STRUCTURE OBLIGATOIRE :

    1. RESUME EXECUTIF
    2. OBJECTIFS PRIORITAIRES
       - Court terme (0-3 mois)
       - Moyen terme (3-6 mois)
       - Long terme (6-12 mois)
    3. ACTIONS CONCRETES (minimum 3)
    4. RISQUES ET MITIGATIONS
    5. INDICATEURS DE SUCCES (KPIs)

    Reponds en francais, de maniere professionnelle et actionnable.
    """

    try:
        logger.info(f"Generation du plan d'action pour: {company_name}")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        logger.info("Plan d'action genere avec succes !")
        return response.text

    except Exception as e:
        logger.error(f"[PLAN ACTION ERREUR] {company_name}: {e}")
        return f"Erreur lors de la génération du plan pour {company_name}: {e}"


# ══════════════════════════════════════════════════════════════════════════════
# RATING IA (SPRINT 3)
# ══════════════════════════════════════════════════════════════════════════════
def generer_rating(company_data: dict, swot_analysis: str) -> dict:
    """
    Demande a Gemini de generer une note globale sur 100 pour l'entreprise
    basee sur les donnees et le SWOT.

    Returns:
        dict avec 'score' (int) et 'justification' (str)
    """
    prompt = f"""
    Tu es un analyste financier et strategique expert.

    Voici les donnees de l'entreprise :
    {json.dumps(company_data, ensure_ascii=False, indent=2)[:3000]}

    Voici l'analyse SWOT :
    {swot_analysis[:2000]}

    Donne une note globale de performance et de sante strategique de cette entreprise sur 100.

    CRITERES D'EVALUATION :
    - Position concurrentielle (20 pts)
    - Solidite financiere (20 pts)
    - Innovation et technologie (20 pts)
    - Satisfaction client et reputation (20 pts)
    - Potentiel de croissance (20 pts)

    REPONDS UNIQUEMENT avec ce format JSON exact, rien d'autre :
    {{
      "score": 74,
      "justification": "Courte justification en une phrase."
    }}
    """

    try:
        logger.info("Generation du rating Gemini...")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        raw = response.text.strip()

        # Nettoyer les backticks markdown si presents
        raw = re.sub(r"```json|```", "", raw).strip()

        data = json.loads(raw)
        score = int(data.get("score", 50))
        score = max(0, min(100, score))  # Clamp entre 0 et 100

        logger.info(f"Rating genere : {score}/100")
        return {
            "score": score,
            "justification": data.get("justification", "")
        }

    except Exception as e:
        logger.error(f"Erreur generation rating: {e}")
        return {"score": 50, "justification": "Rating non disponible"}


# ══════════════════════════════════════════════════════════════════════════════
# LECTURE DEPUIS FICHIER JSON
# ══════════════════════════════════════════════════════════════════════════════
def generer_plan_depuis_fichier(json_path: str, swot_analysis: str = None) -> str:
    """
    Charge un fichier JSON et genere un plan d'action

    Args:
        json_path     : Chemin vers le fichier JSON de l'entreprise
        swot_analysis : Analyse SWOT optionnelle pour enrichir le plan

    Returns:
        Texte du plan d'action
    """
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            company_data = json.load(f)

        # Normaliser la structure (sprint 1 utilise "company", diagnostic_engine "company_name")
        if "company" in company_data and "company_name" not in company_data:
            company_data["company_name"] = company_data["company"]
        if "organic_results" in company_data and "results" not in company_data:
            company_data["results"] = company_data["organic_results"]

        return prompt_plan_action(company_data, swot_analysis)

    except FileNotFoundError:
        logger.error(f"Fichier non trouve: {json_path}")
        return "Erreur: fichier JSON introuvable"
    except json.JSONDecodeError:
        logger.error(f"Fichier JSON invalide: {json_path}")
        return "Erreur: fichier JSON invalide"


if __name__ == "__main__":
    entreprises = ["samsung", "apple", "microsoft"]

    for entreprise in entreprises:
        json_path = f"data/{entreprise}_results.json"
        logger.info(f"Traitement de {entreprise}...")
        plan = generer_plan_depuis_fichier(json_path)
        print(f"\n{'='*60}")
        print(f"PLAN D'ACTION - {entreprise.upper()}")
        print('='*60)
        print(plan)