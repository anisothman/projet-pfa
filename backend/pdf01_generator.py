"""
pdf_generator.py — Générateur PDF avec ReportLab
Design professionnel avec thème bleu épuré
"""

import re
from datetime import datetime
from pathlib import Path
import logging

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
)

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
LOGO_PATH = Path(__file__).parent / "images" / "logo1.png"

# ── Palette bleue professionnelle ──
BLUE_DARK   = colors.HexColor("#0B1E55")   # Bleu marine profond
BLUE_MED    = colors.HexColor("#2563EB")   # Bleu vif
BLUE_LIGHT  = colors.HexColor("#60A5FA")   # Bleu clair
BLUE_PALE   = colors.HexColor("#EFF6FF")   # Bleu très pâle (fond)
BLUE_ACCENT = colors.HexColor("#DBEAFE")   # Bleu accent doux
WHITE       = colors.white
BLACK       = colors.HexColor("#0F172A")
GRAY_DARK   = colors.HexColor("#475569")
GRAY_LIGHT  = colors.HexColor("#94A3B8")
ORANGE      = colors.HexColor("#F97316")   # Score accent
LINE_COLOR  = colors.HexColor("#BFDBFE")


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = str(text)
    replacements = {
        '\u201c': '"', '\u201d': '"', '\u2018': "'", '\u2019': "'",
        '\u00ab': '"', '\u00bb': '"', '\u2013': '-', '\u2014': '-',
        '\u2026': '...', '\u20ac': 'EUR',
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    text = re.sub(r'[^\x20-\x7E\u00C0-\u00FF\u0100-\u017F]', '', text)
    return text.strip()


def get_styles():
    b = getSampleStyleSheet()
    return {
        "h_company": ParagraphStyle("hCompany", parent=b["Normal"],
            fontSize=7, textColor=colors.HexColor("#93C5FD"), fontName="Helvetica",
            leading=10, alignment=TA_CENTER, spaceAfter=2),
        "h_title": ParagraphStyle("hTitle", parent=b["Normal"],
            fontSize=15, textColor=WHITE, fontName="Helvetica-Bold",
            leading=20, alignment=TA_CENTER),
        "h_title_main": ParagraphStyle("hTitleMain", parent=b["Normal"],
            fontSize=12, textColor=WHITE, fontName="Helvetica-Bold",
            leading=18, alignment=TA_CENTER),
        "h_date": ParagraphStyle("hDate", parent=b["Normal"],
            fontSize=7.5, textColor=colors.HexColor("#93C5FD"), fontName="Helvetica",
            leading=11, alignment=TA_RIGHT),
        "score_label": ParagraphStyle("scoreLabel", parent=b["Normal"],
            fontSize=10, textColor=GRAY_DARK, fontName="Helvetica-Bold",
            leading=14, alignment=TA_CENTER, spaceAfter=4),
        "score_value": ParagraphStyle("scoreValue", parent=b["Normal"],
            fontSize=36, textColor=BLUE_MED, fontName="Helvetica-Bold",
            leading=42, alignment=TA_CENTER),
        "score_sub": ParagraphStyle("scoreSub", parent=b["Normal"],
            fontSize=9, textColor=GRAY_LIGHT, fontName="Helvetica",
            leading=12, alignment=TA_CENTER),
        "sec_title": ParagraphStyle("secTitle", parent=b["Normal"],
            fontSize=11, textColor=WHITE, fontName="Helvetica-Bold",
            leading=16, alignment=TA_LEFT),
        "cat_title": ParagraphStyle("catTitle", parent=b["Normal"],
            fontSize=9.5, textColor=BLUE_DARK, fontName="Helvetica-Bold",
            leading=14),
        "item_text": ParagraphStyle("itemText", parent=b["Normal"],
            fontSize=9, textColor=BLACK, fontName="Helvetica",
            leading=14, spaceAfter=2),
        "item_desc": ParagraphStyle("itemDesc", parent=b["Normal"],
            fontSize=8, textColor=GRAY_DARK, fontName="Helvetica",
            leading=12, leftIndent=12, spaceAfter=4),
        "plan_header": ParagraphStyle("planHeader", parent=b["Normal"],
            fontSize=10, textColor=WHITE, fontName="Helvetica-Bold",
            leading=14),
        "plan_item": ParagraphStyle("planItem", parent=b["Normal"],
            fontSize=9, textColor=BLACK, fontName="Helvetica",
            leading=14, spaceAfter=2),
        "plan_desc": ParagraphStyle("planDesc", parent=b["Normal"],
            fontSize=8, textColor=GRAY_DARK, fontName="Helvetica",
            leading=12, leftIndent=12, spaceAfter=4),
        "footer": ParagraphStyle("footer", parent=b["Normal"],
            fontSize=7.5, textColor=GRAY_LIGHT, alignment=TA_CENTER),
        "page_title": ParagraphStyle("pageTitle", parent=b["Normal"],
            fontSize=10, textColor=GRAY_DARK, fontName="Helvetica",
            leading=14, alignment=TA_RIGHT),
    }


def section_bar(title, st, pw, icon=""):
    """Barre de section avec design moderne"""
    label = f"{icon}  {title}" if icon else f"  {title}"
    t = Table([[Paragraph(label, st["sec_title"])]], colWidths=[pw])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLUE_DARK),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("ROUNDEDCORNERS", [3, 3, 3, 3]),
    ]))
    return t


def category_block(label, items, st, pw, label_color=BLUE_PALE, label_text_color=BLUE_DARK):
    """Bloc de catégorie SWOT avec design épuré"""
    if not items:
        items = [{"titre": "Aucune information disponible", "description": ""}]

    rows = []

    # En-tête de catégorie
    cat_row = Table(
        [[Paragraph(f"  {label}", st["cat_title"])]],
        colWidths=[pw]
    )
    cat_row.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), label_color),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
    ]))
    rows.append([cat_row])

    # Items
    for item in items:
        if isinstance(item, dict):
            titre = normalize_text(item.get("titre", ""))
            desc = normalize_text(item.get("description", ""))
        else:
            titre = normalize_text(str(item))
            desc = ""

        item_rows = [[Paragraph(f"•  {titre}", st["item_text"])]]
        if desc:
            item_rows.append([Paragraph(desc, st["item_desc"])])

        item_table = Table(item_rows, colWidths=[pw - 2])
        item_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), WHITE),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 16),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        rows.append([item_table])

    t = Table(rows, colWidths=[pw])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WHITE),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOX", (0, 0), (-1, -1), 1, LINE_COLOR),
    ]))
    return t


def plan_section(subtitle, items, st, pw, header_color):
    """Bloc Plan d'action stylisé"""
    elems = []

    header = Table([[Paragraph(f"  {subtitle}", st["plan_header"])]], colWidths=[pw])
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), header_color),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
    ]))
    elems.append(header)

    if items:
        rows = []
        for item in items:
            if isinstance(item, dict):
                titre = normalize_text(item.get("titre", item.get("action", "")))
                desc = normalize_text(item.get("description", ""))
            else:
                titre = normalize_text(str(item))
                desc = ""

            rows.append([Paragraph(f"•  {titre}", st["plan_item"])])
            if desc:
                rows.append([Paragraph(desc, st["plan_desc"])])

        body = Table(rows, colWidths=[pw])
        body.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), WHITE),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 20),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ("BOX", (0, 0), (-1, -1), 1, LINE_COLOR),
            ("LINEBELOW", (0, 0), (-1, -2), 0.3, BLUE_ACCENT),
        ]))
        elems.append(body)
    else:
        empty = Table(
            [[Paragraph("  Aucune action définie pour cette période.", st["item_desc"])]],
            colWidths=[pw]
        )
        empty.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), WHITE),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("BOX", (0, 0), (-1, -1), 1, LINE_COLOR),
        ]))
        elems.append(empty)

    elems.append(Spacer(1, 0.3 * cm))
    return elems


def build_score_block(score, pw, st):
    """Bloc score visuel centré"""
    # Barre de progression manuelle
    fill_w = (score / 100) * (pw * 0.6)
    bg_w = pw * 0.6

    bar_bg = Table([[""]], colWidths=[bg_w])
    bar_bg.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLUE_ACCENT),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    bar_fill = Table([[""]], colWidths=[fill_w])
    bar_fill.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLUE_MED),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    elems = []
    elems.append(Spacer(1, 0.5 * cm))
    elems.append(Paragraph("Score de maturité globale", st["score_label"]))
    elems.append(Paragraph(f"<b>{score}</b>", st["score_value"]))
    elems.append(Paragraph("/ 100", st["score_sub"]))
    elems.append(Spacer(1, 0.3 * cm))

    # Centrage de la barre
    outer = Table(
        [[bar_bg]],
        colWidths=[pw],
    )
    outer.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elems.append(outer)
    elems.append(Spacer(1, 0.8 * cm))
    return elems


def generate_pdf(
    company_name: str,
    score: int,
    swot_analysis: dict,
    action_plan: dict,
    output_path: str = None
) -> dict:
    try:
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', company_name)[:30]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        fp = Path(output_path) if output_path else REPORTS_DIR / f"diagnostic_{safe_name}_{timestamp}.pdf"
        fp.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(fp), pagesize=A4,
            topMargin=1.4 * cm, bottomMargin=1.6 * cm,
            leftMargin=1.6 * cm, rightMargin=1.6 * cm,
        )

        st = get_styles()
        pw = A4[0] - 3.2 * cm
        date_str = datetime.now().strftime("%d/%m/%Y  %H:%M")
        story = []

        # ── EN-TÊTE AVEC NOUVEL ORDRE DES LIGNES ──
        if LOGO_PATH.exists():
            logo = Image(str(LOGO_PATH), width=1.8 * cm, height=1.8 * cm)
        else:
            logo = Paragraph("", st["h_date"])

        company_name_normalized = normalize_text(company_name)
        # Tronquer si trop long pour éviter les débordements
        if len(company_name_normalized) > 40:
            company_name_normalized = company_name_normalized[:37] + "..."

        # Nouvel ordre : Ligne 1 = RAPPORT DIAGNOSTIC, Ligne 2 = Nom entreprise, Ligne 3 = Logo + Date
        header_content = Table([
            ["", Paragraph("RAPPORT DIAGNOSTIC", st["h_title_main"]), ""],
            [logo, Paragraph(company_name_normalized, st["h_title"]), ""],
            ["", Paragraph(f"Généré le {date_str}", st["h_company"]), ""],
        ], colWidths=[pw * 0.12, pw * 0.76, pw * 0.12])

        header_content.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BLUE_DARK),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LINEBELOW", (0, 0), (-1, -1), 3, BLUE_MED),
        ]))

        header = header_content
        story.append(header)

        # ── SCORE ──
        story.extend(build_score_block(score, pw, st))

        # ── SÉPARATEUR ──
        story.append(HRFlowable(width="100%", thickness=0.8, color=LINE_COLOR))
        story.append(Spacer(1, 0.4 * cm))

        # ── SWOT ──
        story.append(section_bar("ANALYSE SWOT", st, pw))
        story.append(Spacer(1, 0.3 * cm))

        swot_items = [
            ("Points forts",        swot_analysis.get("points_forts", []),  colors.HexColor("#A7EDC8")),
            ("Points à améliorer",  swot_analysis.get("points_faibles", []), colors.HexColor("#F3D8B8")),
            ("Opportunités",        swot_analysis.get("opportunites", []),    colors.HexColor("#A0A7EB")),
            ("Menaces",             swot_analysis.get("menaces", []),         colors.HexColor("#F2BBBB")),
        ]

        for label, items, bg in swot_items:
            story.append(category_block(label, items, st, pw, label_color=bg))
            story.append(Spacer(1, 0.2 * cm))

        # ── PAGE 2 — PLAN D'ACTION ──
        story.append(PageBreak())
        story.append(Spacer(1, 0.5 * cm))
        story.append(section_bar("PLAN D'ACTION STRATEGIQUE", st, pw))
        story.append(Spacer(1, 0.4 * cm))

        plan_items = [
            ("Actions immediates  (0 - 3 mois)",    action_plan.get("court_terme", []),  BLUE_DARK),
            ("Actions moyen terme  (3 - 6 mois)",   action_plan.get("moyen_terme", []),  BLUE_MED),
            ("Actions long terme  (6 - 12 mois)",   action_plan.get("long_terme", []),   BLUE_LIGHT),
        ]

        for subtitle, items, color in plan_items:
            story.extend(plan_section(subtitle, items, st, pw, color))

        # ── PIED DE PAGE ──
        story.append(Spacer(1, 0.6 * cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=LINE_COLOR))
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph(
            f"Document confidentiel genere par Localis AI  •  {datetime.now().year}",
            st["footer"]
        ))

        doc.build(story)
        logger.info(f"PDF généré : {fp}")
        return {"success": True, "filepath": str(fp), "filename": fp.name}

    except Exception as e:
        logger.error(f"Erreur génération PDF : {e}", exc_info=True)
        return {"success": False, "error": str(e)}