"""
diagnostic_engine.py - VERSION CORRIGÉE
Moteur de diagnostic complet avec SWOT, Plan d'action et Rating

CORRECTIONS APPLIQUÉES :
1. generate_swot() utilise maintenant prompt_diagnostic() de gemini_analyzer directement
2. generer_rating() est appelé même sans données web (résultats vides)
3. Import de prompt_diagnostic ajouté depuis gemini_analyzer
4. Suppression de l'usage inutile de PromptDiagnostic pour la génération IA
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# CORRECTION 1 : Ajouter "prompt_diagnostic" dans l'import de gemini_analyzer
# Avant : from gemini_analyzer import prompt_plan_action, generer_rating, groq_client
# Après : on importe aussi prompt_diagnostic qui est la vraie fonction SWOT IA
# -----------------------------------------------------------------------
try:
    from gemini_analyzer import prompt_diagnostic, prompt_plan_action, generer_rating, groq_client
    GEMINI_AVAILABLE = True
    logger.info(f"✅ gemini_analyzer importé — groq_client actif: {groq_client is not None}")
except ImportError as e:
    prompt_diagnostic = None
    prompt_plan_action = None
    generer_rating = None
    groq_client = None
    GEMINI_AVAILABLE = False
    logger.warning(f"⚠️ gemini_analyzer non disponible: {e}")

# -----------------------------------------------------------------------
# PromptDiagnostic est conservé uniquement pour sa méthode de validation
# Il n'est PLUS utilisé pour générer le prompt envoyé à l'IA
# -----------------------------------------------------------------------
try:
    from prompt_diagnostic import PromptDiagnostic
    PROMPT_AVAILABLE = True
    logger.info("✅ PromptDiagnostic importé (validation uniquement)")
except ImportError:
    PromptDiagnostic = None
    PROMPT_AVAILABLE = False
    logger.warning("⚠️ PromptDiagnostic non disponible")


class DiagnosticEngine:
    def __init__(self, data_dir=None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).parent.parent / "data"

        # PromptDiagnostic gardé uniquement pour validation/schema
        self.prompt_diagnostic_validator = PromptDiagnostic() if PromptDiagnostic else None

        logger.info(
            f"DiagnosticEngine initialisé — data_dir: {self.data_dir} | "
            f"GEMINI={GEMINI_AVAILABLE} | groq_client={'OK' if groq_client else 'ABSENT'}"
        )

    # ------------------------------------------------------------------
    # CHARGEMENT DES DONNÉES
    # ------------------------------------------------------------------
    def load_company_data(self, company_name: str) -> Optional[Dict]:
        name_lower = company_name.lower()
        candidates = [
            self.data_dir / f"{name_lower}_results.json",
            self.data_dir / f"{name_lower}.json",
            self.data_dir / f"{company_name}_results.json",
            self.data_dir / f"{company_name}.json",
        ]

        for json_path in candidates:
            if json_path.exists():
                logger.info(f"Fichier trouvé: {json_path}")
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if "company" in data and "company_name" not in data:
                        data["company_name"] = data["company"]
                    if "organic_results" in data and "results" not in data:
                        data["results"] = data["organic_results"]
                    return data
                except Exception as e:
                    logger.error(f"Erreur lecture {json_path}: {e}")

        logger.warning(f"Aucun fichier JSON trouvé pour '{company_name}'")
        return None

    # ------------------------------------------------------------------
    # CORRECTION 2 : generate_swot() appelle directement prompt_diagnostic()
    # de gemini_analyzer.py au lieu de passer par PromptDiagnostic
    #
    # AVANT (cassé) :
    #   prompt = self.prompt_diagnostic.create_diagnostic_prompt(data)
    #   response = groq_client.chat.completions.create(...)  ← dupliquait le travail
    #
    # APRÈS (correct) :
    #   result = prompt_diagnostic(data)  ← appel direct à gemini_analyzer
    #   qui gère elle-même Groq + prompt + parsing
    # ------------------------------------------------------------------
    def generate_swot(self, company_name: str, data: Dict) -> str:
        try:
            if GEMINI_AVAILABLE and prompt_diagnostic:
                logger.info(f"🤖 Appel IA SWOT pour '{company_name}'...")
                result = prompt_diagnostic(data)  # ← CORRECTION PRINCIPALE
                logger.info(f"✅ SWOT IA généré pour {company_name} ({len(result)} chars)")
                return result
            else:
                logger.warning("GEMINI non disponible → fallback SWOT")
        except Exception as e:
            logger.error(f"Erreur génération SWOT IA: {e}")

        return self._fallback_swot(company_name, data)

    def _fallback_swot(self, company_name: str, data: Dict = None) -> str:
        name = company_name.upper()
        results_count = len(data.get("results", [])) if data else 0
        results_info = f"({results_count} résultats web analysés)" if results_count else ""
        return f"""ANALYSE SWOT DE {name} {results_info}:

FORCES:
- Présence établie sur son marché
- Notoriété et reconnaissance de la marque
- Capacité d'innovation et d'adaptation

FAIBLESSES:
- Dépendances potentielles à certains marchés ou partenaires
- Besoins en transformation digitale à identifier
- Analyse approfondie nécessaire pour préciser les points faibles

OPPORTUNITÉS:
- Expansion dans les marchés émergents et nouvelles géographies
- Développement de nouveaux segments de clientèle
- Tendances sectorielles favorables

MENACES:
- Concurrence intense et nouveaux entrants
- Évolutions réglementaires et contraintes de conformité
- Volatilité économique et géopolitique
"""

    # ------------------------------------------------------------------
    # PLAN D'ACTION
    # ------------------------------------------------------------------
    def _fallback_plan(self, company_name: str) -> str:
        name = company_name.upper()
        return f"""PLAN D'ACTION POUR {name}:

COURT TERME (0-3 mois):
- Analyser les données web et signaux marché collectés
- Identifier les axes d'amélioration prioritaires
- Mettre en place des indicateurs de suivi (KPIs)

MOYEN TERME (3-6 mois):
- Développer et déployer une stratégie digitale ciblée
- Optimiser la présence en ligne et le référencement
- Renforcer l'engagement client et la fidélisation

LONG TERME (6-12 mois):
- Consolider le leadership sur les marchés cibles
- Innover sur les produits/services clés
- Évaluer et adapter la stratégie selon les résultats
"""

    # ------------------------------------------------------------------
    # CORRECTION 3 : analyze_company() appelle generer_rating()
    # même quand data["results"] est vide
    #
    # AVANT (cassé) :
    #   if generer_rating and data.get("results"):  ← bloque si pas de fichier JSON
    #
    # APRÈS (correct) :
    #   if generer_rating and GEMINI_AVAILABLE:  ← appelle l'IA dès qu'elle est dispo
    # ------------------------------------------------------------------
    def analyze_company(self, company_name: str) -> Dict:
        company_name = company_name.strip().lower()
        data = self.load_company_data(company_name)

        if not data:
            logger.info(f"Pas de données fichier pour '{company_name}', dict vide utilisé")
            data = {"company_name": company_name, "results": []}

        # Génération SWOT via IA
        swot = self.generate_swot(company_name, data)

        # Génération plan d'action via IA
        plan = ""
        if prompt_plan_action and GEMINI_AVAILABLE:
            try:
                plan = prompt_plan_action(data, swot)
                logger.info(f"✅ Plan d'action IA généré pour {company_name}")
            except Exception as e:
                logger.error(f"Erreur plan action: {e}")
                plan = self._fallback_plan(company_name)
        else:
            plan = self._fallback_plan(company_name)

        # CORRECTION 3 : Rating appelé même sans data["results"]
        rating = {"score": 50, "justification": "Analyse standard — données limitées"}
        if generer_rating and GEMINI_AVAILABLE:
            try:
                rating = generer_rating(data, swot)
                logger.info(f"✅ Rating IA généré: {rating.get('score')}/100")
            except Exception as e:
                logger.error(f"Erreur rating: {e}")

        return {
            "success": True,
            "company_name": company_name,
            "swot": swot,
            "action_plan": plan,
            "rating": rating,
            "has_real_data": bool(data.get("results")),
            "data_source": str(self.data_dir / f"{company_name}_results.json")
        }


def quick_analyze(company_name: str, data_dir: str = None) -> Dict:
    engine = DiagnosticEngine(data_dir)
    return engine.analyze_company(company_name)


if __name__ == "__main__":
    engine = DiagnosticEngine()
    result = engine.analyze_company("isimm")
    print("SUCCESS:", result["success"])
    print("SWOT:", result["swot"][:300])
    print("PLAN:", result["action_plan"][:200])
    print("RATING:", result["rating"])