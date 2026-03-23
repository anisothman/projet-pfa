import json
from serp_client import rechercher
from json_extractor import JSONExtractor


def rechercher_et_extraire(nom_entreprise: str) -> None:
    """
    Recherche une entreprise via SerpAPI et extrait les données en JSON
    
    Args:
        nom_entreprise: Nom de l'entreprise à rechercher
    """
    print(f" Recherche en cours pour: {nom_entreprise}")
    
    # 1. Récupérer les données brutes de SerpAPI
    raw_data = rechercher(nom_entreprise)
    
    # 2. Extraire et structurer en JSON
    extractor = JSONExtractor()
    structured_data = extractor.extract_company_info(raw_data, nom_entreprise)
    
    # 3. Valider la structure JSON
    if extractor.validate_json_structure(structured_data):
        print("Structure JSON valide!")
        
        # 4. Sauvegarder dans un fichier
        filename = f"data/{nom_entreprise.lower()}_results.json"
        if extractor.save_to_json(structured_data, filename):
            print(f" Données sauvegardées dans: {filename}")
        else:
            print(f" Erreur lors de la sauvegarde")
    else:
        print(" Structure JSON invalide!")

if __name__ == "__main__":
    # Tester avec 3 entreprises
    entreprises = ["Samsung", "Apple", "Microsoft"]
    
    for entreprise in entreprises:
        rechercher_et_extraire(entreprise)
        print("-" * 50)
