"""
Intégration complète: TextCleaner + ResponseFormatter

Montre comment utiliser les deux classes ensemble pour:
1. Nettoyer les réponses brutes de Gemini
2. Détecter les sections
3. Parser en JSON structuré
4. Valider la structure
5. Exporter
"""

import json
from datetime import datetime
from src.text_cleaner import TextCleaner
from src.response_formatter import ResponseFormatter
from src.logger_config import logger


def pipeline_complet_avec_nettoyage(
    company_name: str,
    gemini_raw_response: str,
    company_data: dict,
    prompt_type: str = "diagnostic"
) -> dict:
    """
    Pipeline complète avec nettoyage & formatage
    
    Args:
        company_name: Nom de l'entreprise
        gemini_raw_response: Réponse brute de Gemini (sale)
        company_data: Données SerpAPI
        prompt_type: "diagnostic" ou "plan_action"
    
    Returns:
        Dict JSON structuré et validé
    """
    
    print(f"\n{'='*60}")
    print(f"Pipeline: {company_name} - {prompt_type}")
    print(f"{'='*60}")
    
    # ========================================================================
    # ÉTAPE 1: NETTOYER
    # ========================================================================
    print("ÉTAPE 1: Nettoyage du texte...")
    
    cleaner = TextCleaner()
    clean_result = cleaner.full_pipeline(gemini_raw_response)
    
    clean_text = clean_result['clean_text']
    quality_score = clean_result['quality_score']
    sections_detected = list(clean_result['sections_content'].keys())
    
    print(f"   ✓ Qualité: {quality_score}/100")
    print(f"   ✓ Sections détectées: {sections_detected}")
    
    if quality_score < 50:
        logger.warning(f"  Qualité faible ({quality_score}/100). Parsing peut être imprécis.")
    
    # ========================================================================
    # ÉTAPE 2: FORMATTER
    # ========================================================================
    print(" ÉTAPE 2: Formatage en JSON...")
    
    formatter = ResponseFormatter(
        company_name=company_name,
        prompt_type=prompt_type
    )
    
    if prompt_type == "diagnostic":
        structured = formatter.format_diagnostic_response(clean_text, company_data)
    elif prompt_type == "plan_action":
        structured = formatter.format_plan_action_response(clean_text, company_data)
    else:
        raise ValueError(f"prompt_type doit être 'diagnostic' ou 'plan_action', pas {prompt_type}")
    
    print(f"   ✓ Structure JSON créée")
    
    # ========================================================================
    # ÉTAPE 3: VALIDER
    # ========================================================================
    print(" ÉTAPE 3: Validation schéma...")
    
    is_valid, errors = formatter.validate_against_schema(structured)
    
    if is_valid:
        print(f"   ✓ Validation RÉUSSIE ")
    else:
        print(f"    Validation ÉCHOUÉE:")
        for error in errors:
            print(f"      - {error}")
        logger.error(f"Validation failed: {errors}")
    
    # ========================================================================
    # ÉTAPE 4: AFFICHER RÉSUMÉ
    # ========================================================================
    print("RÉSUMÉ:")
    
    if prompt_type == "diagnostic":
        diag = structured['diagnostic']
        print(f"   - Points forts: {len(diag['points_forts'])}")
        print(f"   - Points faibles: {len(diag['points_faibles'])}")
        print(f"   - Opportunités: {len(diag['opportunites'])}")
        if structured.get('analyse_avis'):
            print(f"   - Analyse avis: ✓")
    
    elif prompt_type == "plan_action":
        plan = structured['plan_action']
        print(f"   - Actions court terme: {len(plan['court_terme'])}")
        print(f"   - Actions moyen terme: {len(plan['moyen_terme'])}")
        print(f"   - Actions long terme: {len(plan['long_terme'])}")
        print(f"   - KPIs: {len(plan.get('kpis', []))}")
        print(f"   - Risques: {len(plan.get('risques', []))}")
    
    print(f"   - Validation: {'✓ OK' if is_valid else '✗ ERREUR'}")
    print(f"   - ID analyse: {structured['metadonnees']['id_analyse']}")
    
    return structured


def demo_gemini_sale_vs_propre():
    """
    Démontre le nettoyage: texte sale → texte propre
    """
    
    print("\n" + "="*70)
    print("DÉMO: Nettoyage Gemini Sale → Propre")
    print("="*70)
    
    # Texte SALE (comme pourrait rendre Gemini)
    gemini_sale = """
    FORCES ET POINTS FORTS DE L'ENTREPRISE 
    
    [on commence avec les forces]
    
    1)  **Marque extrêmement puissante** ( ___CRITIQUE___ / VERY IMPORTANT )
    (description): Apple enjoys exceptional brand value and customer loyalty...
    
    II. Innovation En Recherche & Developpement..... (critical importance level)
    - The company invests heavily in R&D departments
    - Continuous product innovation pipeline
    
    =================================
    POINTS FAIBLES / WEAKNESS ANALYSIS
    =================================
    
    • Dependance des fournisseurs extérieurs ( MAJOR / high )
      => TSMC concentration creates supply chain risk
    
    * Prix très élévés (MAJEUR)
      Reduces market penetration in mid-segment
    
    ───────────────────
    opportUNITIES Section
    ───────────────────
    
    ✓ Expansion AI and Machine Learning (potential: VERY HIGH)
      Description: Integrate AI capabilities into products...
      
    ✓ Services Subscription Model (very strong potential)
      Create recurring revenue streams...
    """
    
    # Données de test
    company_data = {
        "name": "Apple Inc.",
        "address": "1 Apple Park Way",
        "rating": 4.7,
        "review_count": 2543
    }
    
    print("\n AVANT NETTOYAGE:")
    print("-" * 70)
    print(gemini_sale[:300] + "...[truncated]")
    
    # Nettoyage
    cleaner = TextCleaner()
    clean_result = cleaner.full_pipeline(gemini_sale)
    
    print("\n" + "="*70)
    print("\n✨ APRÈS NETTOYAGE:")
    print("-" * 70)
    print(clean_result['clean_text'][:300] + "...[truncated]")
    
    print(f"\n STATISTIQUES:")
    print(f"   - Qualité: {clean_result['quality_score']}/100")
    print(f"   - Sections: {list(clean_result['sections_content'].keys())}")
    print(f"   - Longueur avant: {len(gemini_sale)} chars")
    print(f"   - Longueur après: {len(clean_result['clean_text'])} chars")
    
    # Parser en JSON
    print(f"\n" + "="*70)
    print(" CONVERSION EN JSON:")
    print("="*70)
    
    result = pipeline_complet_avec_nettoyage(
        company_name="Apple",
        gemini_raw_response=gemini_sale,
        company_data=company_data,
        prompt_type="diagnostic"
    )
    
    # Sauvegarder
    output_file = "apple_demo_cleaned.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Sauvegardé dans: {output_file}")


def demo_plan_action_sale():
    """
    Démontre le nettoyage d'un plan d'action sale
    """
    
    print("\n" + "="*70)
    print("DÉMO: Plan d'Action Sale")
    print("="*70)
    
    gemini_sale = """
    EXECUTIVE SUMMARY!!!
    
    Apple should focus on AI innovation and market expansion...
    
    === SHORT TERM ACTIONS (0-3months) ===
    
    1)  Launch AI Copilot for SMEs -- PRIORITY: P0 !!!
    Resp: VP Product... Timeline: 90 daysss
    $$$: 2.5Million EUR
    Details: Create packaged AI offering tailored to local market needs
    
    2.)  Hire Cloud Team Members  [PRIORITY=P1]
    ===> Responsible Dept: VP Operations
    ----> Estimated Timeframe: 60 DAYS 
    Plan Details: Recruit 20 cloud specialists..
    
    ~~ MEDIUM TERM (3-6months) ~~
    
    • AI Excellence Center Foundation (p1 PRIORITY)
      Duration: 5months | Budget: 5M€
      Strategy: Build local innovation hub...
    
    LOOOOONG TERM ACTIONS (6-12 months)
    
    → Strategic Startup Acquisition (PRIORITY p2)
      Description: Identify and acquire AI-focused startup...
    
    KPI TRACKING
    - Metrics: AI Revenue → baseline: 0€ | target: 50M€ [MONTHLY]
    - Metric: Market Share → basis: 15% | goal: 20% [ANNUAL]
    
    RISK MANAGEMENT
    ⚠ Risk: Increased Competition (likelihood: HIGH / impact CRITICAL)
       Solution: Differentiate with proprietary AI
    """
    
    company_data = {"name": "Apple", "rating": 4.7}
    
    result = pipeline_complet_avec_nettoyage(
        company_name="Apple",
        gemini_raw_response=gemini_sale,
        company_data=company_data,
        prompt_type="plan_action"
    )
    
    output_file = "apple_plan_demo_cleaned.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Sauvegardé dans: {output_file}")


def utiliser_dans_main():
    """
    Exemple d'utilisation dans main.py
    """
    
    print("\n" + "="*70)
    print("Exemple d'intégration dans main.py")
    print("="*70)
    
    code_example = '''
# main.py - NOUVEAU CODE avec TextCleaner

from src.serp_client import rechercher
from src.json_extractor import JSONExtractor
from src.gemini_analyzer import prompt_diagnostic, prompt_plan_action
from src.text_cleaner import TextCleaner
from src.response_formatter import ResponseFormatter
import json

def analyser_entreprise_complete(nom: str):
    """Analyser une entreprise avec nettoyage complète"""
    
    # 1. SerpAPI data (Sprint 1)
    raw_data = rechercher(nom)
    company_data = JSONExtractor().extract_company_info(raw_data, nom)
    
    # 2. Appeler Gemini diagnostic
    gemini_diagnostic_raw = prompt_diagnostic(company_data)
    
    # 3. NOUVEAU: Nettoyer + Formatter
    cleaner = TextCleaner()
    clean_result = cleaner.full_pipeline(gemini_diagnostic_raw)
    clean_text = clean_result['clean_text']
    
    formatter_diag = ResponseFormatter(nom, prompt_type="diagnostic")
    diagnostic_json = formatter_diag.format_diagnostic_response(
        clean_text, 
        company_data
    )
    
    # 4. Appeler Gemini plan
    gemini_plan_raw = prompt_plan_action(company_data)
    
    # 5. NOUVEAU: Nettoyer + Formatter
    clean_plan = cleaner.full_pipeline(gemini_plan_raw)
    formatter_plan = ResponseFormatter(nom, prompt_type="plan_action")
    plan_json = formatter_plan.format_plan_action_response(
        clean_plan['clean_text'],
        company_data
    )
    
    # 6. Valider
    is_diag_valid, _ = formatter_diag.validate_against_schema(diagnostic_json)
    is_plan_valid, _ = formatter_plan.validate_against_schema(plan_json)
    
    # 7. Fusion rapport complet
    rapport = {
        "entreprise": diagnostic_json["entreprise"],
        "diagnostic": diagnostic_json["diagnostic"],
        "plan_action": plan_json["plan_action"],
        "metadonnees": diagnostic_json["metadonnees"]
    }
    
    # 8. Sauvegarder JSON
    with open(f"data/{nom.lower()}_rapport_complet.json", "w") as f:
        json.dump(rapport, f, indent=2, ensure_ascii=False)
    
    return rapport

# Exécuter
if __name__ == "__main__":
    for entreprise in ["Samsung", "Apple", "Microsoft"]:
        analyser_entreprise_complete(entreprise)
'''
    
    print(code_example)


if __name__ == "__main__":
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║  TextCleaner + ResponseFormatter - Démos Complètes       ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    # Exécuter les démos
    demo_gemini_sale_vs_propre()
    demo_plan_action_sale()
    utiliser_dans_main()
    
    print("\n" + "="*70)
    print("✓ Démos terminées!")
    print("="*70)
