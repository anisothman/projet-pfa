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
SPRINT1_DATA_DIR = PROJET_ROOT / "sprint1" / "data"
SPRINT2_SRC_DIR = PROJET_ROOT / "sprint2" / "src"
SPRINT3_DIR = PROJET_ROOT / "sprint3"

sys.path.insert(0, str(SPRINT2_SRC_DIR))
sys.path.insert(0, str(SPRINT3_DIR))

try:
    from gemini_client import call_gemini
    print("✅ gemini_client chargé")
except ImportError:
    def call_gemini(prompt):
        return f"[SIMULATION] {prompt[:100]}..."

# ===== INITIALISATION FLASK =====
app = Flask(__name__)
CORS(app)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/companies", methods=["GET"])
def list_companies():
    try:
        files = list(SPRINT1_DATA_DIR.glob("*_results.json"))
        companies = [f.stem.replace("_results", "") for f in files]
        return jsonify({"success": True, "companies": companies})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        data = request.json
        company_name = data.get("company_name", "").strip().lower()
        if not company_name:
            return jsonify({"error": "Nom requis"}), 400
        
        # Chercher le fichier (insensible à la casse)
        files = list(SPRINT1_DATA_DIR.glob("*_results.json"))
        found_file = None
        for file in files:
            if file.stem.replace("_results", "").lower() == company_name:
                found_file = file
                break
        
        if not found_file:
            return jsonify({"error": f"Entreprise '{company_name}' non trouvée"}), 404
        
        with open(found_file, encoding="utf-8") as f:
            business_data = json.load(f)
        
        prompt = f"Analyse SWOT de {company_name}: {json.dumps(business_data, ensure_ascii=False)[:2000]}"
        diagnostic = call_gemini(prompt)
        
        prompt_plan = f"Plan d'action pour {company_name}: {diagnostic[:1500]}"
        plan_action = call_gemini(prompt_plan)
        
        return jsonify({
            "success": True,
            "company_name": company_name,
            "diagnostic": diagnostic,
            "plan_action": plan_action
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/generate-pdf", methods=["POST"])
def generate_pdf():
    try:
        data = request.json
        from pdf_generator import generate_pdf as gen_pdf
        result = gen_pdf(data.get("company_name", ""), data.get("diagnostic", ""), data.get("plan_action", ""))
        if result.get("success"):
            return send_file(result["filepath"], as_attachment=True)
        return jsonify({"error": result.get("error")}), 500
    except ImportError:
        return jsonify({"error": "pdf_generator.py non trouvé"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print(f"📁 Racine: {PROJET_ROOT}")
    print(f"🌐 API: http://localhost:5000")
    app.run(debug=True, port=5000)