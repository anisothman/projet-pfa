"""
DiagnoReport - Generateur de rapports PDF professionnel
Responsable: Maram
Sprint 3 - Generation PDF avec rating, SWOT tableau points noirs
"""

import os #gérer les fichiers et dossiers (créer, chemins…)
import re #expressions régulières
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

DARK_BLUE   = colors.HexColor("#1B2A4A")
MEDIUM_BLUE = colors.HexColor("#2C5F8A")
GREEN       = colors.HexColor("#1E7E4A")
GRAY        = colors.HexColor("#5A5A5A")
LIGHT_GRAY  = colors.HexColor("#F4F4F4")
SEPARATOR   = colors.HexColor("#CCCCCC")
WHITE       = colors.white
BLACK       = colors.black

SWOT_COLORS = {
    "Forces":       (colors.HexColor("#189D56"), colors.HexColor("#D4EDDA")),
    "Faiblesses":   (colors.HexColor("#C0392B"), colors.HexColor("#FADBD8")),
    "Opportunites": (colors.HexColor("#2D7AB1"), colors.HexColor("#D6EAF8")),
    "Menaces":      (colors.HexColor("#EF8F3B"), colors.HexColor("#FDEBD0")),
}

def build_styles():
    return {
        "company": ParagraphStyle("company", fontName="Helvetica-Bold", fontSize=16, textColor=WHITE, alignment=TA_CENTER),
        "subtitle_header": ParagraphStyle("subtitle_header", fontName="Helvetica", fontSize=11, textColor=colors.HexColor("#C8DCF0"), alignment=TA_CENTER),
        "date_header": ParagraphStyle("date_header", fontName="Helvetica-Oblique", fontSize=9, textColor=colors.HexColor("#A0BFDB"), alignment=TA_CENTER),
        "section_title": ParagraphStyle("section_title", fontName="Helvetica-Bold", fontSize=13, textColor=WHITE, leftIndent=6),
        "rating_score": ParagraphStyle("rating_score", fontName="Helvetica-Bold",leading=32, fontSize=28, textColor=DARK_BLUE, alignment=TA_CENTER),
        "rating_label": ParagraphStyle("rating_label", fontName="Helvetica", fontSize=10, textColor=GRAY, alignment=TA_CENTER),
        "rating_justif": ParagraphStyle("rating_justif", fontName="Helvetica-Oblique", fontSize=9, textColor=GRAY, alignment=TA_CENTER),
        "swot_header": ParagraphStyle("swot_header", fontName="Helvetica-Bold", fontSize=11, textColor=WHITE, alignment=TA_CENTER),
        "swot_point": ParagraphStyle("swot_point", fontName="Helvetica", fontSize=9, textColor=BLACK, leading=14, spaceAfter=3),
        "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=10, textColor=colors.HexColor("#2C2C2C"), leftIndent=14, spaceAfter=5, leading=15),
        "meta_label": ParagraphStyle("meta_label", fontName="Helvetica-Bold", fontSize=9, textColor=DARK_BLUE),
        "meta_value": ParagraphStyle("meta_value", fontName="Helvetica", fontSize=9, textColor=GRAY),
        "footer_style": ParagraphStyle("footer_style", fontName="Helvetica-Oblique", fontSize=8, textColor=GRAY, alignment=TA_CENTER),
    }

def format_date(iso_date):
    try:
        return datetime.fromisoformat(iso_date).strftime("%d/%m/%Y  %H:%M")
    except:
        return iso_date

def rating_color(score):
    if score >= 75: return colors.HexColor("#1E7E4A")
    elif score >= 50: return colors.HexColor("#E67E22")
    else: return colors.HexColor("#C0392B")

def parse_swot(text):
    result = {k: [] for k in SWOT_COLORS}
    aliases = {
        "Forces":       ["forces","force","strengths","points forts"],
        "Faiblesses":   ["faiblesses","faiblesse","weaknesses","points faibles"],
        "Opportunites": ["opportunites","opportunite","opportunities"],
        "Menaces":      ["menaces","menace","threats"],
    }
    current = None
    for line in text.splitlines():
        s = line.strip().lower().rstrip(":")
        matched = False
        for key, terms in aliases.items():
            if any(t in s for t in terms):
                current = key; matched = True; break
        if not matched and current and line.strip():
            clean = re.sub(r"^[\*\-\u2022\d\.\s]+", "", line).strip()
            if clean: result[current].append(clean)
    return result

def parse_action(text):
    lines = []
    for line in text.splitlines():
        clean = re.sub(r"^[\*\-\u2022\d\.\s]+", "", line).strip()
        if clean and len(clean) > 5: lines.append(clean)
    return lines

def build_header(company, generated_at, styles):
    pw = A4[0] - 3*cm
    elems = []
    for data, tp, bp in [
        ([[Paragraph(f"Report  \u2014  {company.upper()}", styles["company"])]], 18, 4),
        ([[Paragraph("Analyse SWOT  |  Plan d'Action  |  Rating Global", styles["subtitle_header"])]], 4, 4),
        ([[Paragraph(f"Genere le : {format_date(generated_at)}", styles["date_header"])]], 4, 14),
    ]:
        t = Table(data, colWidths=[pw])
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),DARK_BLUE),
            ("TOPPADDING",(0,0),(-1,-1),tp),
            ("BOTTOMPADDING",(0,0),(-1,-1),bp),
            ("LEFTPADDING",(0,0),(-1,-1),10),
            ("RIGHTPADDING",(0,0),(-1,-1),10),
        ]))
        elems.append(t)
    elems.append(Spacer(1,0.4*cm))
    return elems

def build_section_title(title, color, styles):
    pw = A4[0] - 3*cm
    t = Table([[Paragraph(f"  {title}", styles["section_title"])]], colWidths=[pw])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),color),
        ("TOPPADDING",(0,0),(-1,-1),7),
        ("BOTTOMPADDING",(0,0),(-1,-1),7),
        ("LEFTPADDING",(0,0),(-1,-1),8),
    ]))
    return [Spacer(1,0.3*cm), t, Spacer(1,0.25*cm)]

def build_rating(rating, styles):
    score  = rating.get("score", 60)
    justif = rating.get("justification", "")
    bc     = rating_color(score)
    pw     = A4[0] - 3*cm
    elems  = []

    # Note en grand
    t = Table(
    [[Paragraph(f"{score}/100", styles["rating_score"])]],
    colWidths=[pw],
    rowHeights=[60]  
)
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),LIGHT_GRAY),
        ("TOPPADDING",(0,0),(-1,-1),14),
        ("BOTTOMPADDING",(0,0),(-1,-1),2),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
    ]))
    elems.append(t)

    # Label
    t2 = Table([[Paragraph("Note Globale de Performance", styles["rating_label"])]], colWidths=[pw])
    t2.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),LIGHT_GRAY),
        ("TOPPADDING",(0,0),(-1,-1),0),
        ("BOTTOMPADDING",(0,0),(-1,-1),10),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
    ]))
    elems.append(t2)

    # Barre de progression
    filled = pw * score / 100
    empty  = pw - filled
    bar = Table([[""," "]], colWidths=[filled, empty], rowHeights=[16])
    bar.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,0),bc),
        ("BACKGROUND",(1,0),(1,0),colors.HexColor("#E0E0E0")),
        ("TOPPADDING",(0,0),(-1,-1),0),
        ("BOTTOMPADDING",(0,0),(-1,-1),0),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0),
    ]))
    elems.append(bar)
    elems.append(Spacer(1,0.15*cm))

    # Pourcentage
    t3 = Table([[Paragraph(f"{score}%", styles["rating_label"])]], colWidths=[pw])
    t3.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"RIGHT"),("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    elems.append(t3)

    # Justification
    if justif:
        t4 = Table([[Paragraph(f'"{justif}"', styles["rating_justif"])]], colWidths=[pw])
        t4.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),LIGHT_GRAY),
            ("TOPPADDING",(0,0),(-1,-1),6),
            ("BOTTOMPADDING",(0,0),(-1,-1),10),
            ("LEFTPADDING",(0,0),(-1,-1),12),
            ("RIGHTPADDING",(0,0),(-1,-1),12),
            ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ]))
        elems.append(t4)

    elems.append(Spacer(1,0.3*cm))
    return elems

def build_swot_table(swot_text, styles):
    swot  = parse_swot(swot_text)
    col_w = (A4[0] - 3*cm) / 2

    def make_cell(key):
        hc, bg = SWOT_COLORS[key]
        items  = swot.get(key, ["Aucune donnee disponible"])
        rows   = [[Paragraph(key, styles["swot_header"])]]
        for item in items:
            rows.append([Paragraph(f"\u25CF  {item}", styles["swot_point"])])
        ct = Table(rows, colWidths=[col_w - 0.4*cm])
        ct.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(0,0), hc),
            ("BACKGROUND",(0,1),(-1,-1), bg),
            ("TOPPADDING",(0,0),(-1,-1),6),
            ("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",(0,0),(-1,-1),8),
            ("RIGHTPADDING",(0,0),(-1,-1),8),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
        ]))
        return ct

    data = [
        [make_cell("Forces"),       make_cell("Faiblesses")],
        [make_cell("Opportunites"), make_cell("Menaces")],
    ]
    outer = Table(data, colWidths=[col_w, col_w])
    outer.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),1,WHITE),
        ("BOX",(0,0),(-1,-1),1,SEPARATOR),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("LEFTPADDING",(0,0),(-1,-1),4),
        ("RIGHTPADDING",(0,0),(-1,-1),4),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
    ]))
    return [outer, Spacer(1,0.3*cm)]

def build_action_plan(action_text, styles):
    items = parse_action(action_text)
    elems = []
    for item in items:
        elems.append(Paragraph(f"\u2014  {item}", styles["bullet"]))
    if not items:
        elems.append(Paragraph("Aucun plan d'action disponible.", styles["bullet"]))
    elems.append(Spacer(1,0.3*cm))
    return elems

def build_metadata(metadata, styles):
    infos = [
        ("Source des donnees",   metadata.get("data_source","inconnue")),
        ("Resultats analyses",   str(metadata.get("data_results_count",0))),
        ("Version moteur",       metadata.get("engine_version","1.0")),
        ("Modele SWOT",          metadata.get("models_used",{}).get("swot_model","gemini-2.0-flash")),
        ("Modele Plan d'action", metadata.get("models_used",{}).get("action_plan_model","gemini-2.0-flash")),
    ]
    col_w = A4[0] - 3*cm
    data  = [[Paragraph(l, styles["meta_label"]), Paragraph(v, styles["meta_value"])] for l,v in infos]
    t = Table(data, colWidths=[col_w*0.38, col_w*0.62])
    t.setStyle(TableStyle([
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[LIGHT_GRAY,WHITE]),
        ("GRID",(0,0),(-1,-1),0.3,SEPARATOR),
        ("TOPPADDING",(0,0),(-1,-1),5),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),8),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    return [t, Spacer(1,0.4*cm)]

def export_pdf(rapport, output_dir=None):
    if output_dir is None: output_dir = REPORTS_DIR
    os.makedirs(output_dir, exist_ok=True)

    company      = rapport.get("company_name","unknown")
    generated_at = rapport.get("generated_at", datetime.now().isoformat())
    timestamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename     = os.path.join(output_dir, f"diagnostic_{company}_{timestamp}.pdf")

    doc = SimpleDocTemplate(filename, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.2*cm, bottomMargin=1.8*cm,
        title=f"Diagnostic {company}", author="DiagnoReport - LocalGuide AI")

    styles = build_styles()
    elems  = []

    elems += build_header(company, generated_at, styles)
    elems += build_section_title("Rating Global  \u2014  Performance Strategique", DARK_BLUE, styles)
    elems += build_rating(rapport.get("rating", {"score":60,"justification":""}), styles)
    elems.append(HRFlowable(width="100%", thickness=0.5, color=SEPARATOR))
    elems.append(Spacer(1,0.2*cm))
    elems += build_section_title("Analyse SWOT", DARK_BLUE, styles)
    elems += build_swot_table(rapport.get("swot_analysis",""), styles)
    elems.append(HRFlowable(width="100%", thickness=0.5, color=SEPARATOR))
    elems.append(Spacer(1,0.2*cm))
    elems += build_section_title("Plan d'Action Strategique", DARK_BLUE, styles)
    elems += build_action_plan(rapport.get("action_plan",""), styles)
    elems.append(HRFlowable(width="100%", thickness=0.5, color=SEPARATOR))
    elems.append(Spacer(1,0.2*cm))
    elems += build_section_title("Informations Techniques", GRAY, styles)
    elems += build_metadata(rapport.get("metadata",{}), styles)
    elems += [
        HRFlowable(width="100%", thickness=0.5, color=SEPARATOR),
        Spacer(1,0.2*cm),
        Paragraph(f"Report  |  {company.upper()}  |  Genere par LocalGuide AI", styles["footer_style"]),
    ]

    doc.build(elems)
    print(f"PDF genere : {filename}")
    return filename

def export_all_pdf(rapports, output_dir=None):
    print("\n" + "="*60)
    print("DIAGNO REPORT - GENERATION DES PDFs")
    print("="*60)
    success = 0
    for rapport in rapports:
        if "error" not in rapport:
            if export_pdf(rapport, output_dir): success += 1
        else:
            print(f"Rapport ignore (erreur) : {rapport.get('company_name')}")
    print(f"\nPDFs generes : {success}/{len(rapports)}")
    print("="*60)
if __name__ == "__main__":
    from datetime import datetime

    rapport_test = {
        "company_name": "Apple",
        "generated_at": datetime.now().isoformat(),

        "rating": {
            "score": 50,
            "justification": "Performance moyenne avec opportunités d'amélioration."
        },

        "swot_analysis": """
        Forces:
        - Marque forte
        - Innovation continue

        Faiblesses:
        - Prix élevés
        - Dépendance iPhone

        Opportunites:
        - Marché IA
        - Expansion services

        Menaces:
        - Concurrence Samsung
        - Régulation gouvernementale
        """,

        "action_plan": """
        - Investir dans l'intelligence artificielle
        - Réduire les coûts de production
        - Diversifier les produits
        """,

        "metadata": {
            "data_source": "Test manuel",
            "data_results_count": 10,
            "engine_version": "1.0",
            "models_used": {
                "swot_model": "test-model",
                "action_plan_model": "test-model"
            }
        }
    }

    export_pdf(rapport_test)