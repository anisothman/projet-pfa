import os
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


def generer_plan_depuis_fichier(json_path: str, swot_analysis: str = None) -> str:
    """
    Charge un fichier JSON et genere un plan d'action
    
    Args:
        json_path: Chemin vers le fichier JSON
        swot_analysis: Analyse SWOT optionnelle pour enrichir le plan
    """
    import json
    
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