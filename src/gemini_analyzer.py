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

client = genai.Client(api_key=GEMINI_API_KEY)


def prompt_plan_action(company_data: dict, swot_analysis: str = None) -> str:
    """
    Cree un plan d'action base sur les donnees ET le SWOT
    """
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
    {company_data}
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
        logger.info(f"Generation du plan d'action pour: {company_data.get('name', 'entreprise')}")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        logger.info("Plan d'action genere avec succes !")
        return response.text

    except Exception as e:
        logger.error(f"Erreur Gemini: {e}")
        return f"Erreur lors de la generation du plan: {e}"


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
           model="gemini-1.5-flash-8b",

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


def generer_plan_depuis_fichier(json_path: str, swot_analysis: str = None) -> str:
    """
    Charge un fichier JSON et genere un plan d'action

    Args:
        json_path: Chemin vers le fichier JSON
        swot_analysis: Analyse SWOT optionnelle pour enrichir le plan
    """
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            company_data = json.load(f)
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