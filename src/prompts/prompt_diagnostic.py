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
    
CORRECTIONS SPRINT 2+:
    A1. Mapping standardisé Sprint 1 ↔ Sprint 2
    A3. Schéma complet selon ARCHITECTURE_JSON.md
    A4. Parser JSON robuste (pas de regex greedy)
    C1. Validation du prompt améliorée
    C2. Validation de réponse stricte (fail fast)
    C3. Validation des données d'entrée
"""

import json
import logging
import re
import os
from typing import Dict, Any, Optional
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
        
        # ══════════════════════════════════════════════════════
        # MAPPING STANDARDISÉ SPRINT 1 ↔ SPRINT 2 (A1)
        # ══════════════════════════════════════════════════════
        self.FIELD_MAPPING = {
            "name": "nom",
            "address": "adresse",
            "category": "categorie",
            "rating": "note",
            "reviews_count": "nombre_avis",
            "website": "site_web",
            "phone": "telephone",
            "hours": "horaires",
            "reviews": "avis",
            "photos": "photos"
        }

    def _define_schema(self) -> Dict[str, Any]:
        """
        Définit le schéma COMPLET du diagnostic (A3)
        Selon ARCHITECTURE_JSON.md
        """
        return {
            # Section 1: Données d'entreprise
            "entreprise": {
                "id_entreprise": "str",
                "nom": "str",
                "adresse": "str",
                "telephone": "str",
                "site_web": "str",
                "categorie": "str",
                "horaires": "dict",
                "note_moyenne": "float (0-5)",
                "nombre_avis": "int",
                "photos": ["str"]
            },
            # Section 2: Diagnostic SWOT
            "diagnostic": {
                "points_forts": [
                    {
                        "titre": "str",
                        "description": "str",
                        "impact": "str (critique/majeur/modéré/faible)"
                    }
                ],
                "points_faibles": [
                    {
                        "titre": "str",
                        "description": "str",
                        "severite": "str (critique/majeur/modéré/faible)"
                    }
                ],
                "opportunites": [
                    {
                        "titre": "str",
                        "description": "str",
                        "potentiel": "str (très élevé/élevé/modéré/faible)"
                    }
                ],
                "menaces": [
                    {
                        "titre": "str",
                        "description": "str",
                        "probabilite": "str (élevée/modérée/faible)"
                    }
                ]
            },
            # Section 3: Plan d'action
            "plan_action": {
                "resume_executif": "str",
                "court_terme": ["action (0-3 mois)"],
                "moyen_terme": ["action (3-6 mois)"],
                "long_terme": ["action (6-12 mois)"],
                "kpis": ["metrique de suivi"],
                "risques": ["risque identifié"]
            },
            # Section 4: Analyse des avis (optionnel)
            "analyse_avis": {
                "themes_positifs": ["str"],
                "themes_negatifs": ["str"],
                "sentiment_general": "str (très positif/positif/neutre/négatif)"
            },
            # Section 5: Métadonnées
            "metadonnees": {
                "date_analyse": "str (ISO 8601)",
                "version_prompt": "str",
                "modele_gemini": "str",
                "temps_reponse_ms": "int",
                "langue": "str",
                "qualite_donnees": "str",
                "id_analyse": "str"
            }
        }

    # ══════════════════════════════════════════════════════════════
    # VALIDATION DES DONNÉES D'ENTRÉE (C3)
    # ══════════════════════════════════════════════════════════════
    def _validate_company_data(self, company_data: Dict[str, Any]) -> bool:
        """
        Valide que les données d'entrée sont correctes.
        Lève une exception si incorrect.
        """
        # Vérification 1: Pas None ou vide
        if not company_data:
            raise ValueError(" company_data ne peut pas être None ou vide")
        
        # Vérification 2: Doit être un dict
        if not isinstance(company_data, dict):
            raise TypeError(
                f" company_data doit être un dict, reçu {type(company_data).__name__}"
            )
        
        # Vérification 3: Doit avoir AU MOINS UNE clé identifiant l'entreprise
        valid_keys = {"name", "company", "company_name", "nom", "company_data"}
        has_company_key = any(k in company_data for k in valid_keys)
        
        if not has_company_key:
            raise ValueError(
                f" company_data doit avoir une de ces clés: {valid_keys}. "
                f"Reçu: {list(company_data.keys())}"
            )
        
        logger.info(f" company_data valide")
        return True

    # ══════════════════════════════════════════════════════════════
    # EXTRACTION ET STANDARDISATION DES DONNÉES (A1)
    # ══════════════════���═══════════════════════════════════════════
    def _extract_serpapi_data(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrait toutes les données utiles du JSON SerpAPI.
        Gère les trois formats : Sprint 1, SerpAPI brut, Simple test
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
            "avis": [],
            "photos": [],
            "resultats_recherche": [],
            "recherches_associees": []
        }

        # ──────────────────────────────────────────────────────
        # FORMAT 1: Données du Sprint 1 (business_clean.json)
        # ──────────────────────────────────────────────────────
        if "name" in company_data:
            # Appliquer le mapping standardisé
            for sprint1_key, internal_key in self.FIELD_MAPPING.items():
                if sprint1_key in company_data:
                    value = company_data[sprint1_key]
                    # Gérer les None et valeurs vides
                    if value not in [None, "", [], {}]:
                        extracted[internal_key] = value
            
            # Assignations explicites
            extracted["nom"] = company_data.get("name", "Inconnu")
            extracted["categorie"] = company_data.get("category", "Non renseignée")
            extracted["adresse"] = company_data.get("address", "Non renseignée")
            extracted["site_web"] = company_data.get("website", "Non renseigné")
            extracted["telephone"] = company_data.get("phone", "Non renseigné")
            extracted["note"] = company_data.get("rating")
            extracted["nombre_avis"] = company_data.get("reviews_count", 0)
            extracted["horaires"] = company_data.get("hours", {})
            extracted["avis"] = company_data.get("reviews", [])
            extracted["photos"] = company_data.get("photos", [])

        # ──────────────────────────────────────────────────────
        # FORMAT 2: Données SerpAPI brutes
        # ──────────────────────────────────────────────────────
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

        # ──────────────────────────────────────────────────────
        # FORMAT 3: Simple test (company_name + results)
        # ──────────────────────────────────────────────────���───
        elif "company_name" in company_data:
            extracted["nom"] = company_data.get("company_name", "Inconnu")
            results = company_data.get("results", [])
            extracted["resultats_recherche"] = [
                {"titre": r.get("title", ""), "extrait": r.get("snippet", "")}
                for r in results[:8]
            ]

        logger.info(f" Données extraites pour: {extracted['nom']}")
        return extracted

    def standardize_company_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convertit TOUS les formats en format standardisé interne (A1)
        """
        extracted = self._extract_serpapi_data(raw_data)
        
        # Créer le format standardisé final
        standardized = {
            "nom": extracted["nom"],
            "categorie": extracted["categorie"],
            "adresse": extracted["adresse"],
            "site_web": extracted["site_web"],
            "telephone": extracted["telephone"],
            "note": extracted["note"],
            "nombre_avis": extracted["nombre_avis"],
            "horaires": extracted["horaires"],
            "avis": extracted["avis"],
            "photos": extracted["photos"],
            "resultats_recherche": extracted["resultats_recherche"],
            "recherches_associees": extracted["recherches_associees"]
        }
        
        logger.info(f"✅ Données standardisées: {standardized['nom']}")
        return standardized

    # ════════════════��═════════════════════════════════════════════
    # CRÉATION DES PROMPTS
    # ══════════════════════════════════════════════════════════════
    def create_diagnostic_prompt(self, company_data: Dict[str, Any]) -> str:
        """
        Crée un prompt optimisé pour générer un diagnostic complet.
        Inclut validation d'entrée (C3) et standardisation (A1).
        """
        # NOUVEAU: Valider l'entrée AVANT traitement (C3)
        try:
            self._validate_company_data(company_data)
        except (ValueError, TypeError) as e:
            logger.error(str(e))
            raise

        # Utiliser la standardisation
        data = self.standardize_company_data(company_data)

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

    # ══════════════════════════════════════════════════════════════
    # VALIDATION DU PROMPT (C1 - AMÉLIORÉ)
    # ══════════════════════════════════════════════════════════════
    def validate_prompt(self, prompt: str) -> bool:
        """
        Validation renforcée du prompt (C1).
        Vérifie structure, longueur, format JSON.
        """
        # Vérification 1: Longueur minimale
        longueur_minimale = 200
        if len(prompt) < longueur_minimale:
            logger.warning(f" Prompt trop court: {len(prompt)} < {longueur_minimale}")
            return False
        
        # Vérification 2: Mots-clés obligatoires DANS LES INSTRUCTIONS
        mots_cles_requis = {
            "INSTRUCTIONS": r"INSTRUCTIONS\s*:",
            "JSON": r"JSON",
            "recommandations": r"recommandation",
            "points_forts": r"points.?forts",
            "score_reputation": r"score.?reputation"
        }
        
        manquants = []
        for keyword, pattern in mots_cles_requis.items():
            if not re.search(pattern, prompt, re.IGNORECASE):
                manquants.append(keyword)
        
        if manquants:
            logger.warning(f" Mots-clés manquants: {manquants}")
            return False
        
        # Vérification 3: Structure JSON attendue
        if "{{" not in prompt or "}}" not in prompt:
            logger.warning(" Pas de template JSON trouvé ({{ et }})")
            return False
        
        # Vérification 4: Données d'entrée présentes
        if "{data['nom']}" not in prompt and "{data[" not in prompt:
            logger.warning(" Pas de placeholders de données {data[...]}")
            return False
        
        logger.info("✅ Prompt valide!")
        return True

    # ══════════════════════════════════════════════════════════════
    # PARSING JSON ROBUSTE (A4)
    # ══════════════════════════════════════════════════════════════
    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extrait le JSON d'un texte de manière robuste (A4).
        Pas de regex greedy - parcourt caractère par caractère.
        """
        stack = 0
        start_index = None
        
        for i, char in enumerate(text):
            if char == '{':
                if stack == 0:
                    start_index = i  # Potentiel début du JSON
                stack += 1
            elif char == '}':
                stack -= 1
                # Quand stack revient à 0, on a potentiellement un JSON complet
                if stack == 0 and start_index is not None:
                    potential_json = text[start_index:i+1]
                    try:
                        result = json.loads(potential_json)
                        logger.info(f"JSON extrait avec succès (caractères {start_index}-{i+1})")
                        return result
                    except json.JSONDecodeError:
                        # Ce n'était pas du JSON valide, continuer
                        start_index = None
        
        # Fallback: pas de JSON trouvé
        logger.error(" Aucun JSON valide trouvé dans la réponse")
        return None

    def _create_error_response(self, error_msg: str) -> Dict[str, Any]:
        """Crée une réponse d'erreur structurée"""
        return {
            "erreur": error_msg,
            "company_name": "Erreur",
            "points_forts": [],
            "points_faibles": [],
            "opportunites": [],
            "menaces": [],
            "position_marche": "Non analysé",
            "presence_digitale": "Non analysée",
            "score_reputation": 0,
            "recommandations": ["Relancer l'analyse"],
            "horodatage": datetime.now().isoformat()
        }

    # ══════════════════════════════════════════════════════════════
    # NETTOYAGE DE LA RÉPONSE GEMINI (A4 - AMÉLIORÉ)
    # ══════════════════════════════════════════════════════════════
    def clean_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """
        Nettoie et parse la réponse de Gemini de manière ROBUSTE (A4).
        Gère les cas où Gemini ajoute du texte avant/après le JSON.
        """
        if not response_text:
            logger.error(" Réponse vide reçue de Gemini")
            return self._create_error_response("Réponse vide")
        
        # Étape 1: Nettoyer les balises markdown basiques
        cleaned = response_text
        cleaned = cleaned.replace("```json", "").replace("```", "")
        cleaned = cleaned.strip()
        
        # Étape 2: Essayer extraction JSON robuste
        result = self._extract_json_from_text(cleaned)
        
        if result is not None:
            logger.info(" Réponse Gemini parsée avec succès")
            return result
        
        # Étape 3: Fallback - tenter un parse simple
        try:
            result = json.loads(cleaned)
            logger.info(" Réponse parsée en fallback")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Impossible de parser: {e}")
            return self._create_error_response(
                f"JSON non parseable: {str(e)[:100]}"
            )

    # ══════════════════════════════════════════════════════════════
    # VALIDATION DE LA RÉPONSE GEMINI (C2 - STRICT)
    # ══════════════════════════════════════════════════════════════
    def validate_gemini_response(self, response: Dict[str, Any]) -> bool:
        """
        Valide que la réponse Gemini contient TOUS les champs attendus (C2).
        STRICT: lève une exception si invalide (fail fast).
        """
        # Champs obligatoires
        champs_requis = [
            "company_name", 
            "points_forts", 
            "points_faibles",
            "score_reputation", 
            "recommandations"
        ]
        
        # Vérification 1: Tous les champs présents?
        manquants = [c for c in champs_requis if c not in response]
        if manquants:
            raise KeyError(f" Champs manquants: {manquants}")
        
        # Vérification 2: Types corrects?
        if not isinstance(response.get("points_forts"), list):
            raise TypeError(" 'points_forts' doit être une liste")
        
        if not isinstance(response.get("points_faibles"), list):
            raise TypeError("'points_faibles' doit être une liste")
        
        if not isinstance(response.get("recommandations"), list):
            raise TypeError(" 'recommandations' doit être une liste")
        
        if not isinstance(response.get("score_reputation"), int):
            raise TypeError(
                f" 'score_reputation' doit être un int, "
                f"reçu {type(response['score_reputation'])}"
            )
        
        # Vérification 3: Plages valides?
        if not (0 <= response["score_reputation"] <= 100):
            raise ValueError(
                f" 'score_reputation' doit être entre 0 et 100, "
                f"reçu {response['score_reputation']}"
            )
        
        # Vérification 4: Listes non vides?
        if len(response.get("points_forts", [])) == 0:
            raise ValueError(" 'points_forts' ne peut pas être vide")
        
        if len(response.get("points_faibles", [])) == 0:
            raise ValueError(" 'points_faibles' ne peut pas être vide")
        
        if len(response.get("recommandations", [])) == 0:
            raise ValueError(" 'recommandations' ne peut pas être vide")
        
        logger.info(" Réponse Gemini valide (tous les champs présents et valides)")
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
            logger.error(" Prompt invalide, arrêt du test")
            return {"erreur": "Prompt invalide"}

        logger.info("Envoi du prompt à Gemini...")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        response_text = response.text

        result = creator.clean_gemini_response(response_text)

        # CHANGEMENT: Catch les exceptions de validation
        try:
            creator.validate_gemini_response(result)
            logger.info(" Réponse Gemini valide !")
            return result
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f" Réponse invalide: {e}")
            raise

    except Exception as e:
        logger.error(f" Erreur lors de l'appel Gemini: {e}")
        return {"erreur": str(e)}


if __name__ == "__main__":
    import sys

    # ── Données de test ──
    example_company = {
        "company_name": "Samsung Tunisia",
        "results": [
            {
                "position": 1,
                "title": "Samsung Tunisie - Boutique officielle",
                "snippet": "Smartphones Galaxy, TV QLED, électroménager connecté."
            },
            {
                "position": 2,
                "title": "Samsung France",
                "snippet": "Découvrez nos produits High-Tech."
            },
            {
                "position": 3,
                "title": "Groupe Samsung - Wikipedia",
                "snippet": "Fondé en 1938, Samsung est un conglomérat mondial."
            },
        ]
    }

    creator = PromptDiagnostic()
    
    print("=" * 80)
    print("PROMPT OPTIMISÉ GÉNÉRÉ :")
    print("=" * 80)
    try:
        prompt = creator.create_diagnostic_prompt(example_company)
        print(prompt)
        
        print("\n" + "=" * 80)
        if creator.validate_prompt(prompt):
            print(" Prompt valide !")
        else:
            print(" Prompt invalide !")
    except (ValueError, TypeError) as e:
        print(f"Erreur: {e}")
        sys.exit(1)

    # ── Test avec Gemini si clé API fournie ──
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print("\n" + "=" * 80)
        print("TEST AVEC GEMINI API :")
        print("=" * 80)
        result = test_with_gemini(example_company, api_key)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("\n  Pour tester avec Gemini, ajoute GEMINI_API_KEY dans ton .env")
        print("    puis lance : python src/prompts/prompt_diagnostic.py")