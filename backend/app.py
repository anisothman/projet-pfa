"""
app.py - API Flask connectée au DiagnosticEngine
Génère le diagnostic à la volée pour n'importe quelle entreprise
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
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
                # Le moteur a retourné une erreur → tenter fallback JSON
                pass
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
def generate_pdf():
    body = request.get_json()
    if not body:
        return jsonify({"success": False, "error": "Données manquantes"}), 400

    company_name = body.get("company_name", "Inconnu")
    rating = body.get("rating", {})
    score = rating.get("score", "N/A") if isinstance(rating, dict) else "N/A"
    justification = rating.get("justification", "") if isinstance(rating, dict) else ""
    diagnostic = body.get("swot", body.get("diagnostic", "Non disponible"))
    action_plan = body.get("action_plan", "Non disponible")

    pdf_path = f"report_{company_name}.pdf"

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib import colors

        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []

        # Titre
        title_style = ParagraphStyle('Title', parent=styles['Title'],
                                     fontSize=18, textColor=colors.HexColor('#1a1a2e'))
        story.append(Paragraph(f"Rapport Diagnostic — {company_name.upper()}", title_style))
        story.append(Spacer(1, 0.5*cm))

        # Score
        story.append(Paragraph(f"<b>Score Global :</b> {score}/100", styles['Normal']))
        if justification:
            story.append(Paragraph(f"<i>{justification}</i>", styles['Normal']))
        story.append(Spacer(1, 0.5*cm))

        # SWOT
        story.append(Paragraph("<b>Analyse SWOT</b>", styles['Heading2']))
        for line in diagnostic.split('\n'):
            if line.strip():
                story.append(Paragraph(line, styles['Normal']))
        story.append(Spacer(1, 0.5*cm))

        # Plan d'action
        story.append(Paragraph("<b>Plan d'Action</b>", styles['Heading2']))
        for line in action_plan.split('\n'):
            if line.strip():
                story.append(Paragraph(line, styles['Normal']))

        doc.build(story)
        return send_file(pdf_path, as_attachment=True,
                         download_name=f"diagnostic_{company_name}.pdf")

    except ImportError:
        # Fallback PDF minimal sans reportlab avancé
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            c = canvas.Canvas(pdf_path, pagesize=A4)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, 800, f"Rapport: {company_name}")
            c.setFont("Helvetica", 12)
            c.drawString(50, 780, f"Score: {score}/100")
            c.drawString(50, 760, "Voir le portail pour le détail complet.")
            c.save()
            return send_file(pdf_path, as_attachment=True)
        except Exception as e:
            return jsonify({"success": False, "error": f"Erreur PDF: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur génération PDF: {str(e)}"}), 500


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