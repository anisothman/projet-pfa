from serpapi import GoogleSearch
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("SERP_API_KEY")

def rechercher(entreprise):
    params = {
        "q": entreprise,
        "hl": "fr",
        "gl": "tn",
        "num": 10,
        "api_key": API_KEY
    }
    search = GoogleSearch(params)
    return search.get_dict()

# Test
résultat = rechercher("Samsung")
print(résultat)
