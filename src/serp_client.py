from serpapi import GoogleSearch
from config import SERPAPI_KEY

def rechercher(entreprise):
    params = {
        "q": entreprise,
        "hl": "fr",
        "gl": "tn",
        "num": 10,
        "api_key": SERPAPI_KEY
    }
    search = GoogleSearch(params)
    return search.get_dict()

if __name__ == "__main__":
    resultat = rechercher("Samsung")
    print(resultat)