"""
Moteur de diagnostic IA
Responsable: Maram
Sprint 2 - Orchestration complete des analyses Gemini
"""

import io
import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from google import genai

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
# =====================================================
# IMPORT DES MODULES DE L'EQUIPE
#====================================================

# Module d'Isra : Creation des prompts SWOT
from prompts.prompt_diagnostic import PromptDiagnostic

# Module de Maram : Generation des plans d'action
from gemini_analyzer import generer_plan_depuis_fichier

# =====================================================
# CORRECTION: Configuration des chemins absolus
# =====================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# =====================================================
# CONFIGURATION
# =====================================================

load_dotenv()

# Configuration des logs avec chemin absolu
os.makedirs(LOGS_DIR, exist_ok=True)
log_path = os.path.join(LOGS_DIR, "diagnostic_engine.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DiagnosticEngine:
    """
    Moteur d'orchestration des diagnostics IA
    """
    
    def __init__(self, data_dir: str = None, output_dir: str = None):
        """
        Initialise le moteur de diagnostic
        """
        # CORRECTION: Utiliser les chemins absolus
        if data_dir is None:
            self.data_dir = DATA_DIR
        else:
            self.data_dir = data_dir
            
        if output_dir is None:
            self.output_dir = REPORTS_DIR
        else:
            self.output_dir = output_dir
        
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.prompt_creator = PromptDiagnostic()
        logger.info("Module PromptDiagnostic charge")
        
        self.companies = self._detect_companies()
        logger.info("Entreprises detectees: " + str(self.companies))
        
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY non trouvee dans .env")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("Client Gemini initialise")
    
    def _detect_companies(self) -> list:
        """Detecte automatiquement les fichiers JSON dans data/"""
        import glob #  Importer le module glob (recherche de fichiers)

        json_files = glob.glob(os.path.join(self.data_dir, "*_results.json"))
        companies = []
         #Parcourir chaque fichier trouvé
        for f in json_files:
             # 4
             #  Extraire juste le nom du fichier (sans le chemin)
            basename = os.path.basename(f)
             #  Supprimer le suffixe "_results.json"
            company_name = basename.replace("_results.json", "")
            companies.append(company_name)
             # Si aucun fichier trouvé, utiliser la liste par défaut
        return companies if companies else ["apple", "microsoft", "samsung"]
    
    def load_company_data(self, company_name: str) -> dict:
        """
        Charge les donnees JSON d'une entreprise depuis le Sprint 1
        """
        file_path = os.path.join(self.data_dir, f"{company_name}_results.json")
         #  Standardiser le format (uniformiser pour tout le projet)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                
                standardized_data = {
                    "company_name": raw_data.get("company", company_name),
                    "results": raw_data.get("organic_results", []),# liste vide sinon
                    "search_metadata": raw_data.get("search_metadata", {}) # Récupère les métadonnées ou dict vide si absent
                }
                
                logger.info("Donnees chargees pour " + company_name + " (" + str(len(standardized_data['results'])) + " resultats)")
                return standardized_data
                
        except FileNotFoundError:
            logger.error("Fichier non trouve: " + file_path)
            return {"company_name": company_name, "results": []}
        except json.JSONDecodeError:
            logger.error("JSON invalide: " + file_path)
            return {"company_name": company_name, "results": []}
    
    def call_gemini(self, prompt: str, model: str = "gemini-1.5-flash-8b") -> str:
        """
        Appelle l'API Gemini avec un prompt
        """
        if self.client is None:
            logger.error("Client Gemini non initialise")
            return "Erreur: Client Gemini non disponible"
        
        try:
            logger.info("Envoi du prompt a Gemini...")
            response = self.client.models.generate_content(
                model=model,
                contents=prompt
            )
            logger.info("Reponse recue de Gemini")
            return response.text
        except Exception as e:
            logger.error("Erreur appel Gemini: " + str(e))
            return "Erreur: " + str(e)
    
    def generate_swot_analysis(self, company_name: str, company_data: dict) -> str:
        """
        Genere l'analyse SWOT en utilisant le module d'Isra
        """
        try:
            logger.info("Creation du prompt SWOT avec PromptDiagnostic  pour " + company_name)
            swot_prompt = self.prompt_creator.create_diagnostic_prompt(company_data)
            
            if self.prompt_creator.validate_prompt(swot_prompt):
                logger.info("Prompt SWOT valide pour " + company_name)
            else:
                logger.warning("Prompt SWOT pourrait etre incomplet pour " + company_name)
            
            logger.info("Envoi du prompt SWOT a Gemini pour " + company_name)
            swot_analysis = self.call_gemini(swot_prompt)
            
            return swot_analysis
            
        except Exception as e:
            logger.error("Erreur generation SWOT pour " + company_name + ": " + str(e))
            return "Erreur lors de la generation SWOT: " + str(e)
    
    def generate_action_plan(self, company_name: str, swot_analysis: str = None) -> str:
        """
        Genere le plan d'action en utilisant le SWOT si disponible
        """
        try:
            json_path = os.path.join(self.data_dir, f"{company_name}_results.json")
            
            logger.info("Appel de generer_plan_d'action pour " + company_name)
            
            if swot_analysis:
                logger.info("Plan d'action enrichi avec l'analyse SWOT")
                action_plan = generer_plan_depuis_fichier(json_path, swot_analysis)
            else:
                logger.warning("Pas de SWOT fourni, plan base uniquement sur les donnees brutes")
                action_plan = generer_plan_depuis_fichier(json_path)
            
            if "Erreur" in action_plan or "erreur" in action_plan.lower():
                logger.warning("Plan d'action pourrait avoir des erreurs pour " + company_name)
            else:
                logger.info("Plan d'action genere pour " + company_name + " (" + str(len(action_plan)) + " caracteres)")
            
            return action_plan
            
        except Exception as e:
            logger.error("Erreur generation plan d'action pour " + company_name + ": " + str(e))
            return "Erreur lors de la generation du plan d'action: " + str(e)
    
    def generate_diagnostic(self, company_name: str) -> dict:
        """
        Genere un diagnostic complet pour une entreprise
        """
        logger.info("===== DEBUT DIAGNOSTIC POUR " + company_name.upper() + " =====")
        
        company_data = self.load_company_data(company_name)
        if not company_data.get("results"):
            logger.error("Aucune donnee trouvee pour" + company_name)
            return {
                "company_name": company_name,
                "error": "Impossible de charger les donnees des fichiers JSON",
                "generated_at": datetime.now().isoformat()
            }
        
        logger.info("Etape 1/2 - Generation SWOT pour " + company_name)
        swot_analysis = self.generate_swot_analysis(company_name, company_data)
        
        logger.info("Etape 2/2 - Generation du plan d'action pour " + company_name)
        action_plan = self.generate_action_plan(company_name, swot_analysis)
        
        rapport = {
            "company_name": company_name,
            "generated_at": datetime.now().isoformat(),
            "swot_analysis": swot_analysis,
            "action_plan": action_plan,
            "metadata": {
                "data_source": f"{company_name}_results.json",
                "data_results_count": len(company_data.get("results", [])),
                "engine_version": "1.0",
                "models_used": {
                    "swot_model": "gemini-2.0-flash",
                    "action_plan_model": "gemini-2.0-flash"
                }
            }
        }
        
        logger.info("Diagnostic complet pour " + company_name + " genere avec succes")
        return rapport
    
    def generate_all_reports(self) -> list:
        """
        Genere des rapports pour toutes les entreprises
        """
        logger.info("=" * 70)
        logger.info("DEBUT GENERATION DES RAPPORTS POUR TOUTES LES ENTREPRISES")
        logger.info("=" * 70)
        
        results = []
        
        for company in self.companies:
            try:
                rapport = self.generate_diagnostic(company)
                results.append(rapport)
                logger.info("Rapport termine pour " + company)
            except Exception as e:
                logger.error("Echec pour " + company + ": " + str(e))
                results.append({
                    "company_name": company,
                    "error": str(e),
                    "generated_at": datetime.now().isoformat()
                })
        
        success_count = len([r for r in results if 'error' not in r])
        logger.info("Generation terminee: " + str(success_count) + "/" + str(len(self.companies)) + " succes")
        return results
    
    def export_json(self, rapport: dict) -> str:
        """
        Exporte un rapport au format JSON
        """
        os.makedirs(self.output_dir, exist_ok=True)
        
        company = rapport.get("company_name", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"diagnostic_{company}_{timestamp}.json")
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(rapport, f, indent=2, ensure_ascii=False)
            logger.info("Rapport JSON exporte: " + filename)
            return filename
        except Exception as e:
            logger.error("Erreur export JSON: " + str(e))
            return ""
    
    def export_text(self, rapport: dict) -> str:
        """
        Exporte un rapport au format texte lisible
        """
        os.makedirs(self.output_dir, exist_ok=True)
        
        company = rapport.get("company_name", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"diagnostic_{company}_{timestamp}.txt")
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("=" * 70 + "\n")
                f.write("DIAGNOSTIC COMPLET - " + company.upper() + "\n")
                f.write("Date de generation: " + rapport.get('generated_at', datetime.now().isoformat()) + "\n")
                f.write("=" * 70 + "\n\n")
                
                f.write("ANALYSE SWOT\n")
                f.write("-" * 50 + "\n")
                f.write(rapport.get("swot_analysis", "Non disponible") + "\n\n")
                
                f.write("PLAN D'ACTION STRATEGIQUE\n")
                f.write("-" * 50 + "\n")
                f.write(rapport.get("action_plan", "Non disponible") + "\n\n")
                
                f.write("=" * 70 + "\n")
                f.write("Genere par LocalGuide AI - Diagnostic Engine\n")
                f.write("Donnees sources: " + rapport.get('metadata', {}).get('data_source', 'inconnu') + "\n")
                f.write("=" * 70 + "\n")
            
            logger.info("Rapport texte exporte: " + filename)
            return filename
        except Exception as e:
            logger.error("Erreur export texte: " + str(e))
            return ""
    
    def export_all(self, rapports: list):
        """
        Exporte tous les rapports (JSON + texte)
        """
        logger.info("Export de tous les rapports...")
        for rapport in rapports:
            if "error" not in rapport:
                self.export_json(rapport)
                self.export_text(rapport)
            else:
                logger.warning("Rapport avec erreur non exporte: " + rapport.get('company_name'))


# =====================================================
# POINT D'ENTREE - EXECUTION DU DIAGNOSTIC
# =====================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("LOCALGUIDE AI - DIAGNOSTIC ENGINE v1.0")
    print("=" * 70)
    print("Integration des modules :")
    print("  - PromptDiagnostic (Isra) - SWOT Analysis")
    print("  - generer_plan_depuis_fichier (Maram) - Action Plan")
    print("  - Gemini API - IA Engine")
    print("\nGeneration des diagnostics pour: Apple, Microsoft, Samsung\n")
    
    engine = DiagnosticEngine()
    
    if not engine.api_key:
        print("ERREUR: GEMINI_API_KEY non trouvee dans le fichier .env")
        print("Verifiez que votre fichier .env contient: GEMINI_API_KEY=AIza...")
        print("Le fichier .env doit etre a la racine du projet (projet-pfa/.env)")
        exit(1)
    
    rapports = engine.generate_all_reports()
    
    engine.export_all(rapports)
    
    print("\n" + "=" * 70)
    print("RESUME DES DIAGNOSTICS")
    print("=" * 70)
    for rapport in rapports:
        company = rapport.get("company_name", "inconnu")
        if "error" in rapport:
            print("ERREUR " + company.upper() + ": " + rapport['error'])
        else:
            swot = rapport.get("swot_analysis", "")
            action = rapport.get("action_plan", "")
            print("SUCCES " + company.upper() + ":")
            print("   SWOT: " + str(len(swot)) + " caracteres")
            print("   Plan d'action: " + str(len(action)) + " caracteres")
            print()
    
    print("Rapports exportes dans: " + engine.output_dir)
    print("=" * 70)