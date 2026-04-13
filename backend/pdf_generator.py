"""
pdf_generator.py — Version SANS TABLEAUX VISIBLES
Sprint 3 - Generation PDF professionnelle
"""

import re
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle, PageBreak
)

REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Palette de couleurs
SKY_DARK = colors.HexColor("#0077A8")
SKY_MED = colors.HexColor("#00B4D8")
SKY_LIGHT = colors.HexColor("#48CAE4")
SKY_XLIGHT = colors.HexColor("#ADE8F4")
SKY_PALE = colors.HexColor("#E8F8FC")
WHITE = colors.white
BLACK = colors.HexColor("#111111")
GRAY = colors.HexColor("#666666")
ACCENT = colors.HexColor("#FF6600")

print("=" * 60)
print("GENERATEUR PDF - VERSION SANS TABLEAUX")
print("=" * 60)


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = str(text)
    replacements = {'"': '"', '"': '"', ''': "'", ''': "'", '«': '"', '»': '"', '–': '-', '—': '-'}
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    text = re.sub(r'[^\x20-\x7E\u00C0-\u00FF\u0100-\u017F]', '', text)
    return text.strip()


def get_styles():
    b = getSampleStyleSheet()
    return {
        "h_title": ParagraphStyle("hTitle", parent=b["Normal"], fontSize=13, textColor=WHITE, fontName="Helvetica-Bold", leading=19, alignment=TA_CENTER),
        "h_date": ParagraphStyle("hDate", parent=b["Normal"], fontSize=8, textColor=colors.HexColor("#CCF0F8"), leading=12, alignment=TA_RIGHT),
        "score_label": ParagraphStyle("scoreLabel", parent=b["Normal"], fontSize=11, textColor=GRAY, fontName="Helvetica-Bold", leading=16, alignment=TA_CENTER, spaceAfter=6),
        "score": ParagraphStyle("score", parent=b["Normal"], fontSize=26, textColor=ACCENT, fontName="Helvetica-Bold", leading=32, alignment=TA_CENTER),
        "sec_bar": ParagraphStyle("secBar", parent=b["Normal"], fontSize=12, textColor=WHITE, fontName="Helvetica-Bold", leading=16, alignment=TA_LEFT),
        "swot_cat": ParagraphStyle("swotCat", parent=b["Normal"], fontSize=11, textColor=BLACK, fontName="Helvetica-Bold", leading=18, spaceBefore=12, spaceAfter=6),
        "swot_item": ParagraphStyle("swotItem", parent=b["Normal"], fontSize=10, textColor=BLACK, leading=15, leftIndent=15, spaceAfter=4),
        "plan_sub": ParagraphStyle("planSub", parent=b["Normal"], fontSize=11, textColor=WHITE, fontName="Helvetica-Bold", leading=16, alignment=TA_LEFT),
        "plan_item": ParagraphStyle("planItem", parent=b["Normal"], fontSize=10, textColor=BLACK, leading=15, leftIndent=15, spaceAfter=4),
        "footer": ParagraphStyle("footer", parent=b["Normal"], fontSize=8, textColor=GRAY, alignment=TA_CENTER),
    }


def section_bar(title, st, pw, color=SKY_DARK):
    t = Table([[Paragraph(f"  {title}", st["sec_bar"])]], colWidths=[pw])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 0, colors.white),
    ]))
    return t


def swot_block(label, items, st, pw):
    if not items:
        items = [{"titre": "Aucune information disponible"}]
    
    story = []
    story.append(Paragraph(f"<b>{label}</b>", st["swot_cat"]))
    
    for item in items:
        if isinstance(item, dict):
            titre = normalize_text(item.get("titre", ""))
        else:
            titre = normalize_text(str(item))
        story.append(Paragraph(f"•   {titre}", st["swot_item"]))
    
    return story


def plan_block(subtitle, items, st, pw, color):
    story = []
    
    sub_table = Table([[Paragraph(f"  {subtitle}", st["plan_sub"])]], colWidths=[pw])
    sub_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("BOX", (0, 0), (-1, -1), 0, colors.white),
    ]))
    story.append(sub_table)
    story.append(Spacer(1, 0.1*cm))
    
    if items:
        for i, item in enumerate(items, 1):
            if isinstance(item, dict):
                titre = normalize_text(item.get("titre", item.get("action", "")))
            else:
                titre = normalize_text(str(item))
            story.append(Paragraph(f"{i}.   {titre}", st["plan_item"]))
    else:
        story.append(Paragraph("Aucune action définie", st["plan_item"]))
    
    story.append(Spacer(1, 0.3*cm))
    return story


def generate_pdf(company_name, score, swot_analysis, action_plan, output_path=None):
    try:
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', company_name)[:30]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fp = REPORTS_DIR / f"diagnostic_{safe_name}_{timestamp}.pdf"
        
        doc = SimpleDocTemplate(str(fp), pagesize=A4, topMargin=1.5*cm, bottomMargin=1.8*cm, leftMargin=1.5*cm, rightMargin=1.5*cm)
        st = get_styles()
        pw = A4[0] - 3*cm
        date_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
        story = []
        
        # En-tête
        header = Table([["", f"Rapport Diagnostic de l'entreprise :<br/><b>{normalize_text(company_name)}</b>", f"Généré le<br/>{date_str}"]], 
                       colWidths=[pw*0.12, pw*0.64, pw*0.24])
        header.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), SKY_DARK), ("TOPPADDING", (0, 0), (-1, -1), 22), ("BOTTOMPADDING", (0, 0), (-1, -1), 22), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        story.append(header)
        
        # Score
        story.append(Spacer(1, 0.8*cm))
        story.append(Paragraph("Score global :", st["score_label"]))
        story.append(Paragraph(f"<b>{score} / 100</b>", st["score"]))
        story.append(Spacer(1, 1.2*cm))
        
        # SWOT
        story.append(section_bar("ANALYSE SWOT", st, pw))
        story.append(Spacer(1, 0.25*cm))
        
        story.extend(swot_block("Points forts :", swot_analysis.get("points_forts", []), st, pw))
        story.extend(swot_block("Points à améliorer :", swot_analysis.get("points_faibles", []), st, pw))
        story.extend(swot_block("Opportunités :", swot_analysis.get("opportunites", []), st, pw))
        story.extend(swot_block("Menaces :", swot_analysis.get("menaces", []), st, pw))
        
        # Plan d'action (page 2)
        story.append(PageBreak())
        story.append(section_bar("PLAN D'ACTION STRATÉGIQUE", st, pw))
        story.append(Spacer(1, 0.3*cm))
        
        story.extend(plan_block("Actions immédiates (0-3 mois)", action_plan.get("court_terme", []), st, pw, SKY_MED))
        story.extend(plan_block("Actions à moyen terme (3-6 mois)", action_plan.get("moyen_terme", []), st, pw, SKY_LIGHT))
        story.extend(plan_block("Actions à long terme (6-12 mois)", action_plan.get("long_terme", []), st, pw, SKY_XLIGHT))
        
        # Pied de page
        story.append(Spacer(1, 1*cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=SKY_LIGHT))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(f"Document généré par Localis AI - {datetime.now().year}", st["footer"]))
        
        doc.build(story)
        
        print(f"✅ PDF généré: {fp}")
        return {"success": True, "filepath": str(fp), "filename": fp.name}
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    test_swot = {
        "points_forts": [{"titre": "Équipe technique expérimentée"}, {"titre": "Technologie innovante"}],
        "points_faibles": [{"titre": "Budget marketing limité"}],
        "opportunites": [{"titre": "Expansion internationale"}],
        "menaces": [{"titre": "Concurrence agressive"}]
    }
    test_plan = {
        "court_terme": [{"titre": "Optimiser le SEO"}, {"titre": "Lancer campagne"}],
        "moyen_terme": [{"titre": "Développer API"}],
        "long_terme": [{"titre": "Lever des fonds"}]
    }
    result = generate_pdf("MaSuperEntreprise", 65, test_swot, test_plan)
    print(f"Résultat: {result}")
