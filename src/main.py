"""
main.py — Point d'entrée principal
Lance Sprint 1 (SerpAPI) → Sprint 2 (Gemini SWOT+Plan) → Sprint 3 (PDF Report)
Exécuter depuis le dossier src/ : python main.py
"""

import os
import sys
from pathlib import Path
import time
from datetime import datetime

# Assurer que src/ est dans le path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from serp_client import rechercher
from json_extractor import JSONExtractor
from logger_config import logger
from config import check_keys
from diagnostic_engine import DiagnosticEngine
from PDF_generator import export_all_pdf

# ── Chemins ────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent.parent
DATA_DIR    = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR    = BASE_DIR / "logs"

# ── Créer les répertoires s'ils n'existent pas ─────────────────────────────
DATA_DIR.mkdir(exist_ok=True, parents=True)
REPORTS_DIR.mkdir(exist_ok=True, parents=True)
LOGS_DIR.mkdir(exist_ok=True, parents=True)


# ══════════════════════════════════════════════════════════════════════════════
# SPRINT 1 : COLLECTE DES DONNÉES (SerpAPI)
# ══════════════════════════════════════════════════════════════════════════════

def rechercher_et_extraire(nom_entreprise: str) -> bool:
    """
    Recherche via SerpAPI et sauvegarde en JSON (Sprint 1)
    
    Args:
        nom_entreprise: Nom de l'entreprise à chercher
        
    Returns:
        bool: True si succès, False sinon
    """
    try:
        logger.info(f"[SPRINT 1] Recherche : {nom_entreprise}")
        
        # Appel SerpAPI
        raw_data = rechercher(nom_entreprise)
        if not raw_data:
            logger.error(f"Aucune donnée reçue pour {nom_entreprise}")
            return False
        
        # Extraction et structuration
        extractor = JSONExtractor()
        structured = extractor.extract_company_info(raw_data, nom_entreprise)
        
        # Validation
        if not extractor.validate_json_structure(structured):
            logger.error(f"Structure JSON invalide pour {nom_entreprise}")
            return False
        
        # Sauvegarde
        filename = DATA_DIR / f"{nom_entreprise.lower()}_results.json"
        if extractor.save_to_json(structured, str(filename)):
            logger.info(f" Données sauvegardées : {filename}")
            return True
        else:
            logger.error(f" Erreur sauvegarde JSON pour {nom_entreprise}")
            return False
            
    except Exception as e:
        logger.error(f"[SPRINT 1 ERREUR] {nom_entreprise}: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# SPRINT 2 : ANALYSE IA (SWOT + Plan d'Action + Rating)
# ══════════════════════════════════════════════════════════════════════════════

def lancer_diagnostic_complet() -> list:
    """
    Lance l'analyse IA complète (Sprint 2)
    Génère : SWOT + Plan d'Action + Rating
    
    Returns:
        list: Liste des rapports générés
    """
    try:
        logger.info("\n" + "="*70)
        logger.info("[SPRINT 2] LANCEMENT DU DIAGNOSTIC IA COMPLET")
        logger.info("="*70)
        
        # Initialiser le moteur
        engine = DiagnosticEngine(
            data_dir=str(DATA_DIR),
            output_dir=str(REPORTS_DIR),
        )
        
        # Générer les rapports
        logger.info("[SPRINT 2] Génération des rapports (SWOT + Plan + Rating)...")
        rapports = engine.generate_all_reports()
        
        # Exporter en JSON et TXT
        logger.info("[SPRINT 2] Export JSON et TXT...")
        engine.export_all(rapports)
        
        logger.info(" Diagnostic complet terminé!")
        return rapports
        
    except Exception as e:
        logger.error(f"[SPRINT 2 ERREUR] {e}")
        return []


# ══════════════════════════════════════════════════════════════════════════════
# SPRINT 3 : GÉNÉRATION DES RAPPORTS PDF PROFESSIONNELS
# ══════════════════════════════════════════════════════════════════════════════

def generer_rapports_pdf(rapports: list) -> int:
    """
    Génère les rapports PDF professionnels (Sprint 3)
    
    Args:
        rapports: Liste des rapports générés par Sprint 2
        
    Returns:
        int: Nombre de PDFs générés avec succès
    """
    try:
        if not rapports:
            logger.warning("[SPRINT 3] Aucun rapport à traiter")
            return 0
        
        logger.info("\n" + "="*70)
        logger.info("[SPRINT 3] GÉNÉRATION DES RAPPORTS PDF")
        logger.info("="*70)
        
        # Générer les PDFs
        export_all_pdf(rapports, output_dir=str(REPORTS_DIR))
        
        logger.info("✓ Rapports PDF générés avec succès!")
        return len([r for r in rapports if "error" not in r])
        
    except Exception as e:
        logger.error(f"[SPRINT 3 ERREUR] {e}")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """Orchestration complète : Sprint 1 → Sprint 2 → Sprint 3"""
    
    print("\n" + "="*70)
    print(" LOCALGUIDE AI - PIPELINE COMPLET v3.0")
    print("="*70)
    print(f" Data Dir    : {DATA_DIR}")
    print(f" Reports Dir : {REPORTS_DIR}")
    print(f" Logs Dir    : {LOGS_DIR}")
    print("="*70 + "\n")
    
    # ─ Vérification des clés ─────────────────────────────────────────────
    logger.info("Vérification des configurations...")
    check_keys()
    
    # Liste des entreprises à analyser
    entreprises = ["Samsung", "Apple", "Microsoft"]
    stats = {
        "sprint1_success": 0,
        "sprint1_failed": 0,
        "sprint2_reports": 0,
        "sprint3_pdfs": 0,
    }
    
    # ─ SPRINT 1 : Collecte des données ───────────────────────────────────
    print("\n" + "-"*70)
    print("  COLLECTE DES DONNÉES (SerpAPI)")
    print("▼"*70)
    
    logger.info(f"\nDémarrage collecte pour {len(entreprises)} entreprise(s)...")
    
    for i, entreprise in enumerate(entreprises, 1):
        print(f"\n  [{i}/{len(entreprises)}] Traitement : {entreprise}")
        
        if rechercher_et_extraire(entreprise):
            stats["sprint1_success"] += 1
            print(f" Succès")
        else:
            stats["sprint1_failed"] += 1
            print(f" Erreur")
        
        # Délai entre les requêtes (respecter les limites API)
        if i < len(entreprises):
            logger.info(f"Attente 10 secondes avant prochain appel...")
            print(f" Attente 10s...")
            time.sleep(10)
        
        print("  " + "-"*66)
    
    #  Sprint 1
   
    print(f"   Succès : {stats['sprint1_success']}/{len(entreprises)}")
    print(f"   Erreurs : {stats['sprint1_failed']}/{len(entreprises)}")
    
    if stats['sprint1_success'] == 0:
        logger.error("Aucune donnée collectée. Arrêt du pipeline.")
        print("\n    Aucune donnée pour continuer. Pipeline arrêté.")
        return
    
    # ─ SPRINT 2 : Analyse IA (SWOT + Plan + Rating) ─────────────────────
    print("\n" + "-"*70)
    print(" ANALYSE IA (SWOT + Plan d'Action + Rating)")
    print("▼"*70)
    
    rapports = lancer_diagnostic_complet()
    stats['sprint2_reports'] = len([r for r in rapports if "error" not in r])
   
    print(f" Rapports générés : {stats['sprint2_reports']}/{len(entreprises)}")
    
    if stats['sprint2_reports'] == 0:
        logger.error("Aucun rapport généré. Arrêt du pipeline.")
        print("\n Aucun rapport généré. Pipeline arrêté.")
        return
    
    # ─ SPRINT 3 : Génération des PDFs ────────────────────────────────────
    print("\n" + "-"*70)
    print("   GÉNÉRATION DES RAPPORTS PDF")
    print("▼"*70)
    
    stats['sprint3_pdfs'] = generer_rapports_pdf(rapports)
    
    print(f"\n Sprint 3 - Résumé:")
    print(f" PDFs générés : {stats['sprint3_pdfs']}/{len(entreprises)}")
    
    # ─ Résumé Final ──────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("  PIPELINE COMPLÉTÉ AVEC SUCCÈS !")
    print("="*70)
    print(f"\n  STATISTIQUES FINALES:")
    print(f"      Sprint 1 (Données)    : {stats['sprint1_success']}/{len(entreprises)} ✅")
    print(f"      Sprint 2 (Analyse IA) : {stats['sprint2_reports']}/{len(entreprises)} ✅")
    print(f"      Sprint 3 (PDF Report) : {stats['sprint3_pdfs']}/{len(entreprises)} ✅")
    
    print(f"\n FICHIERS GÉNÉRÉS:")
    print(f"      Data     : {DATA_DIR}")
    print(f"      Reports  : {REPORTS_DIR}")
    print(f"      Logs     : {LOGS_DIR}")
    
    print(f"\n   Heure : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*70 + "\n")
    
    logger.info("Pipeline complet terminé avec succès !")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  Pipeline interrompu par l'utilisateur.")
        logger.warning("Pipeline interrompu (Ctrl+C)")
    except Exception as e:
        print(f"\n\n Erreur critique : {e}")
        logger.error(f"Erreur critique du pipeline : {e}", exc_info=True)