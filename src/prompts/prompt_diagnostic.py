"""
Module de création des prompts diagnostiques
Responsable: Isra
Sprint 2 - Analyse IA (Gemini)
"""

import json
import logging
from typing import Dict, Any
from datetime import datetime

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
            "company_name": "str",
            "search_date": "str",
            "strengths": ["str"],  # Points forts
            "weaknesses": ["str"],  # Points faibles
            "opportunities": ["str"],  # Opportunités
            "threats": ["str"],  # Menaces (SWOT)
            "market_position": "str",  # Position sur le marché
            "digital_presence": "str",  # Présence digitale
            "reputation_score": "int (0-100)",
            "recommendations": ["str"],  # Recommandations
            "analysis_timestamp": "str"
        }
    
    def create_diagnostic_prompt(self, company_data: Dict[str, Any]) -> str:
        """
        Crée un prompt pour générer un diagnostic complet
        
        Args:
            company_data: Données de l'entreprise (résultats de recherche JSON)
            
        Returns:
            Prompt structuré pour Gemini
        """
        company_name = company_data.get("company_name", "Unknown")
        search_results = company_data.get("results", [])
        
        # Créer un texte avec les résultats
        search_text = "\n".join([
            f"- {result.get('title', 'N/A')}: {result.get('snippet', 'N/A')}"
            for result in search_results[:10]  # Top 10 résultats
        ])
        
        prompt = f"""
Tu es un analyste d'affaires expert. Analyse les données suivantes sur l'entreprise et génère un diagnostic complet.

ENTREPRISE: {company_name}
DATE D'ANALYSE: {datetime.now().strftime("%Y-%m-%d")}

DONNÉES DE RECHERCHE:
{search_text}

TÂCHE:
1. Analysez la présence en ligne et la réputation de l'entreprise
2. Identifiez les forces (forces), faiblesses (weaknesses), opportunités et menaces (SWOT)
3. Évaluez la position sur le marché (0-100)
4. Déterminez la qualité de la présence digitale
5. Calculez un score de réputation (0-100)
6. Proposez des recommandations d'amélioration

RÉPONDEZ EN JSON avec la structure suivante:
{{
    "company_name": "{company_name}",
    "search_date": "{datetime.now().isoformat()}",
    "strengths": [liste des points forts],
    "weaknesses": [liste des points faibles],
    "opportunities": [liste des opportunités],
    "threats": [liste des menaces],
    "market_position": "description",
    "digital_presence": "évaluation (Excellente/Bonne/Moyenne/Faible)",
    "reputation_score": score_0_100,
    "recommendations": [liste des recommandations],
    "analysis_timestamp": "{datetime.now().isoformat()}"
}}

Soyez précis et basez-vous uniquement sur les données fournies.
"""
        
        logger.info(f"Prompt diagnostic créé pour: {company_name}")
        return prompt
    
    def create_multi_company_diagnostic_prompt(self, companies_data: list) -> str:
        """
        Crée un prompt pour comparer plusieurs entreprises
        
        Args:
            companies_data: Liste des données d'entreprises
            
        Returns:
            Prompt pour analyse comparative
        """
        companies_text = ""
        for i, company in enumerate(companies_data, 1):
            companies_text += f"\n### ENTREPRISE {i}: {company.get('company_name', 'Unknown')}\n"
            results = company.get('results', [])
            for result in results[:5]:  # Top 5 par entreprise
                companies_text += f"- {result.get('title')}: {result.get('snippet')}\n"
        
        prompt = f"""
Tu es un expert en analyse comparative d'entreprises. Analyse et compare les entreprises suivantes:

{companies_text}

TÂCHE:
1. Pour chaque entreprise: diagnostic SWOT
2. Comparaison: qui est leader? qui a les meilleures opportunités?
3. Positionnement relatif sur le marché
4. Recommandations stratégiques pour chacune

RÉPONDEZ EN JSON:
{{
    "analysis_date": "{datetime.now().isoformat()}",
    "comparison_overview": "vue d'ensemble",
    "companies": [
        {{
            "name": "nom",
            "strengths": [],
            "weaknesses": [],
            "market_position": 0-100,
            "reputation_score": 0-100
        }}
    ],
    "competitive_analysis": "analyse compétitive",
    "market_leader": "entreprise dominante",
    "recommendations": []
}}
"""
        
        logger.info(f"Prompt comparatif créé pour {len(companies_data)} entreprises")
        return prompt
    
    def validate_prompt(self, prompt: str) -> bool:
        """Valide que le prompt est bien structuré"""
        required_keywords = [
            "analyse", "diagnostic", "JSON", "recommandations"
        ]
        return all(keyword.lower() in prompt.lower() for keyword in required_keywords)
    
    def save_prompt_template(self, prompt: str, filename: str = None) -> str:
        """Sauvegarde le template du prompt"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"src/prompts/diagnostic_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(prompt)
            logger.info(f"Prompt template sauvegardé: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du prompt: {str(e)}")
            raise
    
    def get_schema(self) -> Dict[str, Any]:
        """Retourne le schéma du diagnostic"""
        return self.diagnostic_schema


if __name__ == "__main__":
    # Exemple d'utilisation
    example_company = {
        "company_name": "TechCorp Tunisia",
        "results": [
            {
                "position": 1,
                "title": "TechCorp - Innovations Digitales",
                "snippet": "Leader en transformation digitale en Tunisie...",
            },
            {
                "position": 2,
                "title": "TechCorp Services Cloud",
                "snippet": "Solutions cloud pour entreprises tunisiennes...",
            }
        ]
    }
    
    # Créer le diagnostic
    prompt_creator = PromptDiagnostic()
    prompt = prompt_creator.create_diagnostic_prompt(example_company)
    
    print("=" * 50)
    print("PROMPT GÉNÉRÉ:")
    print("=" * 50)
    print(prompt)
    
    # Valider
    if prompt_creator.validate_prompt(prompt):
        print("\n✓ Prompt valide!")
    else:
        print("\n✗ Prompt invalide!")
    
    # Afficher le schéma
    print("\nSCHÉMA DE DIAGNOSTIC:")
    print(json.dumps(prompt_creator.get_schema(), indent=2))