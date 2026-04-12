"""
diagnostic_engine.py — Sprint 2 : Orchestration IA         
Responsable : Maram                                         
Dépend de   : gemini_client.py + gemini_analyzer.py      
Orchestre la génération complète des diagnostics :
  1. Charge les données JSON du Sprint 1
  2. Génère l'analyse SWOT (via gemini_analyzer)
  3. Génère le plan d'action (via gemini_analyzer)
  4. Exporte les rapports JSON + TXT
"""

import io
import os
import sys
import json
import glob
import logging
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv


# Fix encodage Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# ── Chemins absolus ────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent.parent
DATA_DIR    = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR    = BASE_DIR / "logs"

# Add src/ to sys.path so all local imports resolve correctly
sys.path.insert(0, str(Path(__file__).resolve().parent))

load_dotenv()

# ── Logging ────────────────────────────────────────────────────────────────────
LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)8s | %(filename)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOGS_DIR / "diagnostic_engine.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("projet-pfa")

# ── Imports modules Sprint 2 ───────────────────────────────────────────────────
from gemini_analyzer import prompt_diagnostic, generer_plan_depuis_fichier
from gemini_client import call_gemini, get_stats

# ── Import PromptDiagnostic (guarded) ─────────────────────────────────────────
_HAS_PROMPT_MODULE = False
try:
    from prompts.prompt_diagnostic import PromptDiagnostic
    _HAS_PROMPT_MODULE = True
    logger.info("Module PromptDiagnostic chargé")
except ImportError:
    logger.warning("prompts.prompt_diagnostic absent → fallback intégré utilisé")

    class PromptDiagnostic:
        """Fallback si le module d'Isra n'est pas encore présent."""
        def create_diagnostic_prompt(self, company_data: dict) -> str:
            return None

        def validate_prompt(self, prompt) -> bool:
            return prompt is not None and len(str(prompt)) > 50


class DiagnosticEngine:
    """
    Moteur d'orchestration des diagnostics IA.
    Génère SWOT + Plan d'action pour chaque entreprise.
    """

    def __init__(self, data_dir: str = None, output_dir: str = None):
        self.data_dir   = Path(data_dir)   if data_dir   else DATA_DIR
        self.output_dir = Path(output_dir) if output_dir else REPORTS_DIR

        self.data_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

        self.prompt_creator = PromptDiagnostic()
        self.companies = self._detect_companies()

        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.error("GEMINI_API_KEY manquante dans .env")
        else:
            logger.info(f"Engine initialisé | {len(self.companies)} entreprise(s) détectée(s)")

    # ── Détection des entreprises depuis data/ ─────────────────────────────────
    def _detect_companies(self) -> list:
        files = glob.glob(str(self.data_dir / "*_results.json"))
        names = [Path(f).stem.replace("_results", "") for f in files]
        if not names:
            logger.warning("Aucun fichier *_results.json trouvé → liste par défaut")
            return ["apple", "microsoft", "samsung"]
        logger.info(f"Entreprises trouvées: {names}")
        return names

    # ── Chargement des données JSON (Sprint 1) ─────────────────────────────
    def load_company_data(self, company_name: str) -> dict:
        file_path = self.data_dir / f"{company_name}_results.json"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw = json.load(f)

            data = {
                "company_name": raw.get("company", company_name),
                "results":      raw.get("organic_results", raw.get("results", [])),
                "search_metadata": raw.get("search_metadata", {}),
            }
            logger.info(f"Données chargées : {company_name} ({len(data['results'])} résultats)")
            return data

        except FileNotFoundError:
            logger.error(f"Fichier introuvable: {file_path}")
            return {"company_name": company_name, "results": []}
        except json.JSONDecodeError as e:
            logger.error(f"JSON invalide ({file_path}): {e}")
            return {"company_name": company_name, "results": []}

    # ── Parsing de la réponse SWOT ─────────────────────────────────────────
    def _parse_swot_response(self, response: str) -> dict:
        """Parse la réponse SWOT en dictionnaire structuré"""
        swot = {
            "points_forts": [],
            "points_faibles": [],
            "opportunites": [],
            "menaces": []
        }
        
        if not response:
            return swot
        
        logger.info(f"Parsing SWOT - Réponse reçue: {len(response)} caractères")
        
        # Nettoyer la réponse (enlever les ```json et ```)
        clean_response = response.strip()
        clean_response = re.sub(r'^```json\s*', '', clean_response)
        clean_response = re.sub(r'\s*```$', '', clean_response)
        
        try:
            # Essayer de parser comme JSON
            data = json.loads(clean_response)
            
            # Extraire les points forts
            for item in data.get("points_forts", []):
                if isinstance(item, str):
                    swot["points_forts"].append({"titre": item[:60], "description": ""})
                elif isinstance(item, dict):
                    swot["points_forts"].append({
                        "titre": item.get("titre", item.get("title", ""))[:60],
                        "description": item.get("description", "")[:200]
                    })
            
            # Extraire les points faibles
            for item in data.get("points_faibles", []):
                if isinstance(item, str):
                    swot["points_faibles"].append({"titre": item[:60], "description": ""})
                elif isinstance(item, dict):
                    swot["points_faibles"].append({
                        "titre": item.get("titre", item.get("title", ""))[:60],
                        "description": item.get("description", "")[:200]
                    })
            
            # Extraire les opportunités
            for item in data.get("opportunites", []):
                if isinstance(item, str):
                    swot["opportunites"].append({"titre": item[:60], "description": ""})
                elif isinstance(item, dict):
                    swot["opportunites"].append({
                        "titre": item.get("titre", item.get("title", ""))[:60],
                        "description": item.get("description", "")[:200]
                    })
            
            # Extraire les menaces
            for item in data.get("menaces", []):
                if isinstance(item, str):
                    swot["menaces"].append({"titre": item[:60], "description": ""})
                elif isinstance(item, dict):
                    swot["menaces"].append({
                        "titre": item.get("titre", item.get("title", ""))[:60],
                        "description": item.get("description", "")[:200]
                    })
            
            logger.info(f"JSON parsé: {len(swot['points_forts'])} forces")
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur JSON: {e}")
            # Si échec, mettre des données par défaut
            swot["points_forts"] = [{"titre": "Donnée non disponible", "description": "L'analyse n'a pas pu être parsée."}]
            swot["points_faibles"] = [{"titre": "Donnée non disponible", "description": "L'analyse n'a pas pu être parsée."}]
            swot["opportunites"] = [{"titre": "Donnée non disponible", "description": "L'analyse n'a pas pu être parsée."}]
            swot["menaces"] = [{"titre": "Donnée non disponible", "description": "L'analyse n'a pas pu être parsée."}]
        
        return swot
    

    

    # ── Génération SWOT ────────────────────────────────────────────────────
    def generate_swot_analysis(self, company_name: str, company_data: dict) -> dict:
        """Génère l'analyse SWOT et retourne un dictionnaire structuré"""
        logger.info(f"[SWOT] Début pour {company_name}")
        try:
            # Appel à l'API
            if _HAS_PROMPT_MODULE:
                custom_prompt = self.prompt_creator.create_diagnostic_prompt(company_data)
                if self.prompt_creator.validate_prompt(custom_prompt):
                    response = call_gemini(custom_prompt)
                else:
                    response = prompt_diagnostic(company_data)
            else:
                response = prompt_diagnostic(company_data)
            
            # Parser la réponse
            swot_dict = self._parse_swot_response(response)
            logger.info(f"[SWOT OK] {company_name}: {len(swot_dict['points_forts'])} forces, {len(swot_dict['opportunites'])} opportunités")
            return swot_dict
            
        except Exception as e:
            logger.error(f"[SWOT ERREUR] {company_name}: {e}")
            return {
                "points_forts": [{"titre": "Erreur", "description": str(e)[:100]}],
                "points_faibles": [],
                "opportunites": [],
                "menaces": []
            }

    # ── Parsing du plan d'action ───────────────────────────────────────────
    def _parse_action_plan(self, response: str) -> dict:
        """Parse le plan d'action en dictionnaire structuré"""
        plan = {
            "court_terme": [],
            "moyen_terme": [],
            "long_terme": []
        }
        
        if not response or "Erreur" in response:
            return plan
        
        logger.info(f"Parsing Plan - Réponse reçue: {len(response)} caractères")
        
        current_period = None
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            line_lower = line.lower()
            
            # Détection des périodes
            if "court terme" in line_lower or "0-3 mois" in line_lower or "court" in line_lower:
                current_period = "court_terme"
                logger.info("Période détectée: COURT TERME")
            elif "moyen terme" in line_lower or "3-6 mois" in line_lower or "moyen" in line_lower:
                current_period = "moyen_terme"
                logger.info("Période détectée: MOYEN TERME")
            elif "long terme" in line_lower or "6-12 mois" in line_lower or "long" in line_lower:
                current_period = "long_terme"
                logger.info("Période détectée: LONG TERME")
            
            # Extraction des actions
            if current_period and re.match(r'^\s*[\d\-•*]\s+', line):
                action_text = re.sub(r'^\s*[\d\-•*]\s+', '', line)
                action_text = re.sub(r'\*\*', '', action_text)
                
                if action_text and len(action_text) > 3:
                    # Ignorer les lignes de métadonnées
                    skip_words = ['risque', 'mitigation', 'kpi', 'taux de croissance', 'part de marché', 'indicateur']
                    if not any(word in action_text.lower() for word in skip_words):
                        plan[current_period].append({
                            "action": action_text[:80],
                            "description": ""
                        })
                        logger.info(f"Ajouté à {current_period}: {action_text[:40]}...")
        
        return plan

    # ── Génération Plan d'action ───────────────────────────────────────────
    def generate_action_plan(self, company_name: str, swot_analysis: dict = None) -> dict:
        """Génère le plan d'action - retourne un dictionnaire vide si erreur"""
        logger.info(f"[PLAN] Début pour {company_name}")
        try:
            json_path = str(self.data_dir / f"{company_name}_results.json")
            swot_json = json.dumps(swot_analysis, ensure_ascii=False) if swot_analysis else None
            response = generer_plan_depuis_fichier(json_path, swot_json)
            
            # Vérifier si la réponse est une erreur
            if not response or "Erreur" in response or "RESOURCE_EXHAUSTED" in response:
                logger.warning(f"[PLAN] Aucun plan généré pour {company_name} (API error)")
                return {}
            
            # Parser le plan d'action
            plan_dict = self._parse_action_plan(response)
            
            if not plan_dict["court_terme"] and not plan_dict["moyen_terme"] and not plan_dict["long_terme"]:
                logger.warning(f"[PLAN] Plan vide pour {company_name}")
                return {}
            
            logger.info(f"[PLAN OK] {company_name}: {len(plan_dict['court_terme'])} CT, {len(plan_dict['moyen_terme'])} MT, {len(plan_dict['long_terme'])} LT")
            return plan_dict
            
        except Exception as e:
            logger.error(f"[PLAN ERREUR] {company_name}: {e}")
            return {}

    # ── Rating avec Groq ───────────────────────────────────────────────────
    def generate_rating_with_groq(self, company_data: dict, swot_analysis: str) -> dict:
        """Génère un rating avec Groq"""
        try:
            from groq import Groq
            from config import GROQ_API_KEY
            
            if not GROQ_API_KEY:
                logger.warning("GROQ_API_KEY non configurée")
                return {"score": 50, "justification": "Rating non disponible"}
            
            groq_client = Groq(api_key=GROQ_API_KEY)
            
            prompt = f"""
Tu es un analyste financier expert. Note cette entreprise sur 100.

Données de l'entreprise:
{json.dumps(company_data, ensure_ascii=False)[:2000]}

Analyse SWOT:
{swot_analysis[:1500]}

Critères (20 points chacun):
- Position concurrentielle
- Solidité financière  
- Innovation et technologie
- Satisfaction client
- Potentiel de croissance

Réponds UNIQUEMENT avec ce format JSON:
{{"score": 75, "justification": "Courte justification en une phrase"}}
"""
            
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            text = response.choices[0].message.content
            text = re.sub(r"```json|```", "", text).strip()
            data = json.loads(text)
            score = max(0, min(100, int(data.get("score", 50))))
            logger.info(f"Rating Groq généré: {score}/100")
            return {
                "score": score,
                "justification": data.get("justification", "")
            }
        except Exception as e:
            logger.error(f"Rating Groq erreur: {e}")
            return {"score": 50, "justification": "Rating non disponible"}

    # ── Génération de tous les rapports ─────────────────────────────────────
    def generate_all_reports(self) -> list:
        """Génère les rapports pour toutes les entreprises"""
        logger.info("\n" + "="*60)
        logger.info(f"GÉNÉRATION DE {len(self.companies)} RAPPORT(S)")
        logger.info("="*60)
        
        rapports = []
        for company in self.companies:
            try:
                company_data = self.load_company_data(company)
                rapport = self.generate_report(company, company_data)
                rapports.append(rapport)
            except Exception as e:
                logger.error(f"Erreur pour {company}: {e}")
                rapports.append({"company_name": company, "error": str(e)})
        
        logger.info(f"\nRésultat : {len([r for r in rapports if 'error' not in r])}/{len(self.companies)} rapport(s) générés avec succès")
        return rapports

    # ── Diagnostic complet (SWOT + Plan + Rating) ──────────────────────────────
    def generate_report(self, company_name: str, company_data: dict) -> dict:
        """Génère un rapport complet pour une entreprise"""
        
        logger.info("\n" + "="*60)
        logger.info(f"DIAGNOSTIC COMPLET : {company_name.upper()}")
        logger.info("="*60)
        
        rapport = {
            "company_name": company_name,
            "generated_at": datetime.now().isoformat(),
            "swot_analysis": {},
            "action_plan": {},
            "rating": {}
        }
        
        # Étape 1: Analyse SWOT
        logger.info("Étape 1/3 → Analyse SWOT")
        try:
            swot_dict = self.generate_swot_analysis(company_name, company_data)
            rapport["swot_analysis"] = swot_dict
            logger.info(f"✓ SWOT généré: {len(swot_dict.get('points_forts', []))} forces, {len(swot_dict.get('opportunites', []))} opportunités")
        except Exception as e:
            logger.error(f"Erreur SWOT: {e}")
            rapport["swot_analysis"] = {"points_forts": [], "points_faibles": [], "opportunites": [], "menaces": []}
        
        # Étape 2: Plan d'action
        logger.info("Étape 2/3 → Plan d'action")
        try:
            plan_dict = self.generate_action_plan(company_name, rapport["swot_analysis"])
            rapport["action_plan"] = plan_dict if plan_dict else {}
            
            if plan_dict:
                logger.info(f"✓ Plan généré: {len(plan_dict.get('court_terme', []))} actions CT, {len(plan_dict.get('moyen_terme', []))} MT, {len(plan_dict.get('long_terme', []))} LT")
            else:
                logger.warning(f"⚠ Aucun plan d'action généré pour {company_name}")
        except Exception as e:
            logger.error(f"Erreur plan: {e}")
            rapport["action_plan"] = {}
        
        # Étape 3: Rating
        logger.info("Étape 3/3 → Rating IA")
        try:
            swot_str = json.dumps(rapport["swot_analysis"], ensure_ascii=False)
            rating_data = self.generate_rating_with_groq(company_data, swot_str)
            rapport["rating"] = rating_data
            logger.info(f"✓ Rating: {rating_data.get('score')}/100")
        except Exception as e:
            logger.error(f"Erreur rating: {e}")
            rapport["rating"] = {"score": 50, "justification": "Rating non disponible"}
        
        logger.info(f"✓ Diagnostic terminé : {company_name}")
        return rapport

    # ── Export JSON ────────────────────────────────────────────────────────
    def export_json(self, rapport: dict) -> str:
        company = rapport.get("company_name", "unknown")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.output_dir / f"diagnostic_{company}_{ts}.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rapport, f, indent=2, ensure_ascii=False)
            logger.info(f"JSON exporté : {path}")
            return str(path)
        except Exception as e:
            logger.error(f"Erreur export JSON: {e}")
            return ""

    # ── Export TXT lisible ─────────────────────────────────────────────────
    def export_text(self, rapport: dict) -> str:
        company = rapport.get("company_name", "unknown")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.output_dir / f"diagnostic_{company}_{ts}.txt"
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("=" * 70 + "\n")
                f.write(f"DIAGNOSTIC — {company.upper()}\n")
                f.write(f"Généré le : {rapport.get('generated_at', '')}\n")
                f.write("=" * 70 + "\n\n")
                
                # SWOT
                f.write("ANALYSE SWOT\n" + "-" * 50 + "\n")
                swot = rapport.get("swot_analysis", {})
                f.write("\nPOINTS FORTS:\n")
                for item in swot.get("points_forts", []):
                    f.write(f"  • {item.get('titre', '')}\n")
                    if item.get('description'):
                        f.write(f"    {item.get('description', '')}\n")
                
                f.write("\nPOINTS FAIBLES:\n")
                for item in swot.get("points_faibles", []):
                    f.write(f"  • {item.get('titre', '')}\n")
                    if item.get('description'):
                        f.write(f"    {item.get('description', '')}\n")
                
                f.write("\nOPPORTUNITÉS:\n")
                for item in swot.get("opportunites", []):
                    f.write(f"  • {item.get('titre', '')}\n")
                    if item.get('description'):
                        f.write(f"    {item.get('description', '')}\n")
                
                f.write("\nMENACES:\n")
                for item in swot.get("menaces", []):
                    f.write(f"  • {item.get('titre', '')}\n")
                    if item.get('description'):
                        f.write(f"    {item.get('description', '')}\n")
                
                # Plan d'action
                f.write("\n\nPLAN D'ACTION\n" + "-" * 50 + "\n")
                plan = rapport.get("action_plan", {})
                
                if plan.get("court_terme"):
                    f.write("\nCOURT TERME (0-6 mois):\n")
                    for item in plan.get("court_terme", []):
                        f.write(f"  • {item.get('action', '')}\n")
                else:
                    f.write("\nCOURT TERME: Aucune action définie\n")
                
                if plan.get("moyen_terme"):
                    f.write("\nMOYEN TERME (6-18 mois):\n")
                    for item in plan.get("moyen_terme", []):
                        f.write(f"  • {item.get('action', '')}\n")
                else:
                    f.write("\nMOYEN TERME: Aucune action définie\n")
                
                if plan.get("long_terme"):
                    f.write("\nLONG TERME (18+ mois):\n")
                    for item in plan.get("long_terme", []):
                        f.write(f"  • {item.get('action', '')}\n")
                else:
                    f.write("\nLONG TERME: Aucune action définie\n")
                
                # Rating
                rating = rapport.get("rating", {})
                f.write("\n\nRATING IA\n" + "-" * 50 + "\n")
                f.write(f"Score: {rating.get('score', 'N/A')}/100\n")
                f.write(f"Justification: {rating.get('justification', '')}\n")
                
                f.write("\n" + "=" * 70 + "\n")
            logger.info(f"TXT exporté : {path}")
            return str(path)
        except Exception as e:
            logger.error(f"Erreur export TXT: {e}")
            return ""

    # ── Export tous les formats ────────────────────────────────────────────
    def export_all(self, rapports: list):
        for r in rapports:
            if "error" not in r:
                self.export_json(r)
                self.export_text(r)
            else:
                logger.warning(f"Rapport ignoré (erreur) : {r.get('company_name')}")

def analyze_company(company_name: str) -> dict:
    import time
    from datetime import datetime
    from pathlib import Path
    from serp_client import rechercher
    from json_extractor import JSONExtractor
    from logger_config import logger

    DATA_DIR = Path(__file__).resolve().parent.parent / "data"
    DATA_DIR.mkdir(exist_ok=True)

    try:
        print(f"[API] Starting analysis for: {company_name}")

        # Sprint 1: Search & Extract
        raw_data = rechercher(company_name)
        if not raw_data:
            raise Exception(f"No data found for {company_name}")

        extractor = JSONExtractor()
        structured = extractor.extract_company_info(raw_data, company_name)
        filename = DATA_DIR / f"{company_name.lower()}_results.json"
        extractor.save_to_json(structured, str(filename))

        # Sprint 2: AI Analysis
        engine = DiagnosticEngine(
            data_dir=str(DATA_DIR),
            output_dir=str(DATA_DIR / "reports"),
        )
        reports = engine.generate_all_reports()

        if not reports:
            raise Exception("Failed to generate AI analysis")

        result = {
            'diagnostic': reports[0].get('diagnostic', {}),
            'plan_action': reports[0].get('plan_action', {}),
            'metadonnees': {
                'date_analyse': datetime.now().isoformat(),
                'id_analyse': f"{company_name}_{int(time.time())}",
                'company_name': company_name
            }
        }

        print(f"[API] Analysis complete for: {company_name}")
        return result

    except Exception as e:
        print(f"[API Error] {e}")
        raise



# POINT D'ENTRÉE
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  LOCALGUIDE AI — DIAGNOSTIC ENGINE v2.0")
    print("=" * 70)

    engine = DiagnosticEngine()

    if not engine.api_key:
        print("\n  GEMINI_API_KEY manquante dans .env — arrêt.")
        sys.exit(1)

    rapports = engine.generate_all_reports()
    engine.export_all(rapports)

    print("\n" + "=" * 70)
    print("  RÉSUMÉ FINAL")
    print("=" * 70)
    for r in rapports:
        company = r.get("company_name", "?")
        if "error" in r:
            print(f"  ✗ {company.upper():12} → ERREUR : {r['error']}")
        else:
            rating_score = r.get("rating", {}).get("score", "N/A")
            swot_count = len(r.get("swot_analysis", {}).get("points_forts", []))
            plan_count = len(r.get("action_plan", {}).get("court_terme", []))
            print(f"  ✓ {company.upper():12} → SWOT: {swot_count} forces | Plan: {plan_count} actions | Rating: {rating_score}/100")

    stats = get_stats()
    print(f"\n  API calls : {stats['total']} total | "
          f"{stats['cache_hits']} cache | "
          f"{stats['quota_errors']} quota errors")
    print(f"  Rapports  : {engine.output_dir}")
    print("=" * 70)


# Alias for the API
analyze_company_api = analyze_company