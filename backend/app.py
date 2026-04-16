"""
app.py - API Flask connectée au DiagnosticEngine
Génère le diagnostic à la volée pour n'importe quelle entreprise
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
import re
import sys

app = Flask(__name__)
CORS(app)

DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

# -------------------------
# IMPORT DU MOTEUR
# -------------------------
try:
    from diagnostic_engine import DiagnosticEngine
    engine = DiagnosticEngine(data_dir=DATA_FOLDER)
    ENGINE_AVAILABLE = True
    print("✅ DiagnosticEngine chargé avec succès")
except ImportError as e:
    print(f"⚠️ DiagnosticEngine non disponible: {e}")
    ENGINE_AVAILABLE = False
    engine = None


# -------------------------
# LISTE ENTREPRISES
# -------------------------
@app.route('/api/companies', methods=['GET'])
def companies():
    try:
        files = os.listdir(DATA_FOLDER)
        # Nettoie les noms : retire le suffixe _results.json
        company_list = []
        for f in files:
            if f.endswith("_results.json"):
                name = f.replace("_results.json", "")
                company_list.append(name)
            elif f.endswith(".json"):
                name = f.replace(".json", "")
                company_list.append(name)
        return jsonify({"success": True, "companies": company_list})


    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# -------------------------
# ANALYSE ENTREPRISE
# -------------------------
@app.route('/api/analyze', methods=['POST'])
def analyze():
    body = request.get_json()
    if not body:
        return jsonify({"success": False, "error": "Corps de requête manquant"}), 400

    company = body.get("company_name", "").strip().lower()

    if not company:
        return jsonify({"success": False, "error": "Nom d'entreprise manquant"}), 400

    # ---------------------------------------------------------
    # STRATÉGIE : Essayer DiagnosticEngine en premier
    # Il génère le diagnostic via IA (SWOT + Plan + Rating)
    # ---------------------------------------------------------
    if ENGINE_AVAILABLE and engine:
        try:
            result = engine.analyze_company(company)

            if result.get("success"):
                return jsonify({
                    "success": True,
                    "company_name": company,
                    "swot": result.get("swot", ""),
                    "action_plan": result.get("action_plan", ""),
                    "rating": result.get("rating", {"score": 50, "justification": "N/A"}),
                    "diagnostic": result.get("swot", ""),  # Alias pour compatibilité PDF
                    "source": "diagnostic_engine"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": f"Aucune donnée trouvée pour '{company}'. "
                    f"Vérifiez que le nom correspond à une entreprise dans notre base."
            }), 404

        except Exception as e:
            print(f"⚠️ Erreur DiagnosticEngine: {e}")

    # ---------------------------------------------------------
    # FALLBACK : Chercher un fichier JSON existant
    # Accepte deux formats de nommage : {company}.json et {company}_results.json
    # ---------------------------------------------------------
    possible_paths = [
        os.path.join(DATA_FOLDER, f"{company}_results.json"),
        os.path.join(DATA_FOLDER, f"{company}.json"),
    ]

    for file_path in possible_paths:
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Normalisation des champs
                swot = data.get("swot", data.get("diagnostic", "Non disponible"))
                plan = data.get("action_plan", data.get("plan", "Non disponible"))
                rating = data.get("rating", {"score": 50, "justification": "Non disponible"})

                return jsonify({
                    "success": True,
                    "company_name": company,
                    "swot": swot,
                    "action_plan": plan,
                    "rating": rating,
                    "diagnostic": swot,
                    "source": "json_file"
                })
            except Exception as e:
                return jsonify({"success": False, "error": f"Erreur lecture fichier: {str(e)}"}), 500

    # ---------------------------------------------------------
    # DERNIER RECOURS : Générer un diagnostic générique
    # Au lieu de retourner "entreprise introuvable", on génère
    # un diagnostic de base avec les infos disponibles.
    # ---------------------------------------------------------
    print(f"ℹ️ Aucune donnée pour '{company}', génération d'un diagnostic générique")

    generic_swot = f"""ANALYSE SWOT DE {company.upper()}:

FORCES:
- Positionnement sur son marché
- Potentiel d'innovation
- Base clients existante

FAIBLESSES:
- Données limitées disponibles pour une analyse approfondie
- Nécessite une collecte de données supplémentaires

OPPORTUNITÉS:
- Expansion dans de nouveaux marchés
- Digitalisation et transformation numérique
- Nouvelles tendances sectorielles

MENACES:
- Concurrence croissante
- Évolutions réglementaires
- Volatilité économique
"""

    generic_plan = f"""PLAN D'ACTION POUR {company.upper()}:

COURT TERME (0-3 mois):
- Collecte et analyse des données de marché
- Audit de la présence digitale
- Identification des axes prioritaires

MOYEN TERME (3-6 mois):
- Développement de la stratégie digitale
- Optimisation de la présence en ligne
- Renforcement de la relation client

LONG TERME (6-12 mois):
- Consolidation du positionnement marché
- Innovation produit/service
- Expansion géographique ou sectorielle
"""

    return jsonify({
        "success": True,
        "company_name": company,
        "swot": generic_swot,
        "action_plan": generic_plan,
        "rating": {
            "score": 50,
            "justification": "Analyse générique — aucune donnée spécifique disponible pour cette entreprise."
        },
        "diagnostic": generic_swot,
        "source": "generic_fallback",
        "warning": "Aucune donnée spécifique trouvée. Diagnostic générique généré."
    })


# -------------------------
# GÉNÉRATION PDF
# -------------------------
@app.route('/api/generate-pdf', methods=['POST'])
def generate_pdf_route():
    body = request.get_json()
    if not body:
        return jsonify({"success": False, "error": "Données manquantes"}), 400

    company_name = body.get("company_name", "Inconnu")
    rating = body.get("rating", {})

    # --- Récupération du score ---
    if isinstance(rating, dict):
        score_raw = rating.get("score", 50)
    else:
        score_raw = 50
    try:
        score = max(0, min(100, int(score_raw)))
    except (ValueError, TypeError):
        score = 50

    # --- Conversion SWOT texte → structure attendue par pdf01_generator ---
    # On tente d'abord le format structuré (dict avec listes), puis on fait
    # un parsing minimal du texte si nécessaire.
    swot_raw = body.get("swot", body.get("diagnostic", ""))
    plan_raw = body.get("action_plan", "")

    # Si les données sont déjà sous forme de dict structuré (provenant du moteur IA),
    # on les utilise directement via adapt_for_pdf_generator.
    # Sinon on les convertit depuis le texte brut.
    analysis_dict = body.get("structured_analysis")

    if analysis_dict and isinstance(analysis_dict, dict):
        # Données structurées disponibles → utiliser l'adaptateur
        score, swot_analysis, action_plan = adapt_for_pdf_generator(analysis_dict, company_name)
    else:
        # Données textuelles brutes → parser et structurer
        swot_analysis = _parse_swot_text(swot_raw)
        action_plan   = _parse_plan_text(plan_raw)

    # --- Génération du PDF via pdf01_generator ---
    try:
        from pdf01_generator import generate_pdf as pdf_gen
        import tempfile, os

        tmp_path = os.path.join(tempfile.gettempdir(), f"diagnostic_{company_name}.pdf")
        result = pdf_gen(
            company_name=company_name,
            score=score,
            swot_analysis=swot_analysis,
            action_plan=action_plan,
            output_path=tmp_path
        )

        if result.get("success"):
            return send_file(
                result["filepath"],
                as_attachment=True,
                download_name=f"diagnostic_{company_name}.pdf",
                mimetype="application/pdf"
            )
        else:
            return jsonify({"success": False, "error": result.get("error", "Erreur inconnue")}), 500

    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur génération PDF: {str(e)}"}), 500


# ── Parsers texte brut → structures pdf01_generator ──────────────────────────

def _items_from_lines(lines: list) -> list:
    """Convertit une liste de lignes en items {titre, description}."""
    items = []
    for line in lines:
        line = line.strip().lstrip("-•*").strip()
        if line:
            items.append({"titre": line, "description": ""})
    return items or [{"titre": "Information non disponible", "description": ""}]


def _parse_swot_text(text: str) -> dict:
    """
    Parse un texte SWOT brut (sections FORCES / FAIBLESSES / OPPORTUNITÉS / MENACES)
    en dict structuré attendu par pdf01_generator.
    """
    sections = {
        "points_forts":   [],
        "points_faibles": [],
        "opportunites":   [],
        "menaces":        [],
    }

    # Mapping souple des en-têtes
    key_map = {
        "force": "points_forts", "fort": "points_forts", "strengths": "points_forts",
        "point fort": "points_forts",
        "faible": "points_faibles", "weakness": "points_faibles", "amelior": "points_faibles",
        "point faible": "points_faibles", "faiblesses": "points_faibles",
        "opportun": "opportunites", "opportunité": "opportunites",
        "menace": "menaces", "threat": "menaces",
    }

    current_key = None
    current_lines = []

    def flush():
        if current_key and current_lines:
            sections[current_key].extend(_items_from_lines(current_lines))

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        # Détecter un en-tête de section (ligne en majuscules ou contenant ":")
        upper = stripped.upper()
        matched_key = None
        for kw, sk in key_map.items():
            if kw.upper() in upper:
                matched_key = sk
                break

        if matched_key and (stripped.isupper() or stripped.endswith(":")):
            flush()
            current_key = matched_key
            current_lines = []
        elif current_key:
            current_lines.append(stripped)

    flush()

    # S'assurer qu'aucune section n'est vide
    for key in sections:
        if not sections[key]:
            sections[key] = [{"titre": "Information non disponible", "description": ""}]

    return sections


def _parse_plan_text(text: str) -> dict:
    """
    Parse un texte de plan d'action brut (Court/Moyen/Long terme)
    en dict structuré attendu par pdf01_generator.
    """
    plan = {
        "court_terme":  [],
        "moyen_terme":  [],
        "long_terme":   [],
    }

    key_map = {
        "court": "court_terme", "0-3": "court_terme", "0 - 3": "court_terme",
        "immédiat": "court_terme", "immediat": "court_terme",
        "moyen": "moyen_terme", "3-6": "moyen_terme", "3 - 6": "moyen_terme",
        "long": "long_terme",   "6-12": "long_terme",  "6 - 12": "long_terme",
    }

    current_key = None
    current_lines = []

    def flush():
        if current_key and current_lines:
            plan[current_key].extend(_items_from_lines(current_lines))

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        upper = stripped.upper()
        matched_key = None
        for kw, pk in key_map.items():
            if kw.upper() in upper:
                matched_key = pk
                break

        if matched_key and (stripped.isupper() or stripped.endswith(":")):
            flush()
            current_key = matched_key
            current_lines = []
        elif current_key:
            current_lines.append(stripped)

    flush()

    for key in plan:
        if not plan[key]:
            plan[key] = [{"titre": "Action non définie", "description": ""}]

    return plan


# -------------------------
# HEALTH CHECK
# -------------------------
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "engine_available": ENGINE_AVAILABLE,
        "data_folder": DATA_FOLDER
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)






def adapt_for_pdf_generator(analysis: dict, company_name: str) -> tuple:
    """
    Adapte la sortie de l'IA au format attendu par pdf01_generator.py
    Retourne (score, swot_analysis, action_plan)
    """
    
    # 1. S'assurer que le score est un entier entre 0 et 100
    score = analysis.get("score", 50)
    if isinstance(score, str):
        score = int(re.sub(r'[^0-9]', '', score)) if score else 50
    score = max(0, min(100, int(score)))
    
    # 2. Adapter SWOT - S'assurer que chaque item a "titre" et "description"
    swot = analysis.get("swot_analysis", {})
    
    def format_items(items):
        """Convertit les items au format {titre, description}"""
        if not items:
            return []
        formatted = []
        for item in items:
            if isinstance(item, dict):
                # Si l'item a déjà le bon format
                if "titre" in item or "title" in item:
                    titre = item.get("titre") or item.get("title") or str(item)
                    desc = item.get("description") or item.get("desc") or ""
                else:
                    # Si l'item est un dictionnaire mais sans titre/description
                    keys = list(item.keys())
                    if keys:
                        titre = keys[0] if keys else str(item)
                        desc = item[keys[0]] if keys else ""
                    else:
                        titre = "Information"
                        desc = ""
            elif isinstance(item, str):
                # Si l'item est juste une string
                titre = item
                desc = ""
            else:
                titre = str(item)
                desc = ""
            
            formatted.append({
                "titre": normalize_text(titre),
                "description": normalize_text(desc)
            })
        return formatted
    
    swot_analysis = {
        "points_forts": format_items(swot.get("points_forts", [])),
        "points_faibles": format_items(swot.get("points_faibles", [])),
        "opportunites": format_items(swot.get("opportunites", [])),
        "menaces": format_items(swot.get("menaces", []))
    }
    
    # 3. Adapter Plan d'action
    plan = analysis.get("action_plan", {})
    
    action_plan = {
        "court_terme": format_items(plan.get("court_terme", [])),
        "moyen_terme": format_items(plan.get("moyen_terme", [])),
        "long_terme": format_items(plan.get("long_terme", []))
    }
    
    return score, swot_analysis, action_plan