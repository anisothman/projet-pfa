"""
Moteur de diagnostic IA
Responsable: Maram
Sprint 2 - Orchestration complète des analyses Gemini

Ce moteur intègre :
- prompt_diagnostic.py (Isra) : Création des prompts SWOT
- gemini_analyzer.py (Maram) : Génération des plans d'action
- API Gemini : Appels aux modèles d'IA
- Export des résultats : JSON + TXT
"""

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from google import genai

# =====================================================
# IMPORT DES MODULES DE L'ÉQUIPE
# =====================================================

# Module d'Isra : Création des prompts SWOT
import sys
sys.path.append('prompts')
from prompt_diagnostic import PromptDiagnostic

# Module de Maram : Génération des plans d'action
from gemini_analyzer import generer_plan_depuis_fichier

# =====================================================
# CONFIGURATION
# =====================================================

# Charger les variables d'environnement
load_dotenv()

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/diagnostic_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DiagnosticEngine:
    """
    Moteur d'orchestration des diagnostics IA
    
    Intègre :
    - Isra → PromptDiagnostic : création des prompts d'analyse SWOT
    - Maram → generer_plan_depuis_fichier : génération des plans d'action
    - Gemini API : exécution des appels IA
    """
    
    def __init__(self, data_dir: str = "../data", output_dir: str = "../reports"):
        """
        Initialise le moteur de diagnostic
        
        Args:
            data_dir: Dossier contenant les fichiers JSON du Sprint 1
            output_dir: Dossier où sauvegarder les rapports
        """
        self.data_dir = data_dir
        self.output_dir = output_dir
        
        # ===== Module d'Isra =====
        self.prompt_creator = PromptDiagnostic()
        logger.info("✅ Module PromptDiagnostic (Isra) chargé")
        
        # ===== Liste des entreprises =====
        self.companies = ["apple", "microsoft", "samsung"]
        
        # ===== Configuration Gemini =====
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("⚠️ GEMINI_API_KEY non trouvée dans .env")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("✅ Client Gemini initialisé")
    
    def load_company_data(self, company_name: str) -> dict:
        """
        Charge les données JSON d'une entreprise depuis le Sprint 1
        
        Args:
            company_name: Nom de l'entreprise (apple, microsoft, samsung)
            
        Returns:
            Données JSON de l'entreprise au format standardisé
        """
        file_path = os.path.join(self.data_dir, f"{company_name}_results.json")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                
                # Standardiser le format pour qu'il corresponde à ce qu'attendent
                # les modules de Maram et Isra
                standardized_data = {
                    "company_name": raw_data.get("company", company_name),
                    "results": raw_data.get("organic_results", []),
                    "search_metadata": raw_data.get("search_metadata", {})
                }
                
                logger.info(f"📂 Données chargées pour {company_name} ({len(standardized_data['results'])} résultats)")
                return standardized_data
                
        except FileNotFoundError:
            logger.error(f"❌ Fichier non trouvé: {file_path}")
            return {"company_name": company_name, "results": []}
        except json.JSONDecodeError:
            logger.error(f"❌ JSON invalide: {file_path}")
            return {"company_name": company_name, "results": []}
    def call_gemini(self, prompt: str, model: str = "gemini-2.0-flash") -> str:
        """
        Appelle l'API Gemini avec un prompt
        
        Args:
            prompt: Le prompt à envoyer à Gemini
            model: Le modèle Gemini à utiliser
            
        Returns:
            La réponse textuelle de Gemini
        """
        if self.client is None:
            logger.error("❌ Client Gemini non initialisé")
            return "Erreur: Client Gemini non disponible"
        
        try:
            logger.info("🤖 Envoi du prompt à Gemini...")
            response = self.client.models.generate_content(
                model=model,
                contents=prompt
            )
            logger.info("✅ Réponse reçue de Gemini")
            return response.text
        except Exception as e:
            logger.error(f"❌ Erreur appel Gemini: {e}")
            return f"Erreur: {e}"
    def generate_swot_analysis(self, company_name: str, company_data: dict) -> str:
        """
        Génère l'analyse SWOT en utilisant le module d'Isra
        
        Cette méthode utilise :
        1. PromptDiagnostic.create_diagnostic_prompt() → création du prompt SWOT
        2. Gemini API → exécution du prompt
        
        Args:
            company_name: Nom de l'entreprise
            company_data: Données de l'entreprise (format Sprint 1)
            
        Returns:
            Analyse SWOT générée par Gemini
        """
        try:
            # === Étape 1 : Création du prompt SWOT (Isra) ===
            logger.info(f"📝 Création du prompt SWOT avec PromptDiagnostic (Isra) pour {company_name}")
            swot_prompt = self.prompt_creator.create_diagnostic_prompt(company_data)
            
            # Validation du prompt
            if self.prompt_creator.validate_prompt(swot_prompt):
                logger.info(f"✅ Prompt SWOT validé pour {company_name}")
            else:
                logger.warning(f"⚠️ Prompt SWOT pourrait être incomplet pour {company_name}")
            
            # === Étape 2 : Appel à Gemini ===
            logger.info(f"🤖 Envoi du prompt SWOT à Gemini pour {company_name}")
            swot_analysis = self.call_gemini(swot_prompt)
            
            return swot_analysis
            
        except Exception as e:
            logger.error(f"❌ Erreur génération SWOT pour {company_name}: {e}")
            return f"Erreur lors de la génération SWOT: {e}"
    
    def generate_action_plan(self, company_name: str) -> str:
        """
        Génère le plan d'action en utilisant le module de Maram
        
        Cette méthode utilise :
        - generer_plan_depuis_fichier() de Maram (gemini_analyzer.py)
        
        Args:
            company_name: Nom de l'entreprise
            
        Returns:
            Plan d'action généré par Gemini
        """
        try:
            json_path = os.path.join(self.data_dir, f"{company_name}_results.json")
            
            logger.info(f"📋 Appel de generer_plan_depuis_fichier (Maram) pour {company_name}")
            action_plan = generer_plan_depuis_fichier(json_path)
            
            # Vérifier si le plan a été généré avec succès
            if "Erreur" in action_plan or "erreur" in action_plan.lower():
                logger.warning(f"⚠️ Plan d'action pourrait avoir des erreurs pour {company_name}")
            else:
                logger.info(f"✅ Plan d'action généré pour {company_name} ({len(action_plan)} caractères)")
            
            return action_plan
            
        except Exception as e:
            logger.error(f"❌ Erreur génération plan d'action pour {company_name}: {e}")
            return f"Erreur lors de la génération du plan d'action: {e}"
    
    def generate_diagnostic(self, company_name: str) -> dict:
        """
        Génère un diagnostic complet pour une entreprise
        
        Orchestration complète :
        1. Chargement des données du Sprint 1
        2. Analyse SWOT (Isra + Gemini)
        3. Plan d'action (Maram)
        4. Assemblage du rapport final
        
        Args:
            company_name: Nom de l'entreprise
            
        Returns:
            Dictionnaire contenant le diagnostic complet
        """
        logger.info(f"🚀 ===== DÉBUT DIAGNOSTIC POUR {company_name.upper()} =====")
        
        # === Étape 1 : Charger les données ===
        company_data = self.load_company_data(company_name)
        if not company_data.get("results"):
            logger.error(f"❌ Aucune donnée trouvée pour {company_name}")
            return {
                "company_name": company_name,
                "error": "Impossible de charger les données du Sprint 1",
                "generated_at": datetime.now().isoformat()
            }
        
        # === Étape 2 : Générer l'analyse SWOT (Isra + Gemini) ===
        logger.info(f"🔍 Étape 1/2 - Génération SWOT pour {company_name}")
        swot_analysis = self.generate_swot_analysis(company_name, company_data)
        
        # === Étape 3 : Générer le plan d'action (Maram) ===
        logger.info(f"📊 Étape 2/2 - Génération du plan d'action pour {company_name}")
        action_plan = self.generate_action_plan(company_name)
        
        # === Étape 4 : Construire le rapport ===
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
        
        logger.info(f"✅ Diagnostic complet pour {company_name} généré avec succès")
        return rapport
    
    def generate_all_reports(self) -> list:
        """
        Génère des rapports pour toutes les entreprises
        
        Returns:
            Liste des rapports pour chaque entreprise
        """
        logger.info("=" * 70)
        logger.info("📊 DÉBUT GÉNÉRATION DES RAPPORTS POUR TOUTES LES ENTREPRISES")
        logger.info("=" * 70)
        
        results = []
        
        for company in self.companies:
            try:
                rapport = self.generate_diagnostic(company)
                results.append(rapport)
                logger.info(f"✅ Rapport terminé pour {company}")
            except Exception as e:
                logger.error(f"❌ Échec pour {company}: {e}")
                results.append({
                    "company_name": company,
                    "error": str(e),
                    "generated_at": datetime.now().isoformat()
                })
        
        success_count = len([r for r in results if 'error' not in r])
        logger.info(f"🏁 Génération terminée: {success_count}/{len(self.companies)} succès")
        return results
    
    def export_json(self, rapport: dict) -> str:
        """
        Exporte un rapport au format JSON
        
        Args:
            rapport: Dictionnaire du rapport
            
        Returns:
            Chemin du fichier sauvegardé
        """
        os.makedirs(self.output_dir, exist_ok=True)
        
        company = rapport.get("company_name", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"diagnostic_{company}_{timestamp}.json")
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(rapport, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Rapport JSON exporté: {filename}")
            return filename
        except Exception as e:
            logger.error(f"❌ Erreur export JSON: {e}")
            return ""
    
    def export_text(self, rapport: dict) -> str:
        """
        Exporte un rapport au format texte lisible
        
        Args:
            rapport: Dictionnaire du rapport
            
        Returns:
            Chemin du fichier sauvegardé
        """
        os.makedirs(self.output_dir, exist_ok=True)
        
        company = rapport.get("company_name", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"diagnostic_{company}_{timestamp}.txt")
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("=" * 70 + "\n")
                f.write(f"DIAGNOSTIC COMPLET - {company.upper()}\n")
                f.write(f"Date de génération: {rapport.get('generated_at', datetime.now().isoformat())}\n")
                f.write("=" * 70 + "\n\n")
                
                # Section SWOT (Isra)
                f.write("🔍 ANALYSE SWOT\n")
                f.write("-" * 50 + "\n")
                f.write(rapport.get("swot_analysis", "Non disponible") + "\n\n")
                
                # Section Plan d'action (Maram)
                f.write("📊 PLAN D'ACTION STRATÉGIQUE\n")
                f.write("-" * 50 + "\n")
                f.write(rapport.get("action_plan", "Non disponible") + "\n\n")
                
                # Footer
                f.write("=" * 70 + "\n")
                f.write("Généré par LocalGuide AI - Diagnostic Engine\n")
                f.write(f"Données sources: {rapport.get('metadata', {}).get('data_source', 'inconnu')}\n")
                f.write("=" * 70 + "\n")
            
            logger.info(f"💾 Rapport texte exporté: {filename}")
            return filename
        except Exception as e:
            logger.error(f"❌ Erreur export texte: {e}")
            return ""
    
    def export_all(self, rapports: list):
        """
        Exporte tous les rapports (JSON + texte)
        
        Args:
            rapports: Liste des rapports à exporter
        """
        logger.info("💾 Export de tous les rapports...")
        for rapport in rapports:
            if "error" not in rapport:
                self.export_json(rapport)
                self.export_text(rapport)
            else:
                logger.warning(f"⚠️ Rapport avec erreur non exporté: {rapport.get('company_name')}")


# =====================================================
# POINT D'ENTRÉE - EXÉCUTION DU DIAGNOSTIC
# =====================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 LOCALGUIDE AI - DIAGNOSTIC ENGINE v1.0")
    print("=" * 70)
    print("📋 Intégration des modules :")
    print("   ✅ PromptDiagnostic (Isra) - SWOT Analysis")
    print("   ✅ generer_plan_depuis_fichier (Maram) - Action Plan")
    print("   ✅ Gemini API - IA Engine")
    print("\n📋 Génération des diagnostics pour: Apple, Microsoft, Samsung\n")
    
    # Créer le moteur de diagnostic
    engine = DiagnosticEngine()
    
    # Vérifier que la clé API est chargée
    if not engine.api_key:
        print("❌ ERREUR: GEMINI_API_KEY non trouvée dans le fichier .env")
        print("   Vérifiez que votre fichier .env contient: GEMINI_API_KEY=AIza...")
        print("   Le fichier .env doit être à la racine du projet (projet-pfa/.env)")
        exit(1)
    
    # Générer tous les rapports
    rapports = engine.generate_all_reports()
    
    # Exporter les rapports
    engine.export_all(rapports)
    
    # Afficher un résumé
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DES DIAGNOSTICS")
    print("=" * 70)
    for rapport in rapports:
        company = rapport.get("company_name", "inconnu")
        if "error" in rapport:
            print(f"❌ {company.upper()}: {rapport['error']}")
        else:
            swot = rapport.get("swot_analysis", "")
            action = rapport.get("action_plan", "")
            print(f"✅ {company.upper()}:")
            print(f"   📝 SWOT: {len(swot)} caractères")
            print(f"   📊 Plan d'action: {len(action)} caractères")
            print()
    
    print(f"📁 Rapports exportés dans: {engine.output_dir}")
    print("=" * 70)