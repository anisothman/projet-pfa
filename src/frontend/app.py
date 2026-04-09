from flask import Flask, request, jsonify
from gemini_client import analyze_business
import json
import os

app = Flask(__name__)

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    nom = data.get("nom")
    localisation = data.get("localisation")
    
    # Charger le JSON du Sprint 1
    json_path = f"../data/{nom}_results.json"
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            business_data = json.load(f)
        
        diagnostic = analyze_business(business_data, "diagnostic")
        plan = analyze_business(business_data, "plan d'action")
        
        return jsonify({
            "diagnostic": diagnostic,
            "plan_action": plan
        })
    
    except FileNotFoundError:
        return jsonify({"erreur": "Entreprise introuvable"}), 404

if __name__ == "__main__":
    app.run(debug=True)
