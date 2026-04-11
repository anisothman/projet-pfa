"""
diagnostic_engine.py - Sprint 2
Moteur de diagnostic complet avec SWOT, Plan d'action et Rating
Intègre: PromptDiagnostic + Gemini Analyzer
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/diagnostic_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===== IMPORT DES MODULES =====
# Essaye différentes méthodes d'import
PromptDiagnostic = None
prompt_plan_action = None
generer_rating = None
groq_client = None

# Méthode 1: Import relatif (même dossier)
try:
    from .prompt_diagnostic import PromptDiagnostic
    from .gemini_analyzer import prompt_plan_action, generer_rating, groq_client
    logger.info("✅ Modules importés (relatif)")
except ImportError as e:
    logger.warning(f"Import relatif échoué: {e}")
    
    # Méthode 2: Import absolu
    try:
        from prompt_diagnostic import PromptDiagnostic
        from gemini_analyzer import prompt_plan_action, generer_rating, groq_client
        logger.info("✅ Modules importés (absolu)")
    except ImportError as e2:
        logger.warning(f"Import absolu échoué: {e2}")
        
        # Méthode 3: Ajouter src au path
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from prompt_diagnostic import PromptDiagnostic
            from gemini_analyzer import prompt_plan_action, generer_rating, groq_client
            logger.info("✅ Modules importés (avec sys.path)")
        except ImportError as e3:
            logger.warning(f"Tous les imports ont échoué: {e3}")
            
            # Fallback: classes simulées
            class PromptDiagnostic:
                def create_diagnostic_prompt(self, company_data):
                    return f"Analyse SWOT pour {company_data.get('company_name', 'entreprise')}"
                def clean_gemini_response(self, response):
                    return {"points_forts": [], "points_faibles": [], "opportunites": [], "menaces": [], "score_reputation": 50, "recommandations": []}
            
            def prompt_plan_action(company_data, swot_analysis):
                return "COURT TERME (0-3 mois):\n- Action 1\n\nMOYEN TERME (3-6 mois):\n- Action 2\n\nLONG TERME (6-12 mois):\n- Action 3"
            
            def generer_rating(company_data, swot_analysis):
                return {"score": 50, "justification": "Rating non disponible"}
            
            groq_client = None


class DiagnosticEngine:
    """Moteur de diagnostic complet"""
    
    def __init__(self, data_dir=None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).parent.parent.parent / "data"
        
        self.prompt_diagnostic = PromptDiagnostic() if PromptDiagnostic else None
        logger.info(f"DiagnosticEngine initialisé avec data_dir: {self.data_dir}")
    
    def load_company_data(self, company_name: str) -> Optional[Dict]:
        """Charge les données JSON de l'entreprise"""
        json_path = self.data_dir / f"{company_name.lower()}_results.json"
        
        if not json_path.exists():
            logger.error(f"Fichier non trouvé: {json_path}")
            return None
        
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Normalisation des clés
        if "company" in data and "company_name" not in data:
            data["company_name"] = data["company"]
        if "organic_results" in data and "results" not in data:
            data["results"] = data["organic_results"]
        
        logger.info(f"Données chargées pour {company_name}")
        return data
    
    def parse_swot_response(self, response_text: str) -> Dict:
        """Parse la réponse SWOT en format structuré"""
        result = {
            "points_forts": [],
            "points_faibles": [],
            "opportunites": [],
            "menaces": []
        }
        
        current_section = None
        lines = response_text.split('\n')
        
        for line in lines:
            line_lower = line.lower().strip()
            
            if 'points forts' in line_lower or 'forces' in line_lower:
                current_section = "points_forts"
                continue
            elif 'points faibles' in line_lower or 'faiblesses' in line_lower:
                current_section = "points_faibles"
                continue
            elif 'opportunites' in line_lower or 'opportunités' in line_lower:
                current_section = "opportunites"
                continue
            elif 'menaces' in line_lower:
                current_section = "menaces"
                continue
            
            if current_section and line.strip():
                clean = re.sub(r'^[\d\.\-\*\s]+', '', line.strip())
                if clean and len(clean) > 3:
                    result[current_section].append(clean)
        
        return result
    
    def format_swot_for_pdf(self, swot_dict: Dict) -> str:
        """Formate le SWOT pour l'affichage dans le PDF"""
        text = "ANALYSE SWOT:\n\n"
        
        text += "FORCES:\n"
        for item in swot_dict.get("points_forts", [])[:5]:
            text += f"- {item}\n"
        
        text += "\nFAIBLESSES:\n"
        for item in swot_dict.get("points_faibles", [])[:5]:
            text += f"- {item}\n"
        
        text += "\nOPPORTUNITES:\n"
        for item in swot_dict.get("opportunites", [])[:5]:
            text += f"- {item}\n"
        
        text += "\nMENACES:\n"
        for item in swot_dict.get("menaces", [])[:5]:
            text += f"- {item}\n"
        
        return text
    
    def analyze_company(self, company_name: str) -> Dict:
        """Analyse complète d'une entreprise"""
        # Charger les données
        data = self.load_company_data(company_name)
        
        if not data:
            return {
                "success": False,
                "error": f"Entreprise '{company_name}' non trouvee dans {self.data_dir}"
            }
        
        # 1. Générer le SWOT
        logger.info(f"Génération SWOT pour {company_name}...")
        
        if self.prompt_diagnostic:
            prompt = self.prompt_diagnostic.create_diagnostic_prompt(data)
            swot_raw = prompt  # Simulé pour l'instant
            swot_parsed = self.parse_swot_response(swot_raw)
            swot_text = self.format_swot_for_pdf(swot_parsed)
        else:
            swot_text = "ANALYSE SWOT:\n\nFORCES:\n- Innovation\n\nFAIBLESSES:\n- Budget\n\nOPPORTUNITES:\n- Expansion\n\nMENACES:\n- Concurrence"
            swot_parsed = {"points_forts": [], "points_faibles": [], "opportunites": [], "menaces": []}
        
        # 2. Générer le plan d'action
        logger.info(f"Génération plan d'action pour {company_name}...")
        if prompt_plan_action:
            plan_text = prompt_plan_action(data, swot_text)
        else:
            plan_text = "COURT TERME (0-3 mois):\n- Action prioritaire\n\nMOYEN TERME (3-6 mois):\n- Action secondaire\n\nLONG TERME (6-12 mois):\n- Action strategique"
        
        # 3. Générer le rating
        logger.info(f"Génération rating pour {company_name}...")
        if generer_rating:
            rating = generer_rating(data, swot_text)
        else:
            rating = {"score": 50, "justification": "Rating non disponible"}
        
        return {
            "success": True,
            "company_name": company_name,
            "swot": swot_text,
            "action_plan": plan_text,
            "rating": rating,
            "swot_parsed": swot_parsed,
            "data_source": str(self.data_dir / f"{company_name}_results.json")
        }


# Fonction utilitaire
def quick_analyze(company_name: str, data_dir: str = None):
    engine = DiagnosticEngine(data_dir)
    return engine.analyze_company(company_name)


if __name__ == "__main__":
    engine = DiagnosticEngine()
    for company in ["apple", "microsoft", "samsung"]:
        print(f"\n{'='*60}")
        print(f"Analyse de {company.upper()}")
        print('='*60)
        result = engine.analyze_company(company)
        if result["success"]:
            print(f"\n⭐ RATING: {result['rating']}")
        else:
            print(f"❌ Erreur: {result['error']}")