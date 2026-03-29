import os
from dotenv import load_dotenv
from google import genai
from logger_config import logger

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def prompt_plan_action(company_data: dict) -> str:
    """
    Crée un plan d'action basé sur les données de l'entreprise
    Args:
        company_data: Données JSON de l'entreprise (venant du Sprint 1)
    Returns:
        Plan d'action généré par Gemini
    """
    prompt = f"""
    Tu es un expert en stratégie d'entreprise et consultant senior.
    
    Voici les données collectées sur l'entreprise :
    {company_data}
    
    Sur la base de ces données, génère un plan d'action détaillé et structuré qui contient :
    
    1.  RÉSUMÉ EXÉCUTIF
       - Points clés identifiés
       - Enjeux principaux
    
    2.  OBJECTIFS PRIORITAIRES
       - Court terme (0-3 mois)
       - Moyen terme (3-6 mois)
       - Long terme (6-12 mois)
    
    3.  ACTIONS CONCRÈTES
       - Action 1 : [description, responsable, délai]
       - Action 2 : [description, responsable, délai]
       - Action 3 : [description, responsable, délai]
    
    4.  RISQUES ET MITIGATIONS
       - Risques identifiés
       - Solutions proposées
    
    5.  INDICATEURS DE SUCCÈS (KPIs)
       - Métriques à suivre
       - Seuils de performance
    
    Réponds en français, de manière professionnelle et actionnable.
    """
    
    try:
        logger.info(f"Génération du plan d'action pour: {company_data.get('name', 'entreprise')}")
        response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
        )
        logger.info("Plan d'action généré avec succès !")
        return response.text
    
    except Exception as e:
        logger.error(f"Erreur Gemini: {e}")
        return f"Erreur lors de la génération du plan: {e}"


def generer_plan_depuis_fichier(json_path: str) -> str:
    """
    Charge un fichier JSON du Sprint 1 et génère un plan d'action
    Args:
        json_path: Chemin vers le fichier JSON
    Returns:
        Plan d'action généré
    """
    import json
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            company_data = json.load(f)
        return prompt_plan_action(company_data)
    
    except FileNotFoundError:
        logger.error(f"Fichier non trouvé: {json_path}")
        return "Erreur: fichier JSON introuvable"
    except json.JSONDecodeError:
        logger.error(f"Fichier JSON invalide: {json_path}")
        return "Erreur: fichier JSON invalide"


if __name__ == "__main__":
    # Test avec les fichiers du Sprint 1
    entreprises = ["samsung", "apple", "microsoft"]
    
    for entreprise in entreprises:
        json_path = f"../data/{entreprise}_results.json"
        logger.info(f"Traitement de {entreprise}...")
        plan = generer_plan_depuis_fichier(json_path)
        print(f"\n{'='*60}")
        print(f"PLAN D'ACTION — {entreprise.upper()}")
        print('='*60)
        print(plan)