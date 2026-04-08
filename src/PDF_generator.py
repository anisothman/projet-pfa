import json
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.graphics.shapes import Drawing, Rect, String

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

NOM_PROJET = "LOCALGUIDE AI - Diagnostic Intelligence"

def create_rating_bar(rating):
   
    d = Drawing(350, 40)
    
    # Fond gris clair SANS bordure
    d.add(Rect(0, 0, 350, 40, fillColor=colors.HexColor('#ecf0f1'), strokeColor=None, strokeWidth=0))
    
    # Couleur selon le score
    if rating >= 75:
        color = colors.HexColor('#27ae60')  # Vert
    elif rating >= 50:
        color = colors.HexColor('#f39c12')  # Orange
    else:
        color = colors.HexColor('#e74c3c')  # Rouge
    
    bar_width = 350 * (rating / 100)
    d.add(Rect(0, 0, bar_width, 40, fillColor=color, strokeColor=None))
    
    # Texte du score
    d.add(String(175, 12, f"{rating}/100", fontSize=16, fillColor=colors.white, 
                 textAnchor='middle', fontName='Helvetica-Bold'))
    
    return d

def generate_smart_action_plan(forces, faiblesses, opportunites, menaces):
  
    
    court_terme = []
    moyen_terme = []
    long_terme = []
    
    # COURT TERME (0-6 mois) - Actions rapides
    if faiblesses:
        court_terme.append(f"Corriger rapidement : {faiblesses[0][:60]}")
    if forces:
        court_terme.append(f"Exploiter immédiatement : {forces[0][:60]}")
    court_terme.append("Mettre en place un tableau de bord de suivi des KPI")
    court_terme.append("Optimiser les processus opérationnels critiques")
    
    # MOYEN TERME (6-18 mois) - Développement
    if opportunites:
        moyen_terme.append(f"Développer : {opportunites[0][:60]}")
    if forces and len(forces) > 1:
        moyen_terme.append(f"Renforcer : {forces[1][:60]}")
    moyen_terme.append("Lancer un programme d'innovation interne")
    moyen_terme.append("Développer de nouveaux partenariats stratégiques")
    moyen_terme.append("Améliorer l'expérience client")
    
    # LONG TERME (18+ mois) - Vision stratégique
    if menaces:
        long_terme.append(f"Anticiper et contrer : {menaces[0][:60]}")
    long_terme.append("Définir une vision stratégique à 5 ans")
    long_terme.append("Investir dans la R&D et les technologies émergentes")
    long_terme.append("Explorer de nouveaux marchés géographiques")
    long_terme.append("Développer une culture d'entreprise durable")
    
    return court_terme[:3], moyen_terme[:4], long_terme[:4]

def export_pdf(rapport, output_dir=None):
    if output_dir is None:
        output_dir = REPORTS_DIR
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(exist_ok=True, parents=True)
    
    company = rapport.get("company_name", "unknown").upper()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_generation = datetime.now().strftime("%d/%m/%Y à %H:%M")
    filename = output_dir / f"diagnostic_{company.lower()}_{timestamp}.pdf"
    
    try:
        doc = SimpleDocTemplate(
            str(filename),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        styles = getSampleStyleSheet()
        
        # Styles
        project_style = ParagraphStyle('Project', parent=styles['Normal'], fontSize=11, 
                                       textColor=colors.HexColor('#7f8c8d'), alignment=TA_LEFT, spaceAfter=3)
        
        company_style = ParagraphStyle('Company', parent=styles['Heading1'], fontSize=24, 
                                       textColor=colors.HexColor('#1a5276'), alignment=TA_CENTER, 
                                       spaceAfter=5, fontName='Helvetica-Bold')
        
        date_style = ParagraphStyle('Date', parent=styles['Normal'], fontSize=11, 
                                    textColor=colors.HexColor('#7f8c8d'), alignment=TA_CENTER, spaceAfter=15)
        
        rating_title_style = ParagraphStyle('RatingTitle', parent=styles['Normal'], fontSize=16, 
                                            textColor=colors.HexColor('#2c3e50'), alignment=TA_CENTER, 
                                            spaceAfter=10, fontName='Helvetica-Bold')
        
        section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=14, 
                                       textColor=colors.white, backColor=colors.HexColor('#34495e'), 
                                       alignment=TA_LEFT, spaceBefore=20, spaceAfter=10, 
                                       fontName='Helvetica-Bold', leftIndent=10, rightIndent=10)
        
        bullet_style = ParagraphStyle('Bullet', parent=styles['Normal'], fontSize=10, 
                                      leftIndent=20, spaceAfter=3)
        
        normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=10, spaceAfter=5)
        
        story = []
        
        # ========== EN-TÊTE ==========
        story.append(Paragraph(NOM_PROJET, project_style))
        story.append(Spacer(1, 5))
        story.append(Paragraph(f"Rapport de diagnostic - {company}", company_style))
        story.append(Paragraph(f"Généré le {date_generation}", date_style))
        
        # Ligne de séparation
        story.append(Table([['']], colWidths=[doc.width], rowHeights=[1], 
                          style=[('LINEABOVE', (0,0), (0,0), 1, colors.HexColor('#bdc3c7'))]))
        story.append(Spacer(1, 20))
        
        # ========== RATING CENTRÉ SANS BORDURE ==========
        rating_data = rapport.get("rating", {})
        if isinstance(rating_data, dict):
            score_global = rating_data.get("score", 50)
        else:
            score_global = 50
        
        story.append(Paragraph("SCORE GLOBAL", rating_title_style))
        story.append(Spacer(1, 5))
        
        # Ajouter la barre de rating centrée
        rating_drawing = create_rating_bar(score_global)
        story.append(rating_drawing)
        story.append(Spacer(1, 8))
        
        # Appréciation
        if score_global >= 75:
            appreciation = "EXCELLENT - Performance supérieure"
            appreciation_color = colors.HexColor('#27ae60')
        elif score_global >= 50:
            appreciation = "BON - Performance satisfaisante"
            appreciation_color = colors.HexColor('#f39c12')
        else:
            appreciation = "À AMÉLIORER - Performance insuffisante"
            appreciation_color = colors.HexColor('#e74c3c')
        
        appreciation_style = ParagraphStyle('Appreciation', parent=styles['Normal'], 
                                           fontSize=12, textColor=appreciation_color, 
                                           alignment=TA_CENTER, spaceAfter=5, fontName='Helvetica-Bold')
        story.append(Paragraph(appreciation, appreciation_style))
        story.append(Spacer(1, 20))
        
        # ========== PARSER LE SWOT ==========
        swot_str = rapport.get("swot_analysis", "{}")
        try:
            if isinstance(swot_str, str):
                swot = json.loads(swot_str)
            else:
                swot = swot_str
        except:
            swot = {}
        
        forces = swot.get("points_forts", swot.get("strengths", []))
        faiblesses = swot.get("points_faibles", swot.get("weaknesses", []))
        opportunites = swot.get("opportunites", swot.get("opportunities", []))
        menaces = swot.get("menaces", swot.get("threats", []))
        
        # S'assurer que ce sont des listes
        if isinstance(forces, str): forces = [forces]
        if isinstance(faiblesses, str): faiblesses = [faiblesses]
        if isinstance(opportunites, str): opportunites = [opportunites]
        if isinstance(menaces, str): menaces = [menaces]
        
        # ========== SWOT EN TABLEAU ==========
        story.append(Paragraph("ANALYSE SWOT", section_style))
        story.append(Spacer(1, 10))
        
        def format_bullet_list(items, max_items=5):
            if not items:
                return [Paragraph("• Aucune donnée disponible", bullet_style)]
            
            result = []
            for item in items[:max_items]:
                text = str(item).strip()
                if text and text != "Données non disponibles":
                    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    result.append(Paragraph(f"• {text}", bullet_style))
            return result if result else [Paragraph("• Aucune donnée disponible", bullet_style)]
        
        forces_content = format_bullet_list(forces)
        faiblesses_content = format_bullet_list(faiblesses)
        opportunites_content = format_bullet_list(opportunites)
        menaces_content = format_bullet_list(menaces)
        
        swot_data = [
            [Paragraph("<b>FORCES</b>", ParagraphStyle('Header', parent=styles['Normal'], 
                       fontSize=12, textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica-Bold')),
             Paragraph("<b>FAIBLESSES</b>", ParagraphStyle('Header', parent=styles['Normal'], 
                       fontSize=12, textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica-Bold'))],
            [forces_content, faiblesses_content],
            [Paragraph("<b>OPPORTUNITÉS</b>", ParagraphStyle('Header', parent=styles['Normal'], 
                       fontSize=12, textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica-Bold')),
             Paragraph("<b>MENACES</b>", ParagraphStyle('Header', parent=styles['Normal'], 
                       fontSize=12, textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica-Bold'))],
            [opportunites_content, menaces_content]
        ]
        
        swot_table = Table(swot_data, colWidths=[8*cm, 8*cm])
        swot_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,0), colors.HexColor('#27ae60')),
            ('BACKGROUND', (1,0), (1,0), colors.HexColor('#e74c3c')),
            ('BACKGROUND', (0,2), (0,2), colors.HexColor('#2980b9')),
            ('BACKGROUND', (1,2), (1,2), colors.HexColor('#f39c12')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('BACKGROUND', (0,1), (1,1), colors.HexColor('#f9f9f9')),
            ('BACKGROUND', (0,3), (1,3), colors.HexColor('#f9f9f9')),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#bdc3c7')),
        ]))
        
        story.append(swot_table)
        story.append(Spacer(1, 25))
        
        # ========== PLAN D'ACTION 3 HORIZONS ==========
        story.append(Paragraph("PLAN D'ACTION STRATÉGIQUE", section_style))
        story.append(Spacer(1, 10))
        
        # Générer le plan d'action
        court_terme, moyen_terme, long_terme = generate_smart_action_plan(forces, faiblesses, opportunites, menaces)
        
        # Style pour les titres d'horizon
        horizon_style = ParagraphStyle('Horizon', parent=styles['Heading3'], fontSize=12, 
                                       textColor=colors.HexColor('#2c3e50'), spaceBefore=10, spaceAfter=5)
        
        # COURT TERME
        story.append(Paragraph("🔴 COURT TERME (0-6 mois)", horizon_style))
        for i, action in enumerate(court_terme, 1):
            action_clean = action.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(f"{i}. {action_clean}", bullet_style))
        story.append(Spacer(1, 10))
        
        # MOYEN TERME
        story.append(Paragraph("🟡 MOYEN TERME (6-18 mois)", horizon_style))
        for i, action in enumerate(moyen_terme, 1):
            action_clean = action.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(f"{i}. {action_clean}", bullet_style))
        story.append(Spacer(1, 10))
        
        # LONG TERME
        story.append(Paragraph("🟢 LONG TERME (18+ mois)", horizon_style))
        for i, action in enumerate(long_terme, 1):
            action_clean = action.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(f"{i}. {action_clean}", bullet_style))
        
        story.append(Spacer(1, 15))
        story.append(Paragraph("<i>* Plan d'action généré automatiquement à partir de l'analyse SWOT</i>", 
                               ParagraphStyle('Note', parent=styles['Italic'], fontSize=8, textColor=colors.grey)))
        
        # Générer le PDF
        doc.build(story)
        print(f"✅ PDF généré avec succès : {filename}")
        return str(filename)
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_pdf_from_json(json_path, output_dir=None):
    with open(json_path, 'r', encoding='utf-8') as f:
        rapport = json.load(f)
    return export_pdf(rapport, output_dir)
