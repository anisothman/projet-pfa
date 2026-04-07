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
import sys
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
from gemini_analyzer import prompt_diagnostic, generer_plan_depuis_fichier, generer_rating
from gemini_client import call_gemini, get_stats

# ── Import PromptDiagnostic (guarded) ─────────────────────────────────────────
try:
    from prompts.prompt_diagnostic import PromptDiagnostic
    _HAS_PROMPT_MODULE = True
    logger.info("Module PromptDiagnostic (Isra) chargé")
except ImportError:
    _HAS_PROMPT_MODULE = False
    logger.warning("prompts.prompt_diagnostic absent → fallback intégré utilisé")

    class PromptDiagnostic:
        """Fallback si le module d'Isra n'est pas encore présent."""
        def create_diagnostic_prompt(self, company_data: dict) -> str:
            return None  # Signal → on utilisera prompt_diagnostic() directement

        def validate_prompt(self, prompt) -> bool:
            return prompt is not None and len(str(prompt)) > 50


# ══════════════════════════════════════════════════════════════════════════════
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

    # ── Détection des entreprises depuis data/ ─────────────────────────────
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

            # Normalisation de la structure (sprint 1 → sprint 2)
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

    # ── Génération SWOT ────────────────────────────────────────────────────
    def generate_swot_analysis(self, company_name: str, company_data: dict) -> str:
        logger.info(f"[SWOT] Début pour {company_name}")
        try:
            # Si le module d'Isra est présent, on l'utilise pour créer le prompt
            if _HAS_PROMPT_MODULE:
                custom_prompt = self.prompt_creator.create_diagnostic_prompt(company_data)
                if self.prompt_creator.validate_prompt(custom_prompt):
                    logger.info(f"[SWOT] Prompt Isra utilisé pour {company_name}")
                    return call_gemini(custom_prompt)

            # Sinon, fallback sur notre prompt_diagnostic()
            return prompt_diagnostic(company_data)

        except Exception as e:
            logger.error(f"[SWOT ERREUR] {company_name}: {e}")
            return f"Erreur SWOT {company_name}: {e}"

    # ── Génération Plan d'action ───────────────────────────────────────────
    def generate_action_plan(self, company_name: str, swot_analysis: str = None) -> str:
        logger.info(f"[PLAN] Début pour {company_name}")
        try:
            json_path = str(self.data_dir / f"{company_name}_results.json")
            return generer_plan_depuis_fichier(json_path, swot_analysis)
        except Exception as e:
            logger.error(f"[PLAN ERREUR] {company_name}: {e}")
            return f"Erreur plan {company_name}: {e}"

    # ── Diagnostic complet (SWOT + Plan) ──────────────────────────────────
    def generate_diagnostic(self, company_name: str) -> dict:
        logger.info(f"\n{'='*60}")
        logger.info(f"DIAGNOSTIC COMPLET : {company_name.upper()}")
        logger.info(f"{'='*60}")

        company_data = self.load_company_data(company_name)
        if not company_data.get("results"):
            logger.error(f"Aucune donnée disponible pour {company_name}")
            return {
                "company_name": company_name,
                "error": "Données JSON manquantes (relancer le sprint 1)",
                "generated_at": datetime.now().isoformat(),
            }

        # Étape 1 : SWOT
        logger.info(f"Étape 1/2 → Analyse SWOT")
        swot = self.generate_swot_analysis(company_name, company_data)

        # Étape 2 : Plan d'action (enrichi avec le SWOT)
        logger.info(f"Étape 2/2 → Plan d'action")
        plan = self.generate_action_plan(company_name, swot)

        # Étape 3 : Rating IA (Sprint 3)
        logger.info(f"Étape 3/3 → Rating IA")
        rating = generer_rating(company_data, swot)

        rapport = {
            "company_name": company_name,
            "generated_at": datetime.now().isoformat(),
            "swot_analysis": swot,
            "action_plan":   plan,
            "rating":        rating,
            "metadata": {
                "data_source":        f"{company_name}_results.json",
                "results_count":      len(company_data.get("results", [])),
                "engine_version":     "2.0",
                "swot_length":        len(swot),
                "plan_length":        len(plan),
                "models_used":        "gemini-2.5-flash-preview-04-17 (+ fallback chain)",
                "api_stats":          get_stats(),
            },
        }

        logger.info(f"✓ Diagnostic terminé : {company_name}")
        return rapport

    # ── Tous les rapports ──────────────────────────────────────────────────
    def generate_all_reports(self) -> list:
        logger.info(f"\n{'='*60}")
        logger.info(f"GÉNÉRATION DE {len(self.companies)} RAPPORT(S)")
        logger.info(f"{'='*60}")

        results = []
        for company in self.companies:
            try:
                results.append(self.generate_diagnostic(company))
            except Exception as e:
                logger.error(f"Échec {company}: {e}")
                results.append({
                    "company_name": company,
                    "error": str(e),
                    "generated_at": datetime.now().isoformat(),
                })

        ok = sum(1 for r in results if "error" not in r)
        logger.info(f"\nRésultat : {ok}/{len(self.companies)} rapport(s) générés avec succès")
        return results

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
                f.write(f"Généré le : {rapport.get('generated_at','')}\n")
                f.write("=" * 70 + "\n\n")
                f.write("ANALYSE SWOT\n" + "-" * 50 + "\n")
                f.write(rapport.get("swot_analysis", "Non disponible") + "\n\n")
                f.write("PLAN D'ACTION\n" + "-" * 50 + "\n")
                f.write(rapport.get("action_plan", "Non disponible") + "\n\n")
                
                # Ajouter le rating si disponible
                rating = rapport.get("rating", {})
                if rating.get("score"):
                    f.write("RATING IA\n" + "-" * 50 + "\n")
                    f.write(f"Score: {rating.get('score')}/100\n")
                    f.write(f"Justification: {rating.get('justification', '')}\n\n")
                
                meta = rapport.get("metadata", {})
                f.write("MÉTADONNÉES\n" + "-" * 50 + "\n")
                f.write(f"Modèle     : {meta.get('models_used','')}\n")
                f.write(f"SWOT       : {meta.get('swot_length',0)} caractères\n")
                f.write(f"Plan       : {meta.get('plan_length',0)} caractères\n")
                f.write("=" * 70 + "\n")
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


# ══════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  LOCALGUIDE AI — DIAGNOSTIC ENGINE v2.0")
    print("=" * 70)

    engine = DiagnosticEngine()

    if not engine.api_key:
        print("\n⚠  GEMINI_API_KEY manquante dans .env — arrêt.")
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
            print(f"  ✓ {company.upper():12} → SWOT: {len(r.get('swot_analysis',''))} chars | "
                  f"Plan: {len(r.get('action_plan',''))} chars | Rating: {rating_score}/100")

    stats = get_stats()
    print(f"\n  API calls : {stats['total']} total | "
          f"{stats['cache_hits']} cache | "
          f"{stats['quota_errors']} quota errors")
    print(f"  Rapports  : {engine.output_dir}")
    print("=" * 70)