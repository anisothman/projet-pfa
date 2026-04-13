<<<<<<< Updated upstream
﻿@app.route("/api/generate-pdf", methods=["POST"])
=======
"""
app.py - Sprint 3 Backend Flask
Responsable : Anis
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import sys
from pathlib import Path

# ===== CHEMINS =====
def get_projet_root():
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "sprint1").exists() or (parent / "sprint2").exists():
            return parent
    return current.parent.parent

PROJET_ROOT = get_projet_root()

DATA_DIR = PROJET_ROOT / "data"
if not DATA_DIR.exists():
    DATA_DIR = PROJET_ROOT / "sprint1" / "data"

SPRINT2_SRC_DIR = PROJET_ROOT / "sprint2" / "src"
SPRINT3_DIR = PROJET_ROOT / "sprint3"
SRC_DIR = PROJET_ROOT / "src"

sys.path.insert(0, str(SPRINT2_SRC_DIR))
sys.path.insert(0, str(SPRINT3_DIR))
sys.path.insert(0, str(SRC_DIR))

try:
    from diagnostic_engine import DiagnosticEngine
    print(f"✅ DiagnosticEngine chargé depuis src/")
    diagnostic_engine = DiagnosticEngine(data_dir=DATA_DIR)
except ImportError as e:
    print(f"⚠️ Erreur import DiagnosticEngine: {e}")
    diagnostic_engine = None

app = Flask(__name__)
CORS(app)


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "message": "API Sprint 3 operationnelle"
    })


@app.route("/api/companies", methods=["GET"])
def list_companies():
    try:
        json_files = list(DATA_DIR.glob("*_results.json"))
        companies = [f.stem.replace("_results", "") for f in json_files]
        return jsonify({
            "success": True,
            "companies": companies,
            "count": len(companies)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/analyze", methods=["POST"])
def analyze_company():
    try:
        data = request.json
        company_name = data.get("company_name", "").strip().lower()

        if not company_name:
            return jsonify({"success": False, "error": "Nom d'entreprise requis"}), 400

        # Si le fichier JSON n'existe pas → collecte via SerpAPI
        json_path = DATA_DIR / f"{company_name}_results.json"
        if not json_path.exists():
            print(f"🔍 Collecte SerpAPI pour : {company_name}")
            try:
                from serpapi import GoogleSearch
                from config import SERPAPI_KEY
                params = {
                    "q": company_name,
                    "hl": "fr",
                    "gl": "tn",
                    "num": 10,
                    "api_key": SERPAPI_KEY
                }
                search = GoogleSearch(params)
                resultat = search.get_dict()
                DATA_DIR.mkdir(exist_ok=True)
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(resultat, f, ensure_ascii=False, indent=2)
                print(f"✅ Données sauvegardées : {json_path}")
            except Exception as e:
                return jsonify({"success": False, "error": f"Erreur collecte SerpAPI: {str(e)}"}), 500

        # Analyse avec DiagnosticEngine (Gemini)
        if diagnostic_engine:
            result = diagnostic_engine.analyze_company(company_name)
            if result["success"]:
                return jsonify({
                    "success": True,
                    "company_name": company_name,
                    "diagnostic": result["swot"],
                    "plan_action": result["action_plan"],
                    "rating": result.get("rating", {"score": 50, "justification": "Non disponible"})
                })
            else:
                return jsonify({"success": False, "error": result.get("error", "Erreur d'analyse")}), 404
        else:
            return jsonify({"success": False, "error": "DiagnosticEngine non disponible"}), 500

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/generate-pdf", methods=["POST"])
>>>>>>> Stashed changes
def generate_pdf():
    """Génère un PDF à partir du diagnostic et plan d'action"""
    try:
        data = request.json
        company_name = data.get("company_name", "entreprise")
        
        # Récupérer les données structurées
        diagnostic_data = data.get("diagnostic", {})
        plan_action_data = data.get("plan_action", {})
        rating = data.get("rating", {"score": 50, "justification": ""})
        
        # Extraire le score
        score = rating.get("score", 50) if isinstance(rating, dict) else 50
        
        # Structurer les données SWOT
        swot_analysis = {}
        action_plan = {}
        
        # Si diagnostic est une chaîne (texte brut), la parser
        if isinstance(diagnostic_data, str):
            swot_analysis = _parse_swot_text(diagnostic_data)
        elif isinstance(diagnostic_data, dict):
            swot_analysis = {
                "points_forts": diagnostic_data.get("points_forts", diagnostic_data.get("forces", [])),
                "points_faibles": diagnostic_data.get("points_faibles", diagnostic_data.get("faiblesses", [])),
                "opportunites": diagnostic_data.get("opportunites", diagnostic_data.get("opportunities", [])),
                "menaces": diagnostic_data.get("menaces", diagnostic_data.get("threats", []))
            }
        else:
            swot_analysis = {
                "points_forts": [],
                "points_faibles": [],
                "opportunites": [],
                "menaces": []
            }
        
        # Si plan_action est une chaîne (texte brut), la parser
        if isinstance(plan_action_data, str):
            action_plan = _parse_plan_text(plan_action_data)
        elif isinstance(plan_action_data, dict):
            action_plan = {
                "court_terme": plan_action_data.get("court_terme", plan_action_data.get("short_term", [])),
                "moyen_terme": plan_action_data.get("moyen_terme", plan_action_data.get("mid_term", [])),
                "long_terme": plan_action_data.get("long_terme", plan_action_data.get("long_term", []))
            }
        else:
            action_plan = {
                "court_terme": [],
                "moyen_terme": [],
                "long_terme": []
            }
        
        # ⚠️ IMPORT CORRIGÉ : pdf01_generator.py au lieu de pdf_generator.py
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        from pdf01_generator import generate_pdf as generate_pdf_report
        
        # Appeler avec les bons paramètres
        result = generate_pdf_report(
            company_name=company_name,
            score=score,
            swot_analysis=swot_analysis,
            action_plan=action_plan
        )
        
=======

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from pdf_generator import generate_pdf as generate_pdf_report

>>>>>>> Stashed changes
        if result.get("success"):
            return send_file(
                result["filepath"],
                as_attachment=True,
                download_name=f"diagnostic_{company_name}.pdf"
            )
        else:
            return jsonify({"success": False, "error": result.get("error")}), 500

    except ImportError as e:
        return jsonify({"success": False, "error": f"pdf01_generator.py non trouve: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def _parse_swot_text(text: str) -> dict:
    """Convertit un texte SWOT en dictionnaire structuré"""
    swot = {
        "points_forts": [],
        "points_faibles": [],
        "opportunites": [],
        "menaces": []
    }
    
    if not text or not isinstance(text, str):
        return swot
    
    current_section = None
    lines = text.split('\n')
    
    for line in lines:
        line_lower = line.lower().strip()
        
        if 'forces' in line_lower or 'points forts' in line_lower:
            current_section = 'points_forts'
            continue
        elif 'faiblesses' in line_lower or 'points faibles' in line_lower:
            current_section = 'points_faibles'
            continue
        elif 'opportunites' in line_lower:
            current_section = 'opportunites'
            continue
        elif 'menaces' in line_lower:
            current_section = 'menaces'
            continue
        
        if current_section and line:
            line_stripped = line.strip()
            if line_stripped and line_stripped[0] in '-•*':
                item = line_stripped.lstrip('-•* ').strip()
                if item and len(item) > 3:
                    swot[current_section].append({"titre": item[:80], "description": ""})
    
    if not any(swot.values()):
        swot["points_forts"] = [{"titre": "Données en cours d'analyse", "description": ""}]
    
    return swot


def _parse_plan_text(text: str) -> dict:
    """Convertit un texte de plan d'action en dictionnaire structuré"""
    import re
    
    plan = {
        "court_terme": [],
        "moyen_terme": [],
        "long_terme": []
    }
    
    if not text or not isinstance(text, str):
        return plan
    
    current_period = None
    lines = text.split('\n')
    
    for line in lines:
        line_lower = line.lower().strip()
        line_stripped = line.strip()
        
        if 'court terme' in line_lower or '0-6 mois' in line_lower or 'immediate' in line_lower:
            current_period = 'court_terme'
            continue
        elif 'moyen terme' in line_lower or '6-18 mois' in line_lower:
            current_period = 'moyen_terme'
            continue
        elif 'long terme' in line_lower or '18+ mois' in line_lower:
            current_period = 'long_terme'
            continue
        
        if current_period and line_stripped:
            first_char = line_stripped[0] if line_stripped else ''
            if first_char.isdigit() or first_char in '-•*':
                item = re.sub(r'^[\d\-•*\.\s]+', '', line_stripped).strip()
                if item and len(item) > 3:
                    plan[current_period].append({"titre": item[:80], "description": ""})
    
    return plan    print("  SPRINT 3 - BACKEND (Anis)")
    print("="*50)
    print(f"  📁 Racine projet: {PROJET_ROOT}")
    print(f"  📁 Donnees: {DATA_DIR}")
    print(f"  📁 Src modules: {SRC_DIR}")
    print(f"  🌐 API: http://localhost:5000")
    print("="*50 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
>>>>>>> Stashed changes
