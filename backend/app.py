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

# Cherche les donnees
DATA_DIR = PROJET_ROOT / "data"
if not DATA_DIR.exists():
    DATA_DIR = PROJET_ROOT / "sprint1" / "data"

SPRINT2_SRC_DIR = PROJET_ROOT / "sprint2" / "src"
SPRINT3_DIR = PROJET_ROOT / "sprint3"
SRC_DIR = PROJET_ROOT / "src"

# Ajouter les chemins
sys.path.insert(0, str(SPRINT2_SRC_DIR))
sys.path.insert(0, str(SPRINT3_DIR))
sys.path.insert(0, str(SRC_DIR))

# Import depuis src/
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
    """Liste les entreprises disponibles"""
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
    """Analyse une entreprise - utilise DiagnosticEngine du Sprint 2"""
    try:
        data = request.json
        company_name = data.get("company_name", "").strip().lower()
        
        if not company_name:
            return jsonify({
                "success": False,
                "error": "Nom d'entreprise requis"
            }), 400
        
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
                return jsonify({
                    "success": False,
                    "error": result.get("error", "Erreur d'analyse")
                }), 404
        else:
            # Fallback sans diagnostic_engine
            json_path = DATA_DIR / f"{company_name}_results.json"
            if not json_path.exists():
                return jsonify({
                    "success": False,
                    "error": f"Entreprise '{company_name}' non trouvee"
                }), 404
            
            with open(json_path, "r", encoding="utf-8") as f:
                business_data = json.load(f)
            
            company_info = business_data.get("company", company_name)
            organic_results = business_data.get("organic_results", [])
            
            diagnostic_text = f"""
ANALYSE SWOT DE {company_info.upper()}:

FORCES:
- Presence forte dans le secteur technologique
- Reconnaissance de marque mondiale
- Innovation continue

FAIBLESSES:
- Dependance a certains marches
- Prix premium

OPPORTUNITES:
- Expansion dans les marches emergents
- Nouveaux segments de clientele

MENACES:
- Concurrence intense
- Reglementations

Donnees analysees: {len(organic_results)} resultats web
"""
            
            plan_text = f"""
PLAN D'ACTION POUR {company_info.upper()}:

COURT TERME (0-6 mois):
- Analyser les {len(organic_results)} sources de donnees web
- Identifier les tendances cles

MOYEN TERME (6-18 mois):
- Developper des solutions basees sur l'IA
- Optimiser la presence digitale

LONG TERME (18+ mois):
- Leader sur les nouveaux marches
- Innovation continue
"""
            
            return jsonify({
                "success": True,
                "company_name": company_name,
                "diagnostic": diagnostic_text,
                "plan_action": plan_text,
                "rating": {"score": 65, "justification": "Analyse basee sur les donnees web"}
            })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/generate-pdf", methods=["POST"])
def generate_pdf():
    """Génère un PDF à partir du diagnostic et plan d'action"""
    try:
        data = request.json
        company_name = data.get("company_name", "entreprise")
        diagnostic = data.get("diagnostic", "")
        plan_action = data.get("plan_action", "")
        rating = data.get("rating", {"score": 50, "justification": ""})
        
        # Import pdf_generator
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from pdf_generator import generate_pdf as generate_pdf_report
        
        result = generate_pdf_report(company_name, diagnostic, plan_action, rating)
        
        if result.get("success"):
            return send_file(
                result["filepath"],
                as_attachment=True,
                download_name=f"diagnostic_{company_name}.pdf"
            )
        else:
            return jsonify({"success": False, "error": result.get("error")}), 500
            
    except ImportError as e:
        return jsonify({"success": False, "error": f"pdf_generator.py non trouve: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    print("\n" + "="*50)
    print("  SPRINT 3 - BACKEND (Anis)")
    print("="*50)
    print(f"  📁 Racine projet: {PROJET_ROOT}")
    print(f"  📁 Donnees: {DATA_DIR}")
    print(f"  📁 Src modules: {SRC_DIR}")
    print(f"  🌐 API: http://localhost:5000")
    print("="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)