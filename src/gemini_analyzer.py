"""
╔══════════════════════════════════════════════════════════════╗
║  gemini_analyzer.py — Sprint 2 : Analyse IA                 ║
║  Utilisé par : diagnostic_engine.py                         ║
║  Dépend de   : gemini_client.py (Anis)                      ║
╚══════════════════════════════════════════════════════════════╝

Ce module contient les fonctions d'analyse métier :
  - prompt_diagnostic()     → génère l'analyse SWOT
  - prompt_plan_action()    → génère le plan d'action stratégique
  - generer_plan_depuis_fichier() → lecture JSON + génération plan
"""

import json
import logging
from pathlib import Path

from gemini_client import call_gemini

logger = logging.getLogger("projet-pfa")


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
        result = call_gemini(prompt)
        logger.info(f"[DIAGNOSTIC OK] {company_name} → {len(result)} caractères")
        return result
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
    swot_context = ""
    if swot_analysis:
        swot_context = f"""
Analyse SWOT préalable :
{swot_analysis[:1500]}

En tenant compte de cette analyse, """
    else:
        swot_context = "En te basant sur tes connaissances de l'entreprise, "

    prompt = f"""Plan d'action stratégique pour {company_name} (max 300 mots).

{swot_context}

Structure requise :
RÉSUMÉ EXÉCUTIF:
[2 phrases]

ACTIONS COURT TERME (0-3 mois):
1. [Action] | Priorité: P0 | [département]
2. [Action] | Priorité: P1 | [département]

ACTIONS MOYEN TERME (3-6 mois):
1. [Action] | Priorité: P1 | [département]
2. [Action] | Priorité: P2 | [département]

ACTIONS LONG TERME (6-12 mois):
1. [Action] | Priorité: P2 | [département]

KPIs:
- [Métrique] : cible [valeur]
- [Métrique] : cible [valeur]

RISQUES:
1. [Risque] | Impact: [niveau] | Mitigation: [action]
"""

    logger.info(f"[PLAN ACTION] Génération pour {company_name}...")
    try:
        result = call_gemini(prompt)
        logger.info(f"[PLAN ACTION OK] {company_name} → {len(result)} caractères")
        return result
    except Exception as e:
        logger.error(f"[PLAN ACTION ERREUR] {company_name}: {e}")
        return f"Erreur lors de la génération du plan pour {company_name}: {e}"


# ══════════════════════════════════════════════════════════════════════════════
# LECTURE DEPUIS FICHIER JSON
# ══════════════════════════════════════════════════════════════════════════════
def generer_plan_depuis_fichier(json_path: str, swot_analysis: str = None) -> str:
    """
    Génère un plan d'action en lisant les données depuis un fichier JSON (sprint 1).

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
        logger.error(f"[FICHIER INTROUVABLE] {json_path}")
        return f"Erreur: Fichier {json_path} non trouvé"
    except json.JSONDecodeError as e:
        logger.error(f"[JSON INVALIDE] {json_path}: {e}")
        return f"Erreur: Fichier {json_path} n'est pas un JSON valide"
    except Exception as e:
        logger.error(f"[ERREUR] generer_plan_depuis_fichier: {e}")
        return f"Erreur lors de la génération: {e}"