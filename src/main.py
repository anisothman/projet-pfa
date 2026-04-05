"""
main.py — Point d'entrée principal
Lance Sprint 1 (SerpAPI) puis Sprint 2 (Gemini)
Exécuter depuis le dossier src/ : python main.py
"""

import sys
from pathlib import Path

# Assurer que src/ est dans le path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pathlib import Path

BASE_DIR    = Path(__file__).resolve().parent.parent
DATA_DIR    = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

from serp_client   import rechercher
from json_extractor import JSONExtractor
from logger_config  import logger
from config         import check_keys


def rechercher_et_extraire(nom_entreprise: str) -> None:
    """Recherche via SerpAPI et sauvegarde en JSON (Sprint 1)"""
    logger.info(f"Recherche : {nom_entreprise}")
    raw_data = rechercher(nom_entreprise)

    extractor = JSONExtractor()
    structured = extractor.extract_company_info(raw_data, nom_entreprise)

    if extractor.validate_json_structure(structured):
        DATA_DIR.mkdir(exist_ok=True)
        filename = DATA_DIR / f"{nom_entreprise.lower()}_results.json"
        if extractor.save_to_json(structured, str(filename)):
            logger.info(f"Sauvegardé : {filename}")
        else:
            logger.error("Erreur sauvegarde JSON")
    else:
        logger.error("Structure JSON invalide")


def lancer_diagnostic_complet() -> None:
    """Lance l'analyse IA complète (Sprint 2)"""
    from diagnostic_engine import DiagnosticEngine

    logger.info("Lancement du diagnostic IA...")
    engine = DiagnosticEngine(
        data_dir=str(DATA_DIR),
        output_dir=str(REPORTS_DIR),
    )
    rapports = engine.generate_all_reports()
    engine.export_all(rapports)
    logger.info("Diagnostic terminé!")


if __name__ == "__main__":
    # Vérification des clés
    check_keys()

    entreprises = ["Samsung", "Apple", "Microsoft"]

    # Sprint 1 : collecte données
    for e in entreprises:
        rechercher_et_extraire(e)
        logger.info("-" * 50)

    # Sprint 2 : analyse IA
    lancer_diagnostic_complet()