import os
from dotenv import load_dotenv
import os
from pathlib import Path
from dotenv import load_dotenv

# Cherche .env à la racine du projet
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SERPAPI_KEY = os.getenv('SERPAPI_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

def check_keys():
    """Verifie que toutes les cles API sont presentes"""
    if not SERPAPI_KEY:
        raise ValueError("SERPAPI_KEY manquante dans .env")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY manquante dans .env")
    print("Toutes les cles API sont presentes")

# Auto-check au chargement du module
check_keys()