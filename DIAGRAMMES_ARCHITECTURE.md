# 🏗️ Diagrammes d'Architecture - Analyse d'Entreprises

## 1️⃣ Flux Global: SerpAPI → Gemini → JSON

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PIPELINE COMPLET D'ANALYSE                        │
└─────────────────────────────────────────────────────────────────────┘

  SPRINT 1                          SPRINT 2                    OUTPUT
┌──────────────────┐          ┌──────────────────┐         ┌──────────┐
│ Google/SerpAPI   │    →     │ Gemini Models    │   →     │  JSON    │
│                  │          │                  │         │ Structuré│
│ - Nom            │          │ Prompt 1:        │         │          │
│ - Adresse        │          │ Diagnostic       │         │ ✓ Web    │
│ - Note: 4.5/5    │          │                  │         │ ✓ PDF    │
│ - 256 avis       │          │ Prompt 2:        │         │ ✓ Excel  │
│ - Horaires       │          │ Plan action      │         │ ✓ DB     │
│ - Photos         │          │                  │         │          │
└──────────────────┘          └──────────────────┘         └──────────┘
       ↓                              ↓                           ↓
   json_extractor.py          ResponseFormatter.py      report_complet.json
   (Sprint 1)                 (Sprint 2) - NEW!         ← Produit final
```

---

## 2️⃣ Structure JSON Détaillée

```
RAPPORT D'ANALYSE COMPLET
│
├─ ENTREPRISE (Données collectées)
│  ├─ Identifiant & contact
│  │  ├─ id_entreprise
│  │  ├─ nom
│  │  ├─ adresse
│  │  ├─ telephone
│  │  └─ site_web
│  ├─ Profil
│  │  ├─ categorie
│  │  └─ horaires
│  └─ Réputation
│     ├─ note_moyenne (4.7/5)
│     ├─ nombre_avis (2543)
│     └─ photos
│
├─ DIAGNOSTIC (Analyse Gemini)
│  ├─ Points Forts ← Force Apple
│  │  ├─ "Prestige marque" [critique]
│  │  ├─ "Innovation R&D" [critique]
│  │  ├─ "Écosystème intégré" [majeur]
│  │  └─ "Rentabilité" [majeur]
│  │
│  ├─ Points Faibles ← Risques
│  │  ├─ "TSMC dependency" [majeur]
│  │     Impact: Ruptures d'approvisionnement
│  │  ├─ "Concentration géo" [modéré]
│  │  ├─ "Prix premium" [modéré]
│  │  └─ "Réparations onéreuses" [majeur]
│  │
│  └─ Opportunités ← Growth
│     ├─ "IA & ML" [très élevé]
│     ├─ "Services récurrents" [très élevé]
│     ├─ "Marchés émergents" [élevé]
│     ├─ "Batterie/Énergie" [élevé]
│     └─ "Santé & Wearables" [élevé]
│
├─ PLAN D'ACTION (Roadmap)
│  ├─ COURT TERME (0-3 mois)
│  │  ├─ Action [P0] "Chaîne appro" → 90 j → 150M EUR
│  │  ├─ Action [P0] "Apple Intelligence"
│  │  └─ Action [P1] "Politique réparation"
│  │
│  ├─ MOYEN TERME (3-6 mois)
│  │  ├─ Action [P1] "Décarbonation" → 6 mois
│  │  ├─ Action [P1] "Expansion services" → 25% revenues
│  │  └─ Action [P2] "Marchés émergents"
│  │
│  ├─ LONG TERME (6-12 mois)
│  │  ├─ Action [P1] "Leader santé digital"
│  │  ├─ Action [P2] "Batteries révolutionnaires"
│  │  └─ Action [P2] "Démocratisation accès"
│  │
│  ├─ KPIs à suivre
│  │  ├─ NPS: 72 → 80 (mensuel)
│  │  ├─ Marge brute: 46% → 48% (trim)
│  │  └─ Services revenue: 22% → 25% (trim)
│  │
│  └─ RISQUES & MITIGATIONS
│     ├─ Rupture chips [ÉLEVÉ impact: CRITIQUE]
│     ├─ Antitrust [ÉLEVÉ/ MAJEUR]
│     └─ Concurrence IA [ÉLEVÉ/MAJEUR]
│
├─ ANALYSE AVIS (Optionnel)
│  ├─ Thèmes positifs
│  │  ├─ "Qualité construction" [très fréquent]
│  │  ├─ "Design premium" [très fréquent]
│  │  └─ "Support client" [fréquent]
│  ├─ Thèmes négatifs
│  │  ├─ "Prix excessif" [très fréquent]
│  │  ├─ "Réparations chères" [fréquent]
│  │  └─ "Batterie courte" [modéré]
│  └─ Sentiment: TRÈS POSITIF
│
└─ MÉTADONNÉES (Audit & Traçabilité)
   ├─ date_analyse: 2026-03-30T14:35:22Z
   ├─ version_prompt: 2.1
   ├─ modele_gemini: gemini-2.0-flash
   ├─ temps_reponse_ms: 2847
   ├─ qualite_donnees: excellente
   └─ id_analyse: ANAL-APPLE-20260330-001 ← Unique!
```

---

## 3️⃣ Cycle de Vie d'une Analyse

```
START (Utilisateur demande analyse)
  ↓
[1] Collecter données SerpAPI
    • Scraper Google Maps
    • Récupérer avis/photos
    ↓
[2] Créer JSON structuré (Sprint 1)
    • JSONExtractor.extract_company_info()
    • Sauvegarder apple_results.json
    ↓
[3] Appeler Gemini - DIAGNOSTIC
    • Envoyer données + Prompt diagnostic
    • Reçoit: texte structuré (MD/texte)
    ↓
[4] Parser diagnostic avec ResponseFormatter
    • formatter.format_diagnostic_response()
    • Extraire: points_forts, points_faibles, opportunites
    • Valider contre schéma
    • Sauvegarder JSON
    ↓
[5] Appeler Gemini - PLAN D'ACTION
    • Envoyer données + diagnostic + Prompt plan
    • Reçoit: texte structuré
    ↓
[6] Parser plan avec ResponseFormatter
    • formatter.format_plan_action_response()
    • Extraire: court/moyen/long terme, KPIs, risques
    • Valider
    • Sauvegarder JSON
    ↓
[7] FUSION analyses
    • Combiner diagnostic + plan_action
    • Créer rapport_complet.json
    ↓
[8] EXPORT multi-format
    ├─ JSON ✓
    ├─ PDF (ReportLab)
    ├─ Excel (Pandas)
    ├─ HTML (Jinja2)
    └─ Web API (FastAPI)
    ↓
END (Rapport disponible pour consultation)
```

---

## 4️⃣ Classe ResponseFormatter - Méthodes

```
ResponseFormatter
├─ PUBLIC METHODS
│  ├─ __init__(company_name, model, version_prompt, prompt_type)
│  │
│  ├─ format_diagnostic_response(response_text, company_data)
│  │  ↓ Retourne: JSON diagnostic complet
│  │  └─ Étapes internes:
│  │     ├─ _extract_section() → points_forts
│  │     ├─ _extract_section() → points_faibles
│  │     ├─ _extract_section() → opportunites
│  │     ├─ _analyze_reviews() → analyse_avis
│  │     └─ _create_metadata()
│  │
│  ├─ format_plan_action_response(response_text, company_data)
│  │  ↓ Retourne: JSON plan d'action complet
│  │  └─ Étapes internes:
│  │     ├─ _extract_actions() → court_terme
│  │     ├─ _extract_actions() → moyen_terme
│  │     ├─ _extract_actions() → long_terme
│  │     ├─ _extract_kpis()
│  │     ├─ _extract_risques()
│  │     ├─ _extract_resume()
│  │     └─ _create_metadata()
│  │
│  └─ validate_against_schema(data, schema_path)
│     ↓ Retourne: (is_valid: bool, errors: List[str])
│
└─ PRIVATE METHODS (Parsing helpers)
   ├─ _extract_section() → Extrait une section par regex
   ├─ _extract_actions() → Parse actions structures
   ├─ _extract_kpis() → Parse KPIs (metrique, baseline, cible)
   ├─ _extract_risques() → Parse risques+mitigations
   ├─ _extract_impact() → Détermine impact (regex)
   ├─ _extract_priorite() → Extrait priorité P0-P3
   ├─ _extract_responsable() → Trouve responsable
   ├─ _split_titre_description() → Parse première ligne
   ├─ _normalize_company_data() → Mappe SerpAPI → schema
   └─ _create_metadata() → Génère métadonnées
```

---

## 5️⃣ Flux d'Intégration dans main.py

```
AVANT (Sprint 1):
main.py
  ├─ rechercher() → SerpAPI
  ├─ JSONExtractor.extract_company_info()
  ├─ save_to_json() → apple_results.json ✓
  └─ END


APRÈS (Sprint 2+) avec ResponseFormatter:
main.py
  ├─ rechercher() → SerpAPI
  ├─ JSONExtractor.extract_company_info()
  ├─ save_to_json() → apple_results.json ✓
  │
  ├─ prompt_diagnostic() → Gemini (texte brut)
  ├─ ResponseFormatter.format_diagnostic_response()
  ├─ validate_against_schema()
  ├─ save_to_json() → apple_diagnostic.json ✓ (NEW!)
  │
  ├─ prompt_plan_action() → Gemini (texte brut)
  ├─ ResponseFormatter.format_plan_action_response()
  ├─ validate_against_schema()
  ├─ save_to_json() → apple_plan_action.json ✓ (NEW!)
  │
  └─ FUSION → apple_rapport_complet.json ✓ (NEW!)
```

---

## 6️⃣ Formats d'Énumération

```
IMPACT / SEVERITE:
┌─────────────┬────────────────────────┐
│ Valeur      │ Interprétation         │
├─────────────┼────────────────────────┤
│ critique    │ 🔴 Très haute priorité │
│ majeur      │ 🟠 Haute priorité      │
│ modéré      │ 🟡 Moyenne priorité    │
│ faible      │ 🟢 Basse priorité      │
└─────────────┴────────────────────────┘

PRIORITÉ D'ACTION:
┌──────┬─────────────────────────────┐
│ Code │ Description                 │
├──────┼─────────────────────────────┤
│ P0   │ 🚨 URGENT - Faire tout de suite
│ P1   │ 🔴 Haute - Semaine 1-2
│ P2   │ 🟡 Moyenne - Mois 1-2
│ P3   │ 🟢 Basse - Peut attendre
└──────┴─────────────────────────────┘

SENTIMENT AVIS:
très positif → positif → neutre → négatif → très négatif
    😄     →    😊    →  😐  →   😞   →    😡
```

---

## 7️⃣ Cas d'Utilisation Multi-Formats

```
rapport_complet.json
│
├→ API REST (JSON directement)
│  GET /api/analysis/ANAL-APPLE-20260330-001
│  ↓ JSON
│  Client web affiche diagnostic/plan
│
├→ PDF (ReportLab)
│  $ python export_pdf.py rapport_complet.json
│  ↓ PDF téléchargeable
│  → E-mail aux stakeholders
│
├→ Excel (Pandas)
│  $ python export_excel.py rapport_complet.json
│  ↓ excel avec onglets
│  → Partage avec finance/ops
│
├→ HTML (Jinja2)
│  $ python export_html.py rapport_complet.json
│  ↓ Page web belle/interactive
│  → Site interne consultation
│
└→ Database (MongoDB)
   collection.insert_one(json_data)
   ↓ Historique analyses
   → Comparaisons temps
```

---

## 8️⃣ Validation Schéma JSON

```
Données entrantes
        ↓
ResponseFormatter.format_*_response()
        ↓
Structure JSON construite
        ↓
validate_against_schema()
        ├─ Fields requis présents? ✓
        ├─ Types corrects? (string, int, float, enum) ✓
        ├─ Enums valides? (P0, P1, critique, ...) ✓
        ├─ Arrays bien formés? ✓
        └─ Null safety? ✓
        ↓
    ✓ VALIDE        ou       ✗ ERREUR
        ↓                      ↓
   Sauvegarder          Log + correction
   Production           nécessaire
```

---

## 9️⃣ Architecture Fichiers

```
projet-pfa/
├── src/
│   ├── response_formatter.py ..................... NEW! Classe principale
│   ├── schemas/
│   │   ├── company_analysis_schema.json ......... NEW! Schema JSON
│   │   └── example_company_report.json ......... NEW! Exemple complet
│   ├── gemini_analyzer.py ...................... À modifier
│   ├── json_extractor.py ....................... Sprint 1
│   └── ...
│
├── tests/
│   └── test_response_formatter.py .............. NEW! Tests + démos
│
├── data/
│   ├── apple_results.json ....................... Sprint 1
│   ├── apple_diagnostic.json ................... NEW! Sprint 2
│   ├── apple_plan_action.json .................. NEW! Sprint 2
│   └── apple_rapport_complet.json .............. NEW! Sprint 2
│
├── ARCHITECTURE_JSON.md ......................... NEW! Doc complète (300 ln)
├── RESUME_ARCHITECTURE.md ....................... NEW! Vue d'ensemble
├── INTEG_RESPONSE_FORMATTER.md .................. NEW! Guide intégration
├── DIAGRAMMES.md (ce fichier) .................. NEW! Visuels
│
└── requirements.txt ............................ À mettre à jour
```

---

## 🔟 Checklist vs Schéma

Avant de sauvegarder, vérifier:

```python
# 1. Champs obligatoires
✓ entreprise.nom              # String, min 1 char
✓ entreprise.adresse          # String
✓ diagnostic.points_forts[]   # Array, min 1 item
✓ plan_action.court_terme[]   # Array, min 1 item
✓ metadonnees.date_analyse    # ISO8601 datetime
✓ metadonnees.id_analyse      # String, unique!

# 2. Types de données
✓ note_moyenne: 0-5 ou null   # Float | Null
✓ nombre_avis: entier ou null # Integer | Null
✓ delai_jours: entier ou null # Integer | Null
✓ budget_estime: float ou null # Number | Null

# 3. Énumérations respectées
✓ impact: "critique"|"majeur"|"modéré"|"faible"
✓ priorite: "P0"|"P1"|"P2"|"P3"
✓ severite: "critique"|"majeur"|"modéré"|"faible"
✓ frequence: "très fréquent"|"fréquent"|"modéré"|"rare"

# 4. Pas de strings vides!
✓ "titre": "Value" pas ""
✓ "theme": null vs ""
✓ "description": "Text" pas ""

# 5. Arrays correctement formés
✓ [{"titre": "...", ...}] pas [{/* champ manquant */}]
```

---

**Diagrammes créés:** 2026-03-30  
**Version:** 1.0  
**Statut:** ✅ Documentation complète
