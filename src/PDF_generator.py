"""
PDF_generator.py — LocalGuide AI v3.1
Rapport professionnel de diagnostic stratégique
"""

import json
import re
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.colors import HexColor

# Constants
BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

W, H = A4

# Color palette
class P:
    NAVY = HexColor('#0A1628')
    BLUE = HexColor('#2563EB')
    BLUE_L = HexColor('#EFF6FF')
    ACCENT = HexColor('#3B82F6')
    GREEN = HexColor('#10B981')
    GREEN_D = HexColor('#065F46')
    RED = HexColor('#EF4444')
    RED_D = HexColor('#7F1D1D')
    ORANGE = HexColor('#F97316')
    ORANGE_D = HexColor('#7C2D12')
    PURPLE = HexColor('#8B5CF6')
    GRAY_D = HexColor('#1F2937')
    GRAY_M = HexColor('#6B7280')
    GRAY_L = HexColor('#F9FAFB')
    GRAY_B = HexColor('#E5E7EB')
    WHITE = HexColor('#FFFFFF')
    SWOT_G = HexColor('#064E3B')
    SWOT_R = HexColor('#7F1D1D')
    SWOT_B = HexColor('#1E3A8A')
    SWOT_O = HexColor('#431407')


def safe(t, n=250):
    """Sécurise une chaîne pour le PDF"""
    if not t:
        return ""
    result = str(t)[:n]
    result = result.replace('&', '&amp;')
    result = result.replace('<', '&lt;')
    result = result.replace('>', '&gt;')
    return result


class ReportCanvas(pdfcanvas.Canvas):
    """Canvas personnalisé avec en-tête simplifié et footer"""
    
    def __init__(self, *args, company="", date_str="", score=0,
                 rating_label="", **kwargs):
        super().__init__(*args, **kwargs)
        self.company = company
        self.date_str = date_str
        self.score = score
        self.rating_label = rating_label
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._saved)
        for i, state in enumerate(self._saved):
            self.__dict__.update(state)
            self._draw_chrome(i + 1, n)
            pdfcanvas.Canvas.showPage(self)
        pdfcanvas.Canvas.save(self)

    def _draw_chrome(self, pg, total):
        HDR = 20 * mm
        
        # Fond bleu marine
        self.setFillColor(P.NAVY)
        self.rect(0, H - HDR, W, HDR, fill=1, stroke=0)
        
        # Barre bleue gauche
        self.setFillColor(P.BLUE)
        self.rect(0, H - HDR, 5 * mm, HDR, fill=1, stroke=0)

        # Logo
        self.setFont('Helvetica-Bold', 9)
        self.setFillColor(P.WHITE)
        self.drawString(8 * mm, H - 8 * mm, "LA")
        self.setFont('Helvetica', 9)
        self.setFillColor(P.GRAY_L)
        self.drawString(13 * mm, H - 8 * mm, "LOCALGUIDE AI")

        # Nom entreprise
        self.setFont('Helvetica-Bold', 13)
        self.setFillColor(P.WHITE)
        self.drawCentredString(W / 2, H - 9 * mm, self.company.upper())
        self.setFont('Helvetica', 7)
        self.setFillColor(HexColor('#94A3B8'))
        self.drawCentredString(W / 2, H - 14 * mm, "Rapport de Diagnostic Strategique")

        # Date de génération à droite
        self.setFont('Helvetica', 6.5)
        self.setFillColor(HexColor('#94A3B8'))
        self.drawRightString(W - 2 * cm, H - 8 * mm, f"Genere le {self.date_str}")

        # Ligne séparatrice
        self.setStrokeColor(P.BLUE)
        self.setLineWidth(1)
        self.line(0, H - HDR, W, H - HDR)

        # Footer
        self.setFillColor(P.GRAY_L)
        self.rect(0, 0, W, 10 * mm, fill=1, stroke=0)
        self.setStrokeColor(P.GRAY_B)
        self.setLineWidth(0.5)
        self.line(0, 10 * mm, W, 10 * mm)
        self.setFont('Helvetica', 6.5)
        self.setFillColor(P.GRAY_M)
        self.drawString(8 * mm, 3.5 * mm, "Document confidentiel — usage interne")
        self.drawCentredString(W / 2, 3.5 * mm, "LocalGuide AI — Intelligence Strategique")
        self.drawRightString(W - 8 * mm, 3.5 * mm, f"Page {pg} / {total}")


class ScoreGauge(Flowable):
    """Jauge circulaire pour le score"""
    
    def __init__(self, score, size=100):
        super().__init__()
        self.score = max(0, min(100, score))
        self.size = size
        self.width = size
        self.height = size + 10

    def draw(self):
        cx = self.size / 2
        cy = self.size / 2 + 5
        r = self.size / 2 - 8
        
        if self.score >= 75:
            col = P.GREEN
        elif self.score >= 50:
            col = P.ACCENT
        else:
            col = P.RED

        # Piste grise
        self.canv.setStrokeColor(P.GRAY_B)
        self.canv.setLineWidth(12)
        self.canv.arc(cx - r, cy - r, cx + r, cy + r, startAng=0, extent=360)

        # Arc coloré
        self.canv.setStrokeColor(col)
        self.canv.setLineWidth(12)
        self.canv.arc(cx - r, cy - r, cx + r, cy + r,
                      startAng=90, extent=-360 * self.score / 100)

        # Fond blanc intérieur
        self.canv.setFillColor(P.WHITE)
        self.canv.circle(cx, cy, r - 8, fill=1, stroke=0)

        # Score
        self.canv.setFillColor(P.GRAY_D)
        self.canv.setFont('Helvetica-Bold', 28)
        self.canv.drawCentredString(cx, cy + 4, str(self.score))
        self.canv.setFont('Helvetica', 9)
        self.canv.setFillColor(P.GRAY_M)
        self.canv.drawCentredString(cx, cy - 13, "/100")


class ProgressBar(Flowable):
    """Barre de progression horizontale"""
    
    def __init__(self, label, value, max_v=20, color=P.BLUE, width=250, height=18):
        super().__init__()
        self.label = label
        self.value = value
        self.max_v = max_v
        self.color = color
        self.width = width
        self.height = height

    def draw(self):
        bx = 110
        bw = self.width - bx - 30
        fw = min(bw, bw * (self.value / self.max_v))
        my = self.height / 2
        
        self.canv.setFont('Helvetica', 7)
        self.canv.setFillColor(P.GRAY_D)
        self.canv.drawString(0, my - 3.5, self.label)
        
        self.canv.setFillColor(P.GRAY_B)
        self.canv.roundRect(bx, my - 4, bw, 8, 4, fill=1, stroke=0)
        
        if fw > 1:
            self.canv.setFillColor(self.color)
            self.canv.roundRect(bx, my - 4, fw, 8, 4, fill=1, stroke=0)
        
        self.canv.setFont('Helvetica-Bold', 7)
        self.canv.setFillColor(P.GRAY_M)
        self.canv.drawString(bx + bw + 5, my - 3.5, f"{self.value:.0f}/20")


def get_styles():
    """Retourne les styles de paragraphe"""
    return {
        'sec': ParagraphStyle(
            'Sec', fontName='Helvetica-Bold', fontSize=13,
            textColor=P.NAVY, spaceBefore=16, spaceAfter=7
        ),
        'ct': ParagraphStyle(
            'CT', fontName='Helvetica-Bold', fontSize=9,
            textColor=P.WHITE, leading=13
        ),
        'cb': ParagraphStyle(
            'CB', fontName='Helvetica', fontSize=7.5,
            textColor=HexColor('#CBD5E1'), leading=12, spaceAfter=5
        ),
        'tlt': ParagraphStyle(
            'TLT', fontName='Helvetica-Bold', fontSize=8.5,
            textColor=P.GRAY_D, spaceAfter=1
        ),
        'tlb': ParagraphStyle(
            'TLB', fontName='Helvetica', fontSize=7.5,
            textColor=P.GRAY_M, leading=11
        ),
        'kl': ParagraphStyle(
            'KL', fontName='Helvetica', fontSize=7,
            textColor=P.GRAY_M, alignment=TA_CENTER
        ),
    }


def sec_hdr(title, styles, color=None):
    """Génère un en-tête de section"""
    if color is None:
        color = P.NAVY
    return [
        Spacer(1, 4),
        HRFlowable(width="100%", thickness=2, color=color, spaceAfter=4),
        Paragraph(title, styles['sec']),
    ]


SWOT_ROW_H = 22
SWOT_HDR_H = 28
SWOT_MAX_ITEMS = 5


def swot_card(items, title, bg, accent, styles):
    """Carte SWOT à hauteur fixe"""
    rows = []
    heights = []

    # Header
    rows.append([Paragraph(f"<b>{title}</b>", styles['ct'])])
    heights.append(SWOT_HDR_H)

    # Items
    display = list(items or [])[:SWOT_MAX_ITEMS]
    while len(display) < SWOT_MAX_ITEMS:
        display.append(None)

    for item in display:
        if item is None:
            rows.append([Paragraph("", styles['cb'])])
        elif isinstance(item, dict):
            t = safe(item.get('titre', item.get('action', '')), 80)
            d = safe(item.get('description', ''), 110)
            content = f"<b>{t}</b>"
            if d and d != t:
                content += f"<br/><font color='#94A3B8' size='6.5'>{d}</font>"
            rows.append([Paragraph(content, styles['cb'])])
        else:
            rows.append([Paragraph(f"<b>{safe(str(item), 80)}</b>", styles['cb'])])
        heights.append(SWOT_ROW_H)

    t = Table(rows, colWidths=[8.4 * cm], rowHeights=heights)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), accent),
        ('BACKGROUND', (0, 1), (-1, -1), bg),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return t


def timeline_item(idx, action, color, styles):
    """Élément de la timeline"""
    if isinstance(action, dict):
        title = action.get('action', action.get('titre', ''))
        desc = action.get('description', '')
    else:
        title = str(action)
        desc = ""

    num = Table(
        [[Paragraph(str(idx), ParagraphStyle(
            'N', fontName='Helvetica-Bold', fontSize=9,
            textColor=P.WHITE, alignment=TA_CENTER))]],
        colWidths=[0.55 * cm],
        style=[
            ('BACKGROUND', (0, 0), (-1, -1), color),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
        ]
    )

    txt = Table(
        [
            [Paragraph(safe(title, 100), styles['tlt'])],
            [Paragraph(safe(desc, 160), styles['tlb'])],
        ],
        colWidths=[None],
        style=[
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0)
        ]
    )

    row = Table([[num, txt]], colWidths=[0.75 * cm, 10.8 * cm])
    row.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0)
    ]))
    return row


def export_pdf(rapport, output_dir=None):
    """Exporte un rapport en PDF"""
    output_dir = Path(output_dir) if output_dir else REPORTS_DIR
    output_dir.mkdir(exist_ok=True, parents=True)

    company = rapport.get("company_name", "Entreprise").upper()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str = datetime.now().strftime("%d/%m/%Y")
    filename = output_dir / f"diagnostic_{company.lower()}_{ts}.pdf"

    # Parse SWOT
    swot_raw = rapport.get("swot_analysis", {})
    if swot_raw is None:
        swot_raw = {}
    
    if isinstance(swot_raw, str):
        try:
            swot = json.loads(swot_raw) if swot_raw.strip() else {}
        except:
            swot = {}
    else:
        swot = swot_raw if isinstance(swot_raw, dict) else {}

    def lst(v):
        if isinstance(v, list):
            return v
        if isinstance(v, str) and v:
            return [v]
        return []

    forces = lst(swot.get("points_forts", swot.get("strengths", [])))
    faibls = lst(swot.get("points_faibles", swot.get("weaknesses", [])))
    opps = lst(swot.get("opportunites", swot.get("opportunities", [])))
    menac = lst(swot.get("menaces", swot.get("threats", [])))

    # Parse plan d'action - SANS VALEURS PAR DÉFAUT
    plan_raw = rapport.get("action_plan", rapport.get("plan_action", {}))
    if plan_raw is None:
        plan_raw = {}

    if isinstance(plan_raw, dict):
        court = lst(plan_raw.get("court_terme", []))
        moyen = lst(plan_raw.get("moyen_terme", []))
        long_ = lst(plan_raw.get("long_terme", []))
    else:
        court = moyen = long_ = []

    # PAS de valeurs par défaut - les listes restent vides si pas de données

    # Score
    rd = rapport.get("rating", {})
    if rd is None:
        rd = {}
    
    if isinstance(rd, dict) and 0 < rd.get("score", 0) <= 100:
        score = int(rd["score"])
        justif = rd.get("justification", "")
    else:
        score = 50
        score += min(len(forces) * 8, 20)
        score += min(len(opps) * 8, 20)
        score -= min(len(faibls) * 7, 18)
        score -= min(len(menac) * 7, 18)
        score = max(10, min(95, score))
        justif = ""

    if score >= 75:
        sc_color = P.GREEN
        rl = "EXCELLENT"
    elif score >= 50:
        sc_color = P.ACCENT
        rl = "SATISFAISANT"
    else:
        sc_color = P.RED
        rl = "A AMELIORER"

    # Performance criteria
    crit = [
        ("Position concurrentielle", score * 20 / 100, P.BLUE),
        ("Solidite financiere", score * 20 / 100, P.GREEN),
        ("Innovation & Technologie", score * 20 / 100, P.PURPLE),
        ("Satisfaction client", score * 20 / 100, P.ACCENT),
        ("Potentiel de croissance", score * 20 / 100, P.ORANGE),
    ]
    offsets = [1.1, 0.95, 1.05, 0.9, 1.0]
    crit = [(n, min(20, v * o), c) for (n, v, c), o in zip(crit, offsets)]

    try:
        styles = get_styles()

        doc = SimpleDocTemplate(
            str(filename), pagesize=A4,
            rightMargin=1.8 * cm, leftMargin=1.8 * cm,
            topMargin=2.6 * cm, bottomMargin=1.6 * cm,
            title=f"Diagnostic {company}", author="LocalGuide AI"
        )

        story = []

        # SECTION 1: RATING + SWOT
        story.extend(sec_hdr("Score Global & Analyse SWOT", styles))

        gauge = ScoreGauge(score, size=95)

        rating_badge = Paragraph(
            f"<b>{rl}</b>",
            ParagraphStyle(
                'RB', fontName='Helvetica-Bold', fontSize=10,
                textColor=sc_color, alignment=TA_CENTER, spaceAfter=4
            )
        )

        justif_p = Paragraph(
            f"<i>{safe(justif, 220)}</i>",
            ParagraphStyle(
                'JP', fontName='Helvetica-Oblique', fontSize=7,
                textColor=P.GRAY_M, alignment=TA_CENTER, leading=10
            )
        ) if justif else Spacer(1, 2)

        # Performance bars
        bar_rows = [[ProgressBar(name, val, 20, col, 250, 18)]
                    for name, val, col in crit]
        bar_tbl = Table(bar_rows, colWidths=[None])
        bar_tbl.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        left_col = Table(
            [[gauge], [rating_badge], [justif_p]],
            colWidths=[4 * cm]
        )
        left_col.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        perf_title = Paragraph(
            "INDICATEURS DE PERFORMANCE",
            ParagraphStyle(
                'PT', fontName='Helvetica-Bold', fontSize=7.5,
                textColor=P.GRAY_M, spaceAfter=5
            )
        )

        right_col = Table(
            [[perf_title], [bar_tbl]],
            colWidths=[None]
        )
        right_col.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        rating_block = Table(
            [[left_col, right_col]],
            colWidths=[4.5 * cm, None]
        )
        rating_block.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (0, 0), P.BLUE_L),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('LINEAFTER', (0, 0), (0, -1), 0.5, P.GRAY_B),
        ]))
        story.append(KeepTogether([rating_block]))
        story.append(Spacer(1, 14))

        # SWOT grid
        story.append(Paragraph(
            "ANALYSE SWOT",
            ParagraphStyle(
                'SL', fontName='Helvetica-Bold', fontSize=7.5,
                textColor=P.GRAY_M, spaceAfter=5
            )
        ))

        swot_grid = Table([
            [swot_card(forces, "  FORCES", P.SWOT_G, P.GREEN_D, styles),
             swot_card(faibls, "  FAIBLESSES", P.SWOT_R, P.RED_D, styles)],
            [swot_card(opps, "  OPPORTUNITES", P.SWOT_B, HexColor('#1E3A8A'), styles),
             swot_card(menac, "  MENACES", P.SWOT_O, P.ORANGE_D, styles)],
        ], colWidths=[8.4 * cm, 8.4 * cm])
        swot_grid.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(swot_grid)
        story.append(PageBreak())

        # SECTION 2: ACTION PLAN
        story.extend(sec_hdr("Plan d'Action Strategique", styles, P.BLUE))

        horizons = [
            (P.RED, "COURT TERME", "0 - 6 mois", court),
            (P.ACCENT, "MOYEN TERME", "6 - 18 mois", moyen),
            (P.GREEN, "LONG TERME", "18+ mois", long_),
        ]

        hdrs, bods = [], []
        for col, title, period, actions in horizons:
            hdr = Table([
                [Paragraph(
                    f"<b>{title}</b>",
                    ParagraphStyle(
                        'HH', fontName='Helvetica-Bold',
                        fontSize=9, textColor=P.WHITE, alignment=TA_CENTER
                    )
                )],
                [Paragraph(
                    period,
                    ParagraphStyle(
                        'HP', fontName='Helvetica',
                        fontSize=7, textColor=HexColor('#CBD5E1'),
                        alignment=TA_CENTER
                    )
                )],
            ], colWidths=[None])
            hdr.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), col),
                ('TOPPADDING', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ]))
            hdrs.append(hdr)

            brows = []
            for i, a in enumerate(actions[:5], 1):
                brows.append([timeline_item(i, a, col, styles)])
                brows.append([Spacer(1, 2)])
            if not brows:
                brows = [[Paragraph("Aucune action definie.", styles['tlb'])]]
            body = Table(brows, colWidths=[None])
            body.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), P.GRAY_L),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            bods.append(body)

        plan_tbl = Table([hdrs, bods], colWidths=[5.7 * cm] * 3)
        plan_tbl.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(plan_tbl)
        story.append(Spacer(1, 18))

                # SECTION 3: KPIs
        story.extend(sec_hdr("Tableau de Bord KPI", styles, P.GREEN))

        kpis = [
            (f"{score}/100", "Score Global", sc_color),
            (str(len(forces)), "Forces", P.GREEN),
            (str(len(faibls)), "Faiblesses", P.RED),
            (str(len(opps)), "Opportunites", P.BLUE),
            (str(len(menac)), "Menaces", P.ORANGE),
            (str(len(court) + len(moyen) + len(long_)), "Actions Total", P.PURPLE),
        ]

        # Créer deux lignes : une pour le score, une pour les autres KPIs
        score_row = [kpis[0]]  # Première ligne : seulement le score global
        kpis_row = kpis[1:]    # Deuxième ligne : tous les autres KPIs

        # Générer les cellules pour la première ligne (Score Global)
        score_cells = []
        for val, lbl, col in [score_row[0]]:
            c = Table([
                [Paragraph(
                    val,
                    ParagraphStyle(
                        'KV', fontName='Helvetica-Bold',
                        fontSize=18, textColor=col, alignment=TA_CENTER
                    )
                )],
                [Paragraph(lbl, styles['kl'])],
            ], colWidths=[None])
            c.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (-1, -1), P.WHITE),
                ('LINEBELOW', (0, 0), (-1, 0), 2.5, col),
                ('BOX', (0, 0), (-1, -1), 0.5, P.GRAY_B),
            ]))
            score_cells.append(c)

        # Générer les cellules pour la deuxième ligne (autres KPIs)
        kpis_cells = []
        for val, lbl, col in kpis_row:
            c = Table([
                [Paragraph(
                    val,
                    ParagraphStyle(
                        'KV', fontName='Helvetica-Bold',
                        fontSize=18, textColor=col, alignment=TA_CENTER
                    )
                )],
                [Paragraph(lbl, styles['kl'])],
            ], colWidths=[None])
            c.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (-1, -1), P.WHITE),
                ('LINEBELOW', (0, 0), (-1, 0), 2.5, col),
                ('BOX', (0, 0), (-1, -1), 0.5, P.GRAY_B),
            ]))
            kpis_cells.append(c)

        # Créer les deux tables
        score_row_table = Table([score_cells], colWidths=[2.8 * cm])
        score_row_table.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))

        kpis_row_table = Table([kpis_cells], colWidths=[2.8 * cm] * 5)
        kpis_row_table.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))

        story.append(score_row_table)
        story.append(Spacer(1, 6))  # Petit espace entre les deux lignes
        story.append(kpis_row_table)
        story.append(Spacer(1, 12))

        # Footer
        story.append(HRFlowable(width="100%", thickness=0.5, color=P.GRAY_B, spaceAfter=6))
        # Footer
        story.append(HRFlowable(width="100%", thickness=0.5, color=P.GRAY_B, spaceAfter=6))
        
        footer_style = ParagraphStyle(
            'FooterStyle',
            fontName='Helvetica-Oblique',
            fontSize=7.5,
            textColor=P.GRAY_M,
            alignment=TA_CENTER,
            spaceAfter=0,
            spaceBefore=0
        )
        
        story.append(Paragraph(
            "Ce rapport a ete genere automatiquement par LocalGuide AI. "
            "Les analyses sont basees sur les donnees disponibles au moment de la generation. "
            "Document confidentiel — usage interne uniquement.",
            footer_style
        ))

        # Build PDF
        class CM(ReportCanvas):
            def __init__(self2, *args, **kwargs):
                super().__init__(
                    *args, company=company, date_str=date_str,
                    score=score, rating_label=rl,
                    **kwargs
                )

        doc.build(story, canvasmaker=CM)
        print(f"  PDF genere : {filename}")
        return str(filename)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"  Erreur : {e}")
        return None


def generate_pdf_from_json(json_path, output_dir=None):
    """Génère un PDF à partir d'un fichier JSON"""
    with open(json_path, 'r', encoding='utf-8') as f:
        rapport = json.load(f)
    return export_pdf(rapport, output_dir)


def export_all_pdf(reports_data, output_dir=None):
    """Exporte plusieurs rapports en PDF"""
    results = []
    for report in reports_data:
        try:
            if isinstance(report, (str, Path)):
                with open(report, 'r', encoding='utf-8') as f:
                    rapport = json.load(f)
            elif isinstance(report, dict):
                rapport = report
            else:
                print(f"  Ignoré: type non supporté {type(report)}")
                continue
            
            pdf_path = export_pdf(rapport, output_dir)
            if pdf_path:
                results.append(pdf_path)
                print(f"  ✓ PDF généré: {pdf_path}")
            else:
                print(f"  ✗ Échec génération PDF pour {rapport.get('company_name', 'Inconnu')}")
                
        except Exception as e:
            print(f"  Erreur lors du traitement: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"{len(results)} PDF(s) généré(s)")
    return results


if __name__ == "__main__":
    import sys
    
    reports_dir = Path(__file__).resolve().parent.parent / "reports"
    
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
        print(f"Génération PDF depuis: {json_file}")
        generate_pdf_from_json(json_file)
    else:
        json_files = list(reports_dir.glob("diagnostic_*.json"))
        
        if json_files:
            print(f" Dossier: {reports_dir}")
            print(f" {len(json_files)} fichier(s) JSON trouvé(s)\n")
            
            for json_file in json_files:
                print(f"Génération PDF pour: {json_file.name}")
                try:
                    pdf_path = generate_pdf_from_json(str(json_file))
                    if pdf_path:
                        print(f"  PDF créé: {Path(pdf_path).name}")
                    else:
                        print(f" Échec génération")
                except Exception as e:
                    print(f"  Erreur: {e}")
                print()
        else:
            print(f" Aucun fichier diagnostic_*.json trouvé dans {reports_dir}")