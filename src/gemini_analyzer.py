"""
Gemini Analyzer - Generation des plans d'action et rating
"""

import os
import re
import json
from config import GEMINI_API_KEY, GROQ_API_KEY
from logger_config import logger
from groq import Groq

# Client Groq
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


# ══════════════════════════════════════════════════════════════════════════════
# ANALYSE SWOT / DIAGNOSTIC
# ══════════════════════════════════════════════════════════════════════════════
def prompt_diagnostic(company_data: dict) -> str:
    """Génère une analyse SWOT complète pour une entreprise."""
    
    company_name = company_data.get("company_name", company_data.get("company", "l'entreprise"))

    results = company_data.get("results", company_data.get("organic_results", []))
    snippets = ""
    for i, r in enumerate(results[:4], 1):
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        if title or snippet:
            snippets += f"{i}. {title}\n   {snippet}\n\n"

    if not snippets:
        snippets = "Aucune donnée de recherche disponible."

    prompt = f"""Analyse SWOT de {company_name}.

Données :
{snippets}

Réponds avec cette structure EXACTE :
POINTS FORTS:
1. [Titre] : [Description courte]
2. [Titre] : [Description courte]
3. [Titre] : [Description courte]

POINTS FAIBLES:
1. [Titre] : [Description courte]
2. [Titre] : [Description courte]

OPPORTUNITÉS:
1. [Titre] : [Description courte]
2. [Titre] : [Description courte]

MENACES:
1. [Titre] : [Description courte]
2. [Titre] : [Description courte]
"""

    logger.info(f"[SWOT] Génération pour {company_name} avec Groq...")
    
    if not groq_client:
        logger.error("Groq client non initialisé")
        return f"POINTS FORTS:\n1. Erreur: API non disponible\n\nPOINTS FAIBLES:\n1. Erreur: API non disponible\n\nOPPORTUNITÉS:\n1. Erreur: API non disponible\n\nMENACES:\n1. Erreur: API non disponible"
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000
        )
        result = response.choices[0].message.content
        logger.info(f"[SWOT OK] {company_name} → {len(result)} caractères")
        return result
    except Exception as e:
        logger.error(f"[SWOT ERREUR] {company_name}: {e}")
        return f"POINTS FORTS:\n1. Erreur: {str(e)[:100]}\n\nPOINTS FAIBLES:\n1. Erreur: {str(e)[:100]}\n\nOPPORTUNITÉS:\n1. Erreur: {str(e)[:100]}\n\nMENACES:\n1. Erreur: {str(e)[:100]}"


# ══════════════════════════════════════════════════════════════════════════════
# PLAN D'ACTION STRATÉGIQUE
# ══════════════════════════════════════════════════════════════════════════════
def prompt_plan_action(company_data: dict, swot_analysis: str = None) -> str:
    """Génère un plan d'action stratégique détaillé."""
    
    company_name = company_data.get("company_name", company_data.get("company", "l'entreprise"))

    swot_section = ""
    if swot_analysis:
        swot_section = f"\nANALYSE SWOT:\n{swot_analysis}\n"

    prompt = f"""
Tu es un expert en stratégie d'entreprise.

Entreprise: {company_name}
Données: {json.dumps(company_data, ensure_ascii=False)[:2000]}
{swot_section}

Génère un plan d'action avec cette structure EXACTE:

COURT TERME (0-3 mois):
1. [Action 1]
2. [Action 2]
3. [Action 3]

MOYEN TERME (3-6 mois):
1. [Action 1]
2. [Action 2]

LONG TERME (6-12 mois):
1. [Action 1]
2. [Action 2]
"""

    logger.info(f"[PLAN] Génération pour {company_name} avec Groq...")
    
    if not groq_client:
        logger.error("Groq client non initialisé")
        return "COURT TERME (0-3 mois):\n1. Erreur: API non disponible\n\nMOYEN TERME (3-6 mois):\n1. Erreur: API non disponible\n\nLONG TERME (6-12 mois):\n1. Erreur: API non disponible"
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000
        )
        result = response.choices[0].message.content
        logger.info(f"[PLAN OK] {company_name} → {len(result)} caractères")
        return result
    except Exception as e:
        logger.error(f"[PLAN ERREUR] {company_name}: {e}")
        return f"COURT TERME (0-3 mois):\n1. Erreur: {str(e)[:100]}\n\nMOYEN TERME (3-6 mois):\n1. Erreur: {str(e)[:100]}\n\nLONG TERME (6-12 mois):\n1. Erreur: {str(e)[:100]}"


# ══════════════════════════════════════════════════════════════════════════════
# RATING IA
# ══════════════════════════════════════════════════════════════════════════════
def generer_rating(company_data: dict, swot_analysis: str) -> dict:
    """Génère un rating avec Groq"""
    
    if not groq_client:
        return {"score": 50, "justification": "Rating non disponible"}
    
    prompt = f"""
Note cette entreprise sur 100.
Données: {json.dumps(company_data, ensure_ascii=False)[:1500]}
SWOT: {swot_analysis[:1000]}

Réponds UNIQUEMENT JSON: {{"score": 75, "justification": "..."}}
"""
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        text = response.choices[0].message.content
        text = re.sub(r"```json|```", "", text).strip()
        data = json.loads(text)
        score = max(0, min(100, int(data.get("score", 50))))
        return {"score": score, "justification": data.get("justification", "")}
    except Exception as e:
        logger.error(f"Rating erreur: {e}")
        return {"score": 50, "justification": f"Erreur: {str(e)[:100]}"}


# ══════════════════════════════════════════════════════════════════════════════
# LECTURE DEPUIS FICHIER JSON
# ══════════════════════════════════════════════════════════════════════════════
def generer_plan_depuis_fichier(json_path: str, swot_analysis: str = None) -> str:
    """Charge un fichier JSON et genere un plan d'action"""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            company_data = json.load(f)

        if "company" in company_data and "company_name" not in company_data:
            company_data["company_name"] = company_data["company"]
        if "organic_results" in company_data and "results" not in company_data:
            company_data["results"] = company_data["organic_results"]

        return prompt_plan_action(company_data, swot_analysis)
    except Exception as e:
        logger.error(f"Erreur: {e}")
        return f"Erreur: {e}"


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