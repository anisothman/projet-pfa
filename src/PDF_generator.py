"""
DiagnoReport - Generateur de rapports PDF professionnel
Responsable: Maram
Sprint 3 - Generation PDF avec rating, SWOT tableau, plan d'action
Features: Rating IA /100, Tableau SWOT 4 cadrants, Plan d'action detaille
"""

import os
import re
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle, PageBreak, Image
)

# ── Chemins ────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# ── Couleurs professionnelles ──────────────────────────────────────────────
DARK_BLUE   = colors.HexColor("#1B2A4A")
MEDIUM_BLUE = colors.HexColor("#2C5F8A")
LIGHT_BLUE  = colors.HexColor("#D6EAF8")
GREEN       = colors.HexColor("#27AE60")
RED         = colors.HexColor("#E74C3C")
ORANGE      = colors.HexColor("#E67E22")
GRAY        = colors.HexColor("#5A5A5A")
LIGHT_GRAY  = colors.HexColor("#F4F4F4")
SEPARATOR   = colors.HexColor("#CCCCCC")
WHITE       = colors.white
BLACK       = colors.black

# ── Couleurs SWOT ─────────────────────────────────────────────────────────
SWOT_COLORS = {
    "Forces":       (colors.HexColor("#27AE60"), colors.HexColor("#D5F4E6")),
    "Faiblesses":   (colors.HexColor("#E74C3C"), colors.HexColor("#FADBD8")),
    "Opportunites": (colors.HexColor("#3498DB"), colors.HexColor("#D6EAF8")),
    "Menaces":      (colors.HexColor("#F39C12"), colors.HexColor("#FEF5E7")),
}

# ══════════════════════════════════════════════════════════════════════════════
# STYLES PDF
# ══════════════════════════════════════════════════════════════════════════════

def build_styles():
    """Définit tous les styles utilisés dans le PDF"""
    return {
        # En-tête
        "company_title": ParagraphStyle(
            "company_title",
            fontName="Helvetica-Bold",
            fontSize=24,
            textColor=WHITE,
            alignment=TA_CENTER,
            spaceAfter=8
        ),
        "subtitle_header": ParagraphStyle(
            "subtitle_header",
            fontName="Helvetica",
            fontSize=12,
            textColor=colors.HexColor("#E8F4F8"),
            alignment=TA_CENTER,
            spaceAfter=4
        ),
        "date_header": ParagraphStyle(
            "date_header",
            fontName="Helvetica-Oblique",
            fontSize=10,
            textColor=colors.HexColor("#B0D4E3"),
            alignment=TA_CENTER
        ),
        # Titres de section
        "section_title": ParagraphStyle(
            "section_title",
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=WHITE,
            leftIndent=10,
            spaceAfter=6
        ),
        # Rating
        "rating_score": ParagraphStyle(
            "rating_score",
            fontName="Helvetica-Bold",
            fontSize=42,
            textColor=DARK_BLUE,
            alignment=TA_CENTER,
            leading=50
        ),
        "rating_label": ParagraphStyle(
            "rating_label",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=GRAY,
            alignment=TA_CENTER,
            spaceAfter=6
        ),
        "rating_justif": ParagraphStyle(
            "rating_justif",
            fontName="Helvetica-Oblique",
            fontSize=10,
            textColor=GRAY,
            alignment=TA_CENTER,
            leading=14
        ),
        # SWOT
        "swot_header": ParagraphStyle(
            "swot_header",
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=WHITE,
            alignment=TA_CENTER,
            spaceAfter=8
        ),
        "swot_point": ParagraphStyle(
            "swot_point",
            fontName="Helvetica",
            fontSize=10,
            textColor=BLACK,
            leading=16,
            spaceAfter=6,
            leftIndent=6
        ),
        # Plan d'action
        "bullet": ParagraphStyle(
            "bullet",
            fontName="Helvetica",
            fontSize=11,
            textColor=colors.HexColor("#2C3E50"),
            leftIndent=20,
            spaceAfter=10,
            leading=16,
            bulletIndent=10
        ),
        "action_title": ParagraphStyle(
            "action_title",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=MEDIUM_BLUE,
            spaceAfter=6,
            leftIndent=14
        ),
        # Métadonnées
        "meta_label": ParagraphStyle(
            "meta_label",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=DARK_BLUE,
            spaceAfter=3
        ),
        "meta_value": ParagraphStyle(
            "meta_value",
            fontName="Helvetica",
            fontSize=9,
            textColor=GRAY,
            spaceAfter=3
        ),
        # Footer
        "footer_style": ParagraphStyle(
            "footer_style",
            fontName="Helvetica-Oblique",
            fontSize=8,
            textColor=GRAY,
            alignment=TA_CENTER
        ),
    }


def format_date(iso_date):
    """Formate une date ISO en format lisible"""
    try:
        dt = datetime.fromisoformat(iso_date)
        return dt.strftime("%d/%m/%Y à %H:%M:%S")
    except:
        return str(iso_date)

def rating_color(score):
    """Retourne la couleur en fonction du score"""
    if score >= 75:
        return colors.HexColor("#27AE60")  
