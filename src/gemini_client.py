from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_business(business_data: dict, prompt: str) -> str:
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt + f"\n\n{business_data}"
        )
        return response.text
    except Exception as e:
        return f"[ERREUR Gemini] {str(e)}"
