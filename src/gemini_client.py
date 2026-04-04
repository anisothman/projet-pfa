from google import genai
from src.config import GEMINI_API_KEY, check_keys

# Vérifier les clés au démarrage
check_keys()

# Créer le client Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

def get_client():
    """Retourne le client Gemini (pour diagnostic_engine.py)"""
    return client

def analyze_business(business_data: dict, prompt: str) -> str:
    """
    Analyse une entreprise avec Gemini
    
    Args:
        business_data: Données de l'entreprise
        prompt: Prompt à envoyer à Gemini
    
    Returns:
        Réponse de Gemini
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt + f"\n\n{business_data}"
        )
        return response.text
    except Exception as e:
        return f"[ERREUR Gemini] {str(e)}"