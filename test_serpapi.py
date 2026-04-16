import os
import requests
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
print("Clé récupérée :", SERPAPI_KEY[:10] + "..." if SERPAPI_KEY else "MANQUANTE")

company = "Apple"
params = {
    "api_key": SERPAPI_KEY,
    "engine": "google",
    "q": f"{company} company",
    "hl": "fr",
    "gl": "fr",
    "num": 3
}

response = requests.get("https://serpapi.com/search", params=params)
print("Statut HTTP :", response.status_code)
data = response.json()
organic = data.get("organic_results", [])
print(f"Nombre de résultats organiques : {len(organic)}")
for i, res in enumerate(organic[:2]):
    print(f"{i+1}. {res.get('title')}")