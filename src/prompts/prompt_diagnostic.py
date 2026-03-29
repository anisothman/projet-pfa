"""
Module de création des prompts diagnostiques - VERSION OPTIMISÉE
Responsable optimisation: Nourhene
Sprint 2 - Optimisation du prompt Gemini

Améliorations apportées:
    1. Prompt entièrement en français et plus précis
    2. Utilisation complète des données SerpAPI (rating, reviews, photos, knowledge_graph)
    3. Validation renforcée du prompt et de la réponse Gemini
    4. Gestion des réponses mal formées de Gemini
    5. Test réel avec l'API Gemini intégré
"""

import json
import logging
import re
import os
from typing import Dict, Any
from datetime import datetime

# ── Configuration du logger ──────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/prompt_diagnostic.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PromptDiagnostic:
    """Classe pour créer et gérer les prompts de diagnostic - Version optimisée"""

    def __init__(self):
        self.prompt_template = None
        self.diagnostic_schema = self._define_schema()

    def _define_schema(self) -> Dict[str, Any]:
        """Définit le schéma complet du diagnostic"""
        return {
            "company_name": "str",
            "date_analyse": "str",
            "points_forts": ["str"],
            "points_faibles": ["str"],
            "opportunites": ["str"],
            "menaces": ["str"],
            "position_marche": "str",
            "presence_digitale": "str (Excellente/Bonne/Moyenne/Faible)",
            "score_reputation": "int (0-100)",
            "recommandations": ["str"],
            "horodatage": "str"
        }

    # ──────────────────────────────────────────────────────────
    # OPTIMISATION 1 : Extraction intelligente des données SerpAPI
    # ──────────────────────────────────────────────────────────
    def _extract_serpapi_data(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrait toutes les données utiles du JSON SerpAPI.
        Gère les deux formats : format brut SerpAPI et format normalisé.
        """
        extracted = {
            "nom": "Inconnu",
            "categorie": "Non renseignée",
            "adresse": "Non renseignée",
            "site_web": "Non renseigné",
            "telephone": "Non renseigné",
            "note": None,
            "nombre_avis": 0,
            "horaires": {},
            "photos": [],
            "resultats_recherche": [],
            "recherches_associees": []
        }

        # Format normalisé (business_clean.json)
        if "name" in company_data:
            extracted["nom"] = company_data.get("name", "Inconnu")
            extracted["categorie"] = company_data.get("category", "Non renseignée")
            extracted["adresse"] = company_data.get("address", "Non renseignée")
            extracted["site_web"] = company_data.get("website", "Non renseigné")
            extracted["telephone"] = company_data.get("phone", "Non renseigné")
            extracted["note"] = company_data.get("rating")
            extracted["nombre_avis"] = company_data.get("reviews_count", 0)
            extracted["horaires"] = company_data.get("hours", {})
            extracted["photos"] = company_data.get("photos", [])
            extracted["resultats_recherche"] = company_data.get("reviews", [])

        # Format brut SerpAPI
        elif "company" in company_data or "search_metadata" in company_data:
            extracted["nom"] = company_data.get("company", "Inconnu")
            kg = company_data.get("knowledge_graph", {})
            extracted["categorie"] = kg.get("entity_type", "Non renseignée")
            extracted["adresse"] = kg.get("address", kg.get("siège_social", "Non renseignée"))
            extracted["site_web"] = kg.get("website", "Non renseigné")
            extracted["telephone"] = kg.get("phone", "Non renseigné")
            extracted["note"] = kg.get("rating")
            extracted["nombre_avis"] = kg.get("reviews", 0)
            extracted["photos"] = [
                img.get("image", "") for img in kg.get("header_images", [])
                if img.get("image")
            ]
            organic = company_data.get("organic_results", [])
            extracted["resultats_recherche"] = [
                {"titre": r.get("title", ""), "extrait": r.get("snippet", "")}
                for r in organic[:8]
            ]
            extracted["recherches_associees"] = [
                r.get("query", "") for r in company_data.get("related_searches", [])[:5]
            ]

        # Format test simple (company_name + results)
        elif "company_name" in company_data:
            extracted["nom"] = company_data.get("company_name", "Inconnu")
            results = company_data.get("results", [])
            extracted["resultats_recherche"] = [
                {"titre": r.get("title", ""), "extrait": r.get("snippet", "")}
                for r in results[:8]
            ]

        return extracted

    # ──────────────────────────────────────────────────────────
    # OPTIMISATION 2 : Prompt enrichi et entièrement en français
    # ──────────────────────────────────────────────────────────
    def create_diagnostic_prompt(self, company_data: Dict[str, Any]) -> str:
        """
        Crée un prompt optimisé pour générer un diagnostic complet.
        Version améliorée : données enrichies + instructions précises en français.
        """
        data = self._extract_serpapi_data(company_data)

        # Construire le bloc résultats de recherche
        resultats_texte = "\n".join([
            f"  • {r.get('titre', r.get('title', 'N/A'))}: {r.get('extrait', r.get('snippet', r.get('text', 'N/A')))}"
            for r in data["resultats_recherche"][:8]
        ]) or "  • Aucun résultat disponible"

        # Construire le bloc note / avis
        note_texte = f"{data['note']}/5" if data['note'] else "Non disponible"
        avis_texte = str(data['nombre_avis']) if data['nombre_avis'] else "Non disponible"

        # Construire le bloc photos
        photos_texte = f"{len(data['photos'])} photo(s) disponible(s)" if data['photos'] else "Aucune photo"

        # Construire le bloc recherches associées
        recherches_texte = ", ".join(data["recherches_associees"]) or "Non disponible"

        prompt = f"""Tu es un expert en analyse d'entreprises et en marketing digital.
Effectue un diagnostic professionnel et détaillé de l'entreprise suivante,
en te basant UNIQUEMENT sur les données fournies ci-dessous.

══════════════════════════════════════════════════
FICHE ENTREPRISE
══════════════════════════════════════════════════
Nom              : {data['nom']}
Catégorie        : {data['categorie']}
Adresse          : {data['adresse']}
Site web         : {data['site_web']}
Téléphone        : {data['telephone']}
Note Google      : {note_texte}
Nombre d'avis    : {avis_texte}
Photos           : {photos_texte}
Date d'analyse   : {datetime.now().strftime("%d/%m/%Y")}

RÉSULTATS DE RECHERCHE GOOGLE :
{resultats_texte}

Recherches associées : {recherches_texte}
══════════════════════════════════════════════════

INSTRUCTIONS :
1. Identifie les POINTS FORTS de l'entreprise (minimum 3)
2. Identifie les POINTS FAIBLES (minimum 3)
3. Identifie les OPPORTUNITÉS de développement (minimum 2)
4. Identifie les MENACES potentielles (minimum 2)
5. Évalue sa POSITION SUR LE MARCHÉ (leader / challenger / suiveur / niche)
6. Évalue sa PRÉSENCE DIGITALE (Excellente / Bonne / Moyenne / Faible)
7. Calcule un SCORE DE RÉPUTATION de 0 à 100 basé sur :
   - La note Google (si disponible)
   - La richesse des informations disponibles
   - La qualité de la présence en ligne
8. Propose 3 à 5 RECOMMANDATIONS concrètes et actionnables

RÈGLES IMPORTANTES :
- Réponds UNIQUEMENT en JSON valide, sans texte avant ou après
- Tous les champs doivent être en français
- Si une information est absente, indique "Information non disponible"
- Base-toi uniquement sur les données fournies, sans inventer

RÉPONDS AVEC CE JSON EXACTEMENT :
{{
    "company_name": "{data['nom']}",
    "date_analyse": "{datetime.now().strftime('%d/%m/%Y')}",
    "points_forts": ["point fort 1", "point fort 2", "point fort 3"],
    "points_faibles": ["point faible 1", "point faible 2", "point faible 3"],
    "opportunites": ["opportunité 1", "opportunité 2"],
    "menaces": ["menace 1", "menace 2"],
    "position_marche": "description de la position sur le marché",
    "presence_digitale": "Excellente | Bonne | Moyenne | Faible",
    "score_reputation": 75,
    "recommandations": ["recommandation 1", "recommandation 2", "recommandation 3"],
    "horodatage": "{datetime.now().isoformat()}"
}}"""

        logger.info(f"Prompt optimisé créé pour : {data['nom']}")
        return prompt

    def create_multi_company_diagnostic_prompt(self, companies_data: list) -> str:
        """
        Crée un prompt comparatif pour plusieurs entreprises.
        Version optimisée : utilise _extract_serpapi_data pour chaque entreprise.
        """
        companies_text = ""
        for i, company in enumerate(companies_data, 1):
            data = self._extract_serpapi_data(company)
            companies_text += f"\n### ENTREPRISE {i} : {data['nom']}\n"
            companies_text += f"  Catégorie : {data['categorie']}\n"
            companies_text += f"  Note : {data['note'] or 'N/A'} | Avis : {data['nombre_avis']}\n"
            for r in data["resultats_recherche"][:4]:
                titre = r.get('titre', r.get('title', ''))
                extrait = r.get('extrait', r.get('snippet', r.get('text', '')))
                companies_text += f"  • {titre}: {extrait}\n"

        prompt = f"""Tu es un expert en analyse comparative d'entreprises.
Compare les entreprises suivantes et génère une analyse comparative détaillée.

{companies_text}

INSTRUCTIONS :
1. Pour chaque entreprise : diagnostic SWOT complet
2. Compare leur positionnement relatif sur le marché
3. Identifie le leader et explique pourquoi
4. Propose des recommandations stratégiques pour chacune

RÉPONDS UNIQUEMENT EN JSON VALIDE :
{{
    "date_analyse": "{datetime.now().strftime('%d/%m/%Y')}",
    "vue_ensemble": "description globale du marché",
    "comparison": "analyse comparative détaillée",
    "entreprises": [
        {{
            "nom": "nom entreprise",
            "points_forts": [],
            "points_faibles": [],
            "position_marche": "description",
            "score_reputation": 0
        }}
    ],
    "analyse_competitive": "qui domine et pourquoi",
    "leader_marche": "nom du leader",
    "recommandations": []
}}"""

        logger.info(f"Prompt comparatif créé pour {len(companies_data)} entreprises")
        return prompt

    # ──────────────────────────────────────────────────────────
    # OPTIMISATION 3 : Validation renforcée
    # ──────────────────────────────────────────────────────────
    def validate_prompt(self, prompt: str) -> bool:
        """
        Validation renforcée du prompt.
        Vérifie les mots-clés obligatoires ET la longueur minimale.
        """
        mots_cles_requis = [
            "diagnostic", "json", "recommandations",
            "points_forts", "points_faibles", "score_reputation"
        ]
        longueur_minimale = 200

        if len(prompt) < longueur_minimale:
            logger.warning(f"Prompt trop court : {len(prompt)} caractères (min {longueur_minimale})")
            return False

        manquants = [m for m in mots_cles_requis if m.lower() not in prompt.lower()]
        if manquants:
            logger.warning(f"Mots-clés manquants dans le prompt : {manquants}")
            return False

        return True

    # ──────────────────────────────────────────────────────────
    # OPTIMISATION 4 : Nettoyage de la réponse Gemini
    # ──────────────────────────────────────────────────────────
    def clean_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """
        Nettoie et parse la réponse de Gemini.
        Gère les cas où Gemini ajoute du texte avant/après le JSON.
        """
        # Supprimer les balises markdown ```json ... ```
        cleaned = re.sub(r'```json\s*', '', response_text)
        cleaned = re.sub(r'```\s*', '', cleaned)
        cleaned = cleaned.strip()

        # Extraire le JSON si du texte est présent avant/après
        json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if json_match:
            cleaned = json_match.group()

        try:
            result = json.loads(cleaned)
            logger.info("Réponse Gemini parsée avec succès")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Impossible de parser la réponse Gemini : {e}")
            return {
                "erreur": "Réponse Gemini non parseable",
                "reponse_brute": response_text[:500],
                "company_name": "Inconnu",
                "points_forts": [],
                "points_faibles": [],
                "recommandations": ["Relancer l'analyse avec un prompt corrigé"]
            }

    def validate_gemini_response(self, response: Dict[str, Any]) -> bool:
        """Vérifie que la réponse Gemini contient tous les champs attendus."""
        champs_requis = [
            "company_name", "points_forts", "points_faibles",
            "score_reputation", "recommandations"
        ]
        manquants = [c for c in champs_requis if c not in response]
        if manquants:
            logger.warning(f"Champs manquants dans la réponse Gemini : {manquants}")
            return False
        return True

    def get_schema(self) -> Dict[str, Any]:
        """Retourne le schéma du diagnostic"""
        return self.diagnostic_schema

    def save_prompt_template(self, prompt: str, filename: str = None) -> str:
        """Sauvegarde le template du prompt"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"src/prompts/diagnostic_{timestamp}.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(prompt)
            logger.info(f"Prompt sauvegardé : {filename}")
            return filename
        except Exception as e:
            logger.error(f"Erreur sauvegarde prompt : {e}")
            raise


# ══════════════════════════════════════════════════════════════
# TEST RÉEL AVEC GEMINI API
# ══════════════════════════════════════════════════════════════

def test_with_gemini(company_data: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    """
    Teste le prompt optimisé avec l'API Gemini.
    Retourne le diagnostic complet.
    """
    try:
        import google.genai as genai

        client = genai.Client(api_key=api_key)

        creator = PromptDiagnostic()
        prompt = creator.create_diagnostic_prompt(company_data)

        if not creator.validate_prompt(prompt):
            logger.error("Prompt invalide, arrêt du test")
            return {"erreur": "Prompt invalide"}

        logger.info("Envoi du prompt à Gemini...")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        response_text = response.text

        result = creator.clean_gemini_response(response_text)

        if creator.validate_gemini_response(result):
            logger.info("✅ Réponse Gemini valide !")
        else:
            logger.warning("⚠️ Réponse Gemini incomplète")

        return result

    except Exception as e:
        logger.error(f"Erreur lors de l'appel Gemini : {e}")
        return {"erreur": str(e)}


if __name__ == "__main__":
    import sys

    # ── Données de test ──
    example_company = {
        "company_name": "Samsung Tunisia",
        "results": [
            {"position": 1, "title": "Samsung Tunisie - Boutique officielle", "snippet": "Smartphones Galaxy, TV QLED, électroménager connecté."},
            {"position": 2, "title": "Samsung France", "snippet": "Découvrez nos produits High-Tech."},
            {"position": 3, "title": "Groupe Samsung - Wikipedia", "snippet": "Fondé en 1938, Samsung est un conglomérat mondial."},
        ]
    }

    creator = PromptDiagnostic()
    prompt = creator.create_diagnostic_prompt(example_company)

    print("=" * 60)
    print("PROMPT OPTIMISÉ GÉNÉRÉ :")
    print("=" * 60)
    print(prompt)

    print("\n" + "=" * 60)
    if creator.validate_prompt(prompt):
        print("✅ Prompt valide !")
    else:
        print("❌ Prompt invalide !")

    # ── Test avec Gemini si clé API fournie ──
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print("\n" + "=" * 60)
        print("TEST AVEC GEMINI API :")
        print("=" * 60)
        result = test_with_gemini(example_company, api_key)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("\n⚠️  Pour tester avec Gemini, ajoute GEMINI_API_KEY dans ton .env")
        print("    puis lance : python src/prompts/prompt_diagnostic.py")
