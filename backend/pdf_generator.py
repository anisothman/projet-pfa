"""
DiagnoReport — pdf_generator.py
Responsable : Maram
Sprint 3 — Generation PDF professionnelle avec parsing automatique
"""

import re
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)

# ===== CHEMINS =====
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ===== COULEURS =====
DARK_BLUE = colors.HexColor("#1B2A4A")
MEDIUM_BLUE = colors.HexColor("#2C5F8A")
GREEN = colors.HexColor("#1E7E4A")
RED = colors.HexColor("#C0392B")
ORANGE = colors.HexColor("#E67E22")
GRAY = colors.HexColor("#5A5A5A")
LIGHT_GRAY = colors.HexColor("#F4F4F4")
WHITE = colors.white

# ===== CONFIGURATION PARSING =====
SWOT_KEYWORDS = {
    "forces": ["forces", "strengths", "points forts", "atouts"],
    "faiblesses": ["faiblesses", "weaknesses", "points faibles"],
    "opportunites": ["opportunites", "opportunities", "opportunités"],
    "menaces": ["menaces", "threats", "risques"]
}

PLAN_KEYWORDS = {
    "court_terme": ["court terme", "court-terme", "0-3 mois", "0-6 mois", "immediat", "court therme"],
    "moyen_terme": ["moyen terme", "moyen-terme", "3-6 mois", "6-12 mois", "moyen therme"],
    "long_terme": ["long terme", "long-terme", "12+ mois", "18+ mois", "long therme"]
}

# ===== STYLES =====
def get_styles():
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title", parent=styles["Heading1"],
            fontSize=18, textColor=WHITE, alignment=TA_CENTER, spaceAfter=20
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", parent=styles["Normal"],
            fontSize=10, textColor=colors.HexColor("#C8DCF0"), alignment=TA_CENTER
        ),
        "section": ParagraphStyle(
            "Section", parent=styles["Heading2"],
            fontSize=14, textColor=WHITE, leftIndent=8, spaceBefore=15, spaceAfter=10
        ),
        "swot_header": ParagraphStyle(
            "SwotHeader", parent=styles["Heading3"],
            fontSize=11, textColor=WHITE, alignment=TA_CENTER
        ),
        "swot_item": ParagraphStyle(
            "SwotItem", parent=styles["Normal"],
            fontSize=9, leading=14, spaceAfter=4, leftIndent=8
        ),
        "plan_header": ParagraphStyle(
            "PlanHeader", parent=styles["Heading3"],
            fontSize=11, textColor=WHITE, leftIndent=6
        ),
        "plan_item": ParagraphStyle(
            "PlanItem", parent=styles["Normal"],
            fontSize=10, leading=15, spaceAfter=6, leftIndent=14
        ),
        "normal": styles["Normal"],
        "footer": ParagraphStyle(
            "Footer", parent=styles["Normal"],
            fontSize=8, textColor=GRAY, alignment=TA_CENTER
        ),
    }

# ===== FONCTIONS DE PARSING =====
def parse_swot(text):
    """Parse le texte SWOT en 4 categories"""
    result = {"forces": [], "faiblesses": [], "opportunites": [], "menaces": []}
    current_category = None
    text_lower = text.lower()
    
    # D'abord, essayer de trouver les sections
    lines = text.split('\n')
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        # Verifier si la ligne est une categorie
        line_lower = line_clean.lower()
        category_found = None
        
        for cat, keywords in SWOT_KEYWORDS.items():
            if any(keyword in line_lower for keyword in keywords):
                category_found = cat
                break
        
        if category_found:
            current_category = category_found
        elif current_category and line_clean:
            # Nettoyer la ligne (enlever les puces)
            clean_item = re.sub(r'^[\*\-\•\d\.\s]+', '', line_clean).strip()
            if clean_item and len(clean_item) > 2:
                result[current_category].append(clean_item)
    
    # Si aucun parsing n'a fonctionné, mettre tout dans forces
    if not any(result.values()):
        result["forces"] = [text[:500]]
    
    return result

def parse_plan(text):
    """Parse le texte du plan d'action en 3 horizons"""
    result = {"court_terme": [], "moyen_terme": [], "long_terme": []}
    current_horizon = "court_terme"
    text_lower = text.lower()
    
    lines = text.split('\n')
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        line_lower = line_clean.lower()
        horizon_found = None
        
        for horizon, keywords in PLAN_KEYWORDS.items():
            if any(keyword in line_lower for keyword in keywords):
                horizon_found = horizon
                break
        
        if horizon_found:
            current_horizon = horizon_found
        elif line_clean:
            # Nettoyer la ligne
            clean_item = re.sub(r'^[\*\-\•\d\.\s]+', '', line_clean).strip()
            if clean_item and len(clean_item) > 3:
                result[current_horizon].append(clean_item)
    
    return result

# ===== CONSTRUCTION DU PDF =====
def build_swot_table(swot_data, styles, page_width):
    """Construit le tableau SWOT 2x2"""
    col_width = page_width / 2 - 0.4 * cm
    
    def make_swot_cell(items, title, bg_color, text_color):
        # En-tete
        header = Paragraph(f"<b>{title}</b>", styles["swot_header"])
        header_table = Table([[header]], colWidths=[col_width - 0.4 * cm])
        header_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), text_color),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        
        # Contenu
        content = []
        if not items:
            content.append(Paragraph("Aucune donnee", styles["swot_item"]))
        else:
            for item in items[:8]:  # Max 8 items
                content.append(Paragraph(f"• {item}", styles["swot_item"]))
        
        content_table = Table([[c] for c in content], colWidths=[col_width - 0.4 * cm])
        content_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg_color),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        
        # Assembler
        cell = Table([[header_table], [content_table]], colWidths=[col_width - 0.4 * cm])
        cell.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        return cell
    
    # Couleurs par categorie
    colors_cfg = {
        "forces": (GREEN, colors.HexColor("#D4EDDA")),
        "faiblesses": (RED, colors.HexColor("#FADBD8")),
        "opportunites": (MEDIUM_BLUE, colors.HexColor("#D6EAF8")),
        "menaces": (ORANGE, colors.HexColor("#FDEBD0")),
    }
    
    titles = {
        "forces": "FORCES",
        "faiblesses": "FAIBLESSES",
        "opportunites": "OPPORTUNITES",
        "menaces": "MENACES",
    }
    
    top_left = make_swot_cell(
        swot_data.get("forces", []),
        titles["forces"],
        colors_cfg["forces"][1],
        colors_cfg["forces"][0]
    )
    top_right = make_swot_cell(
        swot_data.get("faiblesses", []),
        titles["faiblesses"],
        colors_cfg["faiblesses"][1],
        colors_cfg["faiblesses"][0]
    )
    bottom_left = make_swot_cell(
        swot_data.get("opportunites", []),
        titles["opportunites"],
        colors_cfg["opportunites"][1],
        colors_cfg["opportunites"][0]
    )
    bottom_right = make_swot_cell(
        swot_data.get("menaces", []),
        titles["menaces"],
        colors_cfg["menaces"][1],
        colors_cfg["menaces"][0]
    )
    
    table_data = [
        [top_left, top_right],
        [bottom_left, bottom_right]
    ]
    
    outer_table = Table(table_data, colWidths=[col_width, col_width])
    outer_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, WHITE),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    
    return outer_table

def build_plan_section(plan_data, styles, page_width):
    """Construit la section plan d'action"""
    elements = []
    
    horizons = [
        ("court_terme", "COURT TERME (0-6 mois)", GREEN),
        ("moyen_terme", "MOYEN TERME (6-18 mois)", MEDIUM_BLUE),
        ("long_terme", "LONG TERME (18+ mois)", ORANGE),
    ]
    
    for key, title, color in horizons:
        items = plan_data.get(key, [])
        
        # En-tete
        header = Paragraph(f"  {title}", styles["plan_header"])
        header_table = Table([[header]], colWidths=[page_width])
        header_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), color),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 0.1 * cm))
        
        if not items:
            elements.append(Paragraph("Aucune action definie", styles["plan_item"]))
        else:
            for item in items[:10]:
                elements.append(Paragraph(f"• {item}", styles["plan_item"]))
        
        elements.append(Spacer(1, 0.3 * cm))
    
    return elements

# ===== FONCTION PRINCIPALE =====
def generate_pdf(company_name, diagnostic, plan_action, rating=None):
    """
    Genere un PDF professionnel avec SWOT et Plan d'action structures
    
    Args:
        company_name (str): Nom de l'entreprise
        diagnostic (str): Texte brut du diagnostic (sera parse en SWOT)
        plan_action (str): Texte brut du plan d'action (sera parse en horizons)
        rating (dict, optional): Score et justification
    
    Returns:
        dict: {"success": bool, "filepath": str, "error": str}
    """
    try:
        # Parser les textes
        swot_data = parse_swot(diagnostic)
        plan_data = parse_plan(plan_action)
        
        # Preparer le nom du fichier
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', company_name)[:30]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"diagnostic_{safe_name}_{timestamp}.pdf"
        filepath = REPORTS_DIR / filename
        
        # Creer le document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            topMargin=1.5*cm,
            bottomMargin=1.8*cm,
            leftMargin=1.5*cm,
            rightMargin=1.5*cm
        )
        
        styles = get_styles()
        page_width = A4[0] - 3*cm
        story = []
        
        # En-tete
        title_table = Table([[Paragraph(f"RAPPORT D'ANALYSE", styles["title"])]], colWidths=[page_width])
        title_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), DARK_BLUE),
            ("TOPPADDING", (0, 0), (-1, -1), 20),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(title_table)
        
        company_table = Table([[Paragraph(company_name.upper(), styles["title"])]], colWidths=[page_width])
        company_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), DARK_BLUE),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(company_table)
        
        date_str = f"Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')}"
        date_table = Table([[Paragraph(date_str, styles["subtitle"])]], colWidths=[page_width])
        date_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), DARK_BLUE),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
        ]))
        story.append(date_table)
        
        story.append(Spacer(1, 0.5*cm))
        
        # Section SWOT
        swot_header = Table([[Paragraph("ANALYSE SWOT", styles["section"])]], colWidths=[page_width])
        swot_header.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), MEDIUM_BLUE),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(swot_header)
        story.append(Spacer(1, 0.3*cm))
        story.append(build_swot_table(swot_data, styles, page_width))
        story.append(Spacer(1, 0.5*cm))
        
        # Separateur
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC")))
        story.append(Spacer(1, 0.3*cm))
        
        # Section Plan d'Action
        plan_header = Table([[Paragraph("PLAN D'ACTION", styles["section"])]], colWidths=[page_width])
        plan_header.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), GREEN),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(plan_header)
        story.append(Spacer(1, 0.3*cm))
        
        for elem in build_plan_section(plan_data, styles, page_width):
            story.append(elem)
        
        # Pied de page
        story.append(Spacer(1, 1*cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC")))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(
            f"Document genere par Localis AI - {datetime.now().year}",
            styles["footer"]
        ))
        
        # Generer le PDF
        doc.build(story)
        
        return {
            "success": True,
            "filepath": str(filepath),
            "filename": filename,
            "swot_parsed": swot_data,
            "plan_parsed": plan_data
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Test
    test_diagnostic = """
    FORCES:
    - Equipe technique experimentee
    - Technologie innovante
    - Base clients fidele
    
    FAIBLESSES:
    - Budget marketing limite
    - Notoriete faible
    - Processus manuels
    
    OPPORTUNITES:
    - Expansion internationale
    - Partenariats strategiques
    - Nouveaux marches
    
    MENACES:
    - Concurrence agressive
    - Evolution technologique rapide
    """
    
    test_plan = """
    COURT TERME (0-6 mois):
    - Recruter un commercial senior
    - Lancer campagne marketing
    - Optimiser le site web
    
    MOYEN TERME (6-18 mois):
    - Developper l'API publique
    - Ouvrir un bureau a l'etranger
    - Obtenir certification ISO
    
    LONG TERME (18+ mois):
    - Lancer version 2.0
    - Atteindre 1000 clients
    - Lever des fonds
    """
    
    result = generate_pdf("MaSuperEntreprise", test_diagnostic, test_plan)
    print(result)
    
    if result["success"]:
        print(f"\n✅ PDF genere: {result['filepath']}")
        print(f"📊 SWOT parse: {list(result['swot_parsed'].keys())}")
        print(f"📋 Plan parse: {list(result['plan_parsed'].keys())}")