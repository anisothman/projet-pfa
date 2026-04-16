# serpapi_search.py
import os
import requests
from config import SERPAPI_KEY

def search_company(company_name: str) -> dict:
    """
    Recherche une entreprise via SerpAPI (Google Search).
    Retourne un dict avec :
        - 'found': bool
        - 'results': liste des résultats organiques
        - 'error': message d'erreur éventuel
    """
    if not SERPAPI_KEY:
        return {"found": False, "error": "Clé SerpAPI manquante", "results": []}

    params = {
        "api_key": SERPAPI_KEY,
        "engine": "google",
        "q": f"{company_name} company",
        "hl": "fr",
        "gl": "fr",
        "num": 5
    }
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=10)
        data = response.json()
        organic = data.get("organic_results", [])
        # Si moins de 2 résultats, on considère que l'entreprise n'est pas trouvée
        if len(organic) < 2:
            return {"found": False, "results": organic, "error": "Pas assez de résultats"}
        return {"found": True, "results": organic, "error": None}
    except Exception as e:
        return {"found": False, "results": [], "error": str(e)}