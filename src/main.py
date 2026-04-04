import os
from pathlib import Path
from serp_client import rechercher
from json_extractor import JSONExtractor
from logger_config import logger
from config import check_keys
from PDF_generator import export_all_pdf
import time

# =====================================================
# Chemins absolus
# =====================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

def rechercher_et_extraire(nom_entreprise: str) -> None:
    """
    Recherche une entreprise via SerpAPI et extrait les donnees en JSON
    """
    logger.info(f"Recherche en cours pour: {nom_entreprise}")
    
    raw_data = rechercher(nom_entreprise)
    
    extractor = JSONExtractor()
    structured_data = extractor.extract_company_info(raw_data, nom_entreprise)
    
    if extractor.validate_json_structure(structured_data):
        logger.info("Structure JSON valide!")
        
        DATA_DIR.mkdir(exist_ok=True)
        filename = DATA_DIR / f"{nom_entreprise.lower()}_results.json"
        
        if extractor.save_to_json(structured_data, str(filename)):
            logger.info(f"Donnees sauvegardees dans: {filename}")
        else:
            logger.error("Erreur lors de la sauvegarde")
    else:
        logger.error("Structure JSON invalide!")

def lancer_diagnostic_complet() -> None:
    """
    Lance le diagnostic complet apres avoir recupere les donnees
    """
    from diagnostic_engine import DiagnosticEngine
    
    logger.info("Lancement du diagnostic complet...")
    
    engine = DiagnosticEngine()
    rapports = engine.generate_all_reports()
    engine.export_all(rapports)
    export_all_pdf(rapports)
    
    logger.info("Diagnostic complet termine!")

if __name__ == "__main__":
    # Verifier les cles API
    check_keys()
    
    # Etape 1: Recuperer les donnees des entreprises
    entreprises = ["Samsung", "Apple", "Microsoft"]
    
    for entreprise in entreprises:
        rechercher_et_extraire(entreprise)
        logger.info("-" * 50)
        time.sleep(10)  # attendre 10 secondes entre chaque
    
    # Etape 2: Lancer le diagnostic complet (une seule fois)
    lancer_diagnostic_complet()