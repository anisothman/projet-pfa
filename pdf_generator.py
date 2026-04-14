"""
pdf_generator.py — Générateur PDF avec ReportLab
S'intègre avec diagnostic_engine.py pour produire des rapports professionnels
"""

import re
from datetime import datetime
from pathlib import Path
import json
import logging

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle, PageBreak
)

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Palette de couleurs professionnelle ──
SKY_DARK   = colors.HexColor("#0077A8")
SKY_MED    = colors.HexColor("#00B4D8")
SKY_LIGHT  = colors.HexColor("#48CAE4")
SKY_XLIGHT = colors.HexColor("#ADE8F4")
SKY_PALE   = colors.HexColor("#E8F8FC")
WHITE      = colors.white
BLACK      = colors.HexColor("#111111")
GRAY       = colors.HexColor("#666666")
ACCENT     = colors.HexColor("#FF6600")


def normalize_text(text: str) -> str:
    """Nettoie le texte pour éviter les problèmes d'encodage"""
    if not text:
        return ""
    text = str(text)
    # Remplacer les caractères problématiques
    replacements = {
        '"': '"', '"': '"', ''': "'", ''': "'",
        '«': '"', '»': '"', '–': '-', '—': '-',
        '…': '...', '€': 'EUR', '°': '°',
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    # Supprimer les caractères non imprimables
    text = re.sub(r'[^\x20-\x7E\u00C0-\u00FF\u0100-\u017F]', '', text)
    return text.strip()


def get_styles():
    b = getSampleStyleSheet()
    return {
        # En-tête
        "h_title": ParagraphStyle("hTitle", parent=b["Normal"],
            fontSize=13, textColor=WHITE, fontName="Helvetica-Bold",
            leading=19, alignment=TA_CENTER),
        "h_date": ParagraphStyle("hDate", parent=b["Normal"],
            fontSize=8, textColor=colors.HexColor("#CCF0F8"), fontName="Helvetica",
            leading=12, alignment=TA_RIGHT),

        # Score
        "score_label": ParagraphStyle("scoreLabel", parent=b["Normal"],
            fontSize=11, textColor=GRAY, fontName="Helvetica-Bold",
            leading=16, alignment=TA_CENTER, spaceAfter=6),
        "score": ParagraphStyle("score", parent=b["Normal"],
            fontSize=26, textColor=ACCENT, fontName="Helvetica-Bold",
            leading=32, alignment=TA_CENTER),

        # Barres de section
        "sec_bar": ParagraphStyle("secBar", parent=b["Normal"],
            fontSize=12, textColor=WHITE, fontName="Helvetica-Bold",
            leading=16, alignment=TA_LEFT),

        # SWOT catégorie
        "swot_cat": ParagraphStyle("swotCat", parent=b["Normal"],
            fontSize=10, textColor=BLACK, fontName="Helvetica-Bold",
            leading=16, spaceBefore=8, spaceAfter=4),

        # SWOT item
        "swot_item": ParagraphStyle("swotItem", parent=b["Normal"],
            fontSize=9.5, textColor=BLACK, fontName="Helvetica",
            leading=15, leftIndent=12, spaceAfter=3),

        # Plan sous-titre
        "plan_sub": ParagraphStyle("planSub", parent=b["Normal"],
            fontSize=10, textColor=WHITE, fontName="Helvetica-Bold",
            leading=14, alignment=TA_LEFT),

        # Plan item
        "plan_item": ParagraphStyle("planItem", parent=b["Normal"],
            fontSize=9.5, textColor=BLACK, fontName="Helvetica",
            leading=15, leftIndent=12, spaceAfter=4),

        # Pied de page
        "footer": ParagraphStyle("footer", parent=b["Normal"],
            fontSize=8, textColor=GRAY, alignment=TA_CENTER),
    }


def section_bar(title, st, pw, color=SKY_DARK):
    """Barre de section colorée"""
    t = Table([[Paragraph(f"  {title}", st["sec_bar"])]], colWidths=[pw])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), color),
        ("TOPPADDING",    (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("BOX",           (0, 0), (-1, -1), 0, colors.white),
    ]))
    return t


def swot_block(label, items, st, pw):
    """Bloc SWOT avec fond coloré sans bordures visibles"""
    if not items:
        items = [{"titre": "Aucune information disponible", "description": ""}]
    
    rows = []
    rows.append([Paragraph(f"<b>{label}</b>", st["swot_cat"])])
    
    for item in items:
        if isinstance(item, dict):
            titre = normalize_text(item.get("titre", ""))
            desc = normalize_text(item.get("description", ""))
        else:
            titre = normalize_text(str(item))
            desc = ""
        
        text = f"•   {titre}"
        if desc:
            text = f"•   {titre}<br/><font size='8' color='#666666'>{desc}</font>"
        rows.append([Paragraph(text, st["swot_item"])])
    
    t = Table(rows, colWidths=[pw])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), SKY_PALE),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 20),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("BOX",           (0, 0), (-1, -1), 0, colors.white),
        ("INNERGRID",     (0, 0), (-1, -1), 0, colors.white),
    ]))
    return t


def plan_block(subtitle, items, st, pw, color):
    """Bloc Plan d'action avec fond coloré"""
    if not items:
        items = []
    
    elems = []
    
    # Barre de sous-titre
    sub_table = Table([[Paragraph(f"  {subtitle}", st["plan_sub"])]], colWidths=[pw])
    sub_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), color),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 0, colors.white),
    ]))
    elems.append(sub_table)
    elems.append(Spacer(1, 0.1*cm))
    
    if items:
        rows = []
        for i, item in enumerate(items, 1):
            if isinstance(item, dict):
                titre = normalize_text(item.get("titre", item.get("action", "")))
                desc = normalize_text(item.get("description", ""))
            else:
                titre = normalize_text(str(item))
                desc = ""
            
            text = f"{i}.   {titre}"
            if desc:
                text = f"{i}.   {titre}<br/><font size='8' color='#666666'>{desc}</font>"
            rows.append([Paragraph(text, st["plan_item"])])
        
        if rows:
            body = Table(rows, colWidths=[pw])
            body.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), SKY_PALE),
                ("TOPPADDING",    (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING",   (0, 0), (-1, -1), 20),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
                ("BOX",           (0, 0), (-1, -1), 0, colors.white),
                ("INNERGRID",     (0, 0), (-1, -1), 0, colors.white),
            ]))
            elems.append(body)
    else:
        empty_text = Paragraph("Aucune action définie pour cette période", 
                               ParagraphStyle("empty", parent=st["plan_item"], 
                                            textColor=GRAY, fontName="Helvetica-Oblique"))
        empty_table = Table([[empty_text]], colWidths=[pw])
        empty_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SKY_PALE),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 20),
            ("BOX", (0, 0), (-1, -1), 0, colors.white),
        ]))
        elems.append(empty_table)
    
    elems.append(Spacer(1, 0.2*cm))
    return elems


def generate_pdf(
    company_name: str,
    score: int,
    swot_analysis: dict,
    action_plan: dict,
    output_path: str = None
) -> dict:
    """Génère un PDF professionnel à partir des données du diagnostic"""
    try:
        # Nettoyer le nom pour le fichier
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', company_name)[:30]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_path:
            fp = Path(output_path)
        else:
            fp = REPORTS_DIR / f"diagnostic_{safe_name}_{timestamp}.pdf"
        
        fp.parent.mkdir(parents=True, exist_ok=True)
        
        # Configuration du document
        doc = SimpleDocTemplate(
            str(fp), pagesize=A4,
            topMargin=1.5*cm, bottomMargin=1.8*cm,
            leftMargin=1.5*cm, rightMargin=1.5*cm,
        )
        
        st = get_styles()
        pw = A4[0] - 3*cm
        date_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
        story = []
        
        # ═══════════════════════════════════════════════════════════════════
        # PAGE 1 - EN-TÊTE
        # ═══════════════════════════════════════════════════════════════════
        header = Table(
            [[
                Paragraph("", st["h_date"]),
                Paragraph(
                    f"Rapport Diagnostic de l'entreprise :<br/><b>{normalize_text(company_name)}</b>",
                    st["h_title"]
                ),
                Paragraph(f"Généré le<br/>{date_str}", st["h_date"]),
            ]],
            colWidths=[pw * 0.12, pw * 0.64, pw * 0.24]
        )
        header.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), SKY_DARK),
            ("TOPPADDING",    (0, 0), (-1, -1), 22),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 22),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("BOX",           (0, 0), (-1, -1), 0, colors.white),
        ]))
        story.append(header)
        
        # ═══════════════════════════════════════════════════════════════════
        # PAGE 1 - SCORE
        # ═══════════════════════════════════════════════════════════════════
        story.append(Spacer(1, 0.8*cm))
        story.append(Paragraph("Score global :", st["score_label"]))
        story.append(Paragraph(f"<b>{score} / 100</b>", st["score"]))
        story.append(Spacer(1, 1.2*cm))
        
        # ═══════════════════════════════════════════════════════════════════
        # PAGE 1 - ANALYSE SWOT
        # ═══════════════════════════════════════════════════════════════════
        story.append(section_bar("ANALYSE SWOT", st, pw))
        story.append(Spacer(1, 0.25*cm))
        
        # Extraire les données SWOT
        points_forts = swot_analysis.get("points_forts", [])
        points_faibles = swot_analysis.get("points_faibles", [])
        opportunites = swot_analysis.get("opportunites", [])
        menaces = swot_analysis.get("menaces", [])
        
        story.append(swot_block("Points forts :", points_forts, st, pw))
        story.append(Spacer(1, 0.25*cm))
        story.append(swot_block("Points à améliorer :", points_faibles, st, pw))
        story.append(Spacer(1, 0.25*cm))
        story.append(swot_block("Opportunités :", opportunites, st, pw))
        story.append(Spacer(1, 0.25*cm))
        story.append(swot_block("Menaces :", menaces, st, pw))
        
        # ═══════════════════════════════════════════════════════════════════
        # PAGE 2 - PLAN D'ACTION
        # ═══════════════════════════════════════════════════════════════════
        story.append(PageBreak())
        
        story.append(section_bar("PLAN D'ACTION STRATÉGIQUE", st, pw))
        story.append(Spacer(1, 0.3*cm))
        
        # Extraire les données du plan
        court_terme = action_plan.get("court_terme", [])
        moyen_terme = action_plan.get("moyen_terme", [])
        long_terme = action_plan.get("long_terme", [])
        
        story.extend(plan_block("Actions immédiates (0-3 mois)", court_terme, st, pw, SKY_MED))
        story.extend(plan_block("Actions à moyen terme (3-6 mois)", moyen_terme, st, pw, SKY_LIGHT))
        story.extend(plan_block("Actions à long terme (6-12 mois)", long_terme, st, pw, SKY_XLIGHT))
        
        # ═══════════════════════════════════════════════════════════════════
        # PIED DE PAGE
        # ═══════════════════════════════════════════════════════════════════
        story.append(Spacer(1, 1*cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=SKY_LIGHT))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(
            f"Document généré par Localis AI - {datetime.now().year}",
            st["footer"]
        ))
        
        # Génération du PDF
        doc.build(story)
        
        logger.info(f"✅ PDF généré: {fp}")
        
        # Retourner les données parsées
        return {
            'success': True,
            'filepath': str(fp),
            'filename': fp.name,
            'swot_parsed': {
                'forces': [item.get('titre', str(item))[:50] for item in points_forts],
                'faiblesses': [item.get('titre', str(item))[:50] for item in points_faibles],
                'opportunites': [item.get('titre', str(item))[:50] for item in opportunites],
                'menaces': [item.get('titre', str(item))[:50] for item in menaces]
            },
            'plan_parsed': {
                'court_terme': [item.get('titre', item.get('action', str(item)))[:50] for item in court_terme],
                'moyen_terme': [item.get('titre', item.get('action', str(item)))[:50] for item in moyen_terme],
                'long_terme': [item.get('titre', item.get('action', str(item)))[:50] for item in long_terme]
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur génération PDF: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def generate_pdf_from_rapport(rapport: dict, output_path: str = None) -> dict:
    """Génère un PDF à partir d'un rapport complet du diagnostic_engine"""
    company_name = rapport.get("company_name", "Entreprise")
    score = rapport.get("rating", {}).get("score", 50)
    swot_analysis = rapport.get("swot_analysis", {})
    action_plan = rapport.get("action_plan", {})
    
    return generate_pdf(company_name, score, swot_analysis, action_plan, output_path)


# ── TEST AVEC LA NOUVELLE STRUCTURE ──────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  GÉNÉRATEUR PDF - TEST INTÉGRATION")
    print("="*60 + "\n")
    
    # Données de test avec la structure du diagnostic_engine
    test_rapport = {
        "company_name": "PharmAstuces Djerba",
        "rating": {"score": 72, "justification": "Bonne présence locale mais potentiel d'amélioration web"},
        "swot_analysis": {
            "points_forts": [
                {"titre": "Présence active sur Facebook", "description": "Interaction directe avec la clientèle locale"},
                {"titre": "Nom de marque mémorisable", "description": "'PharmAstuces' évoque la santé et les conseils"},
                {"titre": "Emplacement stratégique", "description": "Zone touristique de Djerba"}
            ],
            "points_faibles": [
                {"titre": "Absence de site web", "description": "Limite le référencement et la crédibilité"},
                {"titre": "Peu d'avis Google", "description": "Seulement 2 avis, réduit la confiance"},
                {"titre": "Dépendance à Facebook", "description": "Risque de perte de visibilité"}
            ],
            "opportunites": [
                {"titre": "Création Google My Business", "description": "Capter les recherches locales"},
                {"titre": "Développement site web", "description": "Améliorer le SEO et la crédibilité"},
                {"titre": "Marché touristique", "description": "Croissance du tourisme à Djerba"}
            ],
            "menaces": [
                {"titre": "Concurrence mieux référencée", "description": "Perte de parts de marché"},
                {"titre": "Évolution des algorithmes", "description": "Défavorise les profils incomplets"}
            ]
        },
        "action_plan": {
            "court_terme": [
                {"titre": "Optimiser Google My Business", "description": "Remplir toutes les informations (horaires, photos, services)"},
                {"titre": "Rechercher mots-clés locaux", "description": "Identifier les termes recherchés à Djerba"},
                {"titre": "Maintenir engagement Facebook", "description": "Publier des conseils santé régulièrement"}
            ],
            "moyen_terme": [
                {"titre": "Créer un site web", "description": "Nom de domaine propre avec optimisation SEO locale"},
                {"titre": "Développer pages services", "description": "Contenu ciblé avec mots-clés locaux"},
                {"titre": "Blog thématique", "description": "Articles sur la santé pour la communauté"}
            ],
            "long_terme": [
                {"titre": "Schema Markup LocalBusiness", "description": "Balises pour meilleur référencement"},
                {"titre": "Obtenir backlinks qualité", "description": "Annuaires régionaux et blogs locaux"},
                {"titre": "Analyse concurrentielle", "description": "Surveiller stratégies des concurrents"}
            ]
        }
    }
    
    # Générer le PDF
    result = generate_pdf_from_rapport(test_rapport)
    
    if result['success']:
        print(f"✅ PDF généré avec succès!")
        print(f"📁 Emplacement: {result['filepath']}")
        print(f"📊 SWOT: {len(result['swot_parsed']['forces'])} forces, {len(result['swot_parsed']['faiblesses'])} faiblesses")
        print(f"📈 Opportunités: {len(result['swot_parsed']['opportunites'])}, Menaces: {len(result['swot_parsed']['menaces'])}")
        print(f"🎯 Actions: {len(result['plan_parsed']['court_terme'])} CT, {len(result['plan_parsed']['moyen_terme'])} MT, {len(result['plan_parsed']['long_terme'])} LT")
    else:
        print(f"❌ Erreur: {result['error']}")
    
    print("\n" + "="*60)