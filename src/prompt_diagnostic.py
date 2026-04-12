# Créer et écrire dans le fichier

"""
Module de création des prompts diagnostiques - VERSION OPTIMISÉE
Responsable optimisation: Nourhene
Sprint 2 - Optimisation du prompt Gemini
"""

import json
import logging
import re
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Configuration du logger
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/prompt_diagnostic.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PromptDiagnostic:
    """Classe pour créer et gérer les prompts de diagnostic"""

    def __init__(self):
        self.prompt_template = None
        self.diagnostic_schema = self._define_schema()

    def _define_schema(self) -> Dict[str, Any]:
        """Définit le schéma du diagnostic"""
        return {
            "entreprise": {
                "nom": "str",
                "categorie": "str",
                "adresse": "str",
                "site_web": "str",
            },
            "diagnostic": {
                "points_forts": ["str"],
                "points_faibles": ["str"],
                "opportunites": ["str"],
                "menaces": ["str"]
            },
            "score_reputation": "int (0-100)",
            "recommandations": ["str"]
        }

    def create_diagnostic_prompt(self, company_data: Dict[str, Any]) -> str:
        """Crée un prompt pour générer un diagnostic complet"""
        
        # Extraire le nom de l'entreprise
        company_name = company_data.get("company_name") or company_data.get("name") or "Entreprise"
        
        # Extraire les résultats de recherche
        results = company_data.get("results", [])
        resultats_texte = "\n".join([
            f"  • {r.get('title', '')}: {r.get('snippet', '')}"
            for r in results[:5]
        ]) or "  • Aucun résultat disponible"

        prompt = f"""Tu es un expert en analyse d'entreprises.
Effectue un diagnostic complet de l'entreprise suivante.

Entreprise: {company_name}

Résultats de recherche:
{resultats_texte}

INSTRUCTIONS:
1. Identifie 3 POINTS FORTS
2. Identifie 3 POINTS FAIBLES
3. Identifie 2 OPPORTUNITÉS
4. Identifie 2 MENACES
5. Calcule un SCORE DE RÉPUTATION (0-100)
6. Propose 3 RECOMMANDATIONS

RÉPONDS UNIQUEMENT EN JSON:
{{
    "company_name": "{company_name}",
    "points_forts": ["point 1", "point 2", "point 3"],
    "points_faibles": ["point 1", "point 2", "point 3"],
    "opportunites": ["opportunité 1", "opportunité 2"],
    "menaces": ["menace 1", "menace 2"],
    "score_reputation": 75,
    "recommandations": ["recommandation 1", "recommandation 2", "recommandation 3"]
}}"""

        logger.info(f"Prompt créé pour: {company_name}")
        return prompt

    def validate_prompt(self, prompt: str) -> bool:
        """Valide que le prompt est correct"""
        if len(prompt) < 100:
            return False
        if "JSON" not in prompt:
            return False
        if "{" not in prompt or "}" not in prompt:
            return False
        logger.info("Prompt valide!")
        return True

    def clean_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """Nettoie la réponse de Gemini"""
        if not response_text:
            return {"erreur": "Réponse vide"}
        
        # Nettoyer les backticks
        cleaned = response_text.replace("```json", "").replace("```", "").strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.error("Erreur parsing JSON")
            return {"erreur": "JSON invalide"}

    def validate_gemini_response(self, response: Dict[str, Any]) -> bool:
        """Valide la réponse de Gemini"""
        champs_requis = ["company_name", "points_forts", "points_faibles", "score_reputation", "recommandations"]
        
        for champ in champs_requis:
            if champ not in response:
                raise KeyError(f"Champ manquant: {champ}")
        
        if not isinstance(response.get("points_forts"), list):
            raise TypeError("'points_forts' doit être une liste")
        
        if not isinstance(response.get("score_reputation"), int):
            raise TypeError("'score_reputation' doit être un nombre")
        
        logger.info("Réponse valide!")
        return True

    def get_schema(self) -> Dict[str, Any]:
        """Retourne le schéma"""
        return self.diagnostic_schema


if __name__ == "__main__":
    example_company = {
        "company_name": "Samsung",
        "results": [
            {"title": "Samsung Officiel", "snippet": "Produits électroniques"},
            {"title": "Samsung Tech", "snippet": "Innovation technologique"}
        ]
    }

    creator = PromptDiagnostic()
    prompt = creator.create_diagnostic_prompt(example_company)
    
    if creator.validate_prompt(prompt):
        print(" Prompt valide!")
    else:
        print(" Prompt invalide!")
