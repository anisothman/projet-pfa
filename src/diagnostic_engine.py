"""
diagnostic_engine.py - Sprint 2
Moteur de diagnostic complet avec SWOT, Plan d'action et Rating
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional

# Configuration du logger
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import des modules
try:
    from prompt_diagnostic import PromptDiagnostic
    from gemini_analyzer import prompt_plan_action, generer_rating, groq_client
    logger.info("✅ Modules importés avec succès")
except ImportError as e:
    logger.error(f"Erreur import: {e}")
    PromptDiagnostic = None
    prompt_plan_action = None
    generer_rating = None
    groq_client = None


class DiagnosticEngine:
    def __init__(self, data_dir=None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).parent.parent / "data"
        
        self.prompt_diagnostic = PromptDiagnostic() if PromptDiagnostic else None
        logger.info(f"DiagnosticEngine initialisé avec data_dir: {self.data_dir}")
    
    def load_company_data(self, company_name: str) -> Optional[Dict]:
        json_path = self.data_dir / f"{company_name.lower()}_results.json"
        if not json_path.exists():
            logger.error(f"Fichier non trouvé: {json_path}")
            return None
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Normalisation
        if "company" in data and "company_name" not in data:
            data["company_name"] = data["company"]
        if "organic_results" in data and "results" not in data:
            data["results"] = data["organic_results"]
        
        return data
    
    def generate_swot(self, company_name: str, data: Dict) -> str:
        """Génère le SWOT en utilisant l'IA"""
        try:
            if self.prompt_diagnostic:
                prompt = self.prompt_diagnostic.create_diagnostic_prompt(data)
                
                if groq_client:
                    response = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        max_tokens=1500
                    )
                    result = response.choices[0].message.content
                    logger.info(f"SWOT généré pour {company_name}")
                    return result
                else:
                    return self._fallback_swot(company_name)
            else:
                return self._fallback_swot(company_name)
        except Exception as e:
            logger.error(f"Erreur génération SWOT: {e}")
            return self._fallback_swot(company_name)
    
    def _fallback_swot(self, company_name: str) -> str:
        return f"""
ANALYSE SWOT DE {company_name.upper()}:

FORCES:
- Innovation technologique
- Marque reconnue mondialement
- Équipe talentueuse

FAIBLESSES:
- Dépendance à certains marchés
- Prix premium

OPPORTUNITES:
- Expansion dans les marchés émergents
- Nouveaux segments de clientèle

MENACES:
- Concurrence intense
- Réglementations strictes
"""
    
    def analyze_company(self, company_name: str) -> Dict:
        data = self.load_company_data(company_name)
        
        if not data:
            return {
                "success": False,
                "error": f"Entreprise '{company_name}' non trouvee"
            }
        
        # Générer SWOT
        swot = self.generate_swot(company_name, data)
        
        # Générer plan d'action
        plan = ""
        if prompt_plan_action:
            try:
                plan = prompt_plan_action(data, swot)
                logger.info(f"Plan d'action généré pour {company_name}")
            except Exception as e:
                logger.error(f"Erreur plan action: {e}")
                plan = self._fallback_plan(company_name)
        else:
            plan = self._fallback_plan(company_name)
        
        # Générer rating
        rating = {"score": 50, "justification": "Non disponible"}
        if generer_rating:
            try:
                rating = generer_rating(data, swot)
                logger.info(f"Rating généré: {rating.get('score')}/100")
            except Exception as e:
                logger.error(f"Erreur rating: {e}")
        
        return {
            "success": True,
            "company_name": company_name,
            "swot": swot,
            "action_plan": plan,
            "rating": rating,
            "data_source": str(self.data_dir / f"{company_name}_results.json")
        }
    
    def _fallback_plan(self, company_name: str) -> str:
        return f"""
COURT TERME (0-3 mois):
- Analyser les données web collectées
- Identifier les axes d'amélioration

MOYEN TERME (3-6 mois):
- Développer une stratégie digitale
- Optimiser la présence en ligne

LONG TERME (6-12 mois):
- Leader sur les marchés cibles
- Innover en continu
"""


def quick_analyze(company_name: str, data_dir: str = None):
    engine = DiagnosticEngine(data_dir)
    return engine.analyze_company(company_name)


if __name__ == "__main__":
    engine = DiagnosticEngine()
    result = engine.analyze_company("apple")
    print("SWOT:", result["swot"][:200])
    print("PLAN:", result["action_plan"][:200])
    print("RATING:", result["rating"])