"""
config.py — Configuration centralisée
Charge les variables d'environnement depuis .env
check_keys() doit être appelé MANUELLEMENT (pas à l'import)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SERPAPI_KEY    = os.getenv("SERPAPI_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  



def check_keys():
    """Vérifie que toutes les clés API sont présentes. Appeler depuis main.py."""
    missing = []
    if not SERPAPI_KEY:
        missing.append("SERPAPI_KEY")
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if missing:
        raise ValueError(f"Clés manquantes dans .env : {', '.join(missing)}")
    print("✓ Toutes les clés API sont présentes")