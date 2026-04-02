# Architecture JSON Standardisée - Analyse d'Entreprises

## 📋 Vue d'ensemble

Cette documentation décrit la structure JSON standardisée pour organiser les réponses de l'API Gemini dans le cadre de l'analyse de fiches d'entreprises Google.

**Contexte du projet:**
- Collecte de données via SerpAPI (nom, adresse, catégorie, note, avis, photos)
- Envoi à Gemini avec 2 prompts: Diagnostic + Plan d'action
- Besoin de JSON structuré pour affichage web et génération PDF

---

## 🏗️ Structure Principale

```
{
  "entreprise": {},           // Données collectées (SerpAPI)
  "diagnostic": {},           // Analyse diagnostic (Gemini)
  "plan_action": {},          // Plan d'action (Gemini)
  "analyse_avis": {},         // Analyse qualitative (optionnel)
  "metadonnees": {}           // Infos techniques
}
```

---

## 1️⃣ Section `entreprise`

**Rôle:** Contient les données brutes collectées via SerpAPI

```json
{
  "entreprise": {
    "id_entreprise": "apple_cupertino_001",
    "nom": "Apple Inc.",
    "adresse": "1 Apple Park Way, Cupertino, CA 95014",
    "telephone": "+1 (408) 996-1010",
    "site_web": "https://www.apple.com",
    "categorie": "Électronique - Technologie",
    "horaires": {
      "lundi": "9h00 - 17h00",
      "samedi": "10h00 - 16h00"
    },
    "note_moyenne": 4.7,
    "nombre_avis": 2543,
    "photos": ["url1", "url2"]
  }
}
```

**Champs clés:**
- `id_entreprise`: Identifiant unique (hash ou SERP ID)
- `nom`: Nom officiel
- `note_moyenne`: 0-5 (peut être null)
- `nombre_avis`: Nombre total (peut être null)

---

## 2️⃣ Section `diagnostic`

**Rôle:** Organise l'analyse diagnostic en 3 sous-sections

### Structure
```json
{
  "diagnostic": {
    "points_forts": [...],
    "points_faibles": [...],
    "opportunites": [...]
  }
}
```

### Format de chaque item

**Points forts:**
```json
{
  "titre": "Prestige et valeur de marque",
  "description": "Apple a une loyauté client...",
  "impact": "critique"  // "critique", "majeur", "modéré", "faible"
}
```

**Points faibles:**
```json
{
  "titre": "Dépendance aux fournisseurs",
  "description": "TSMC concentre la production...",
  "severite": "majeur",
  "impact_client": "Risque de délais de livraison"
}
```

**Opportunités:**
```json
{
  "titre": "Expansion IA et ML",
  "description": "Intégration d'IA avancée...",
  "potentiel": "très élevé"  // "très élevé", "élevé", "modéré", "faible"
}
```

---

## 3️⃣ Section `plan_action`

**Rôle:** Organise les actions par horizon temporel

### Structure globale
```json
{
  "plan_action": {
    "resume_executif": "Apple doit maintenir...",
    "court_terme": [...],      // 0-3 mois
    "moyen_terme": [...],      // 3-6 mois
    "long_terme": [...],       // 6-12 mois
    "kpis": [...],
    "risques": [...]
  }
}
```

### Actions court/moyen/long terme

```json
{
  "action": "Renforcer la chaîne d'approvisionnement",
  "description": "Mettre en place des contrats multi-fournisseurs...",
  "priorite": "P0",              // P0 (critique), P1, P2, P3
  "responsable": "VP Operations",
  "delai_jours": 90,             // court terme
  "budget_estime": 150000000
}
```

### KPIs
```json
{
  "metrique": "Satisfaction client (NPS)",
  "baseline": 72,
  "cible": 80,
  "frequence_mesure": "mensuel"
}
```

### Risques
```json
{
  "risque": "Ruptures d'approvisionnement",
  "probabilite": "modéré",
  "impact": "critique",
  "mitigation": "Contrats long-terme multi-fournisseurs..."
}
```

---

## 4️⃣ Section `analyse_avis` (optionnelle)

**Rôle:** Analyse qualitative que les avis clients

```json
{
  "analyse_avis": {
    "themes_positifs": [
      {
        "theme": "Qualité de construction",
        "frequence": "très fréquent",
        "exemple": "Le matériel dure longtemps"
      }
    ],
    "themes_negatifs": [
      {
        "theme": "Prix excessif",
        "frequence": "très fréquent"
      }
    ],
    "sentiment_general": "très positif"  // très positif, positif, neutre, négatif
  }
}
```

---

## 5️⃣ Section `metadonnees`

**Rôle:** Traçabilité technique et audit

```json
{
  "metadonnees": {
    "date_analyse": "2026-03-30T14:35:22Z",
    "version_prompt": "2.1",
    "modele_gemini": "gemini-2.0-flash",
    "temps_reponse_ms": 2847,
    "langue": "fr",
    "qualite_donnees": "excellente",
    "id_analyse": "ANAL-APPLE-20260330-001"
  }
}
```

**Champs:**
- `date_analyse`: ISO 8601 pour traçabilité
- `version_prompt`: Permet de suivre les évolutions du prompt
- `temps_reponse_ms`: Important pour optimisation costs
- `id_analyse`: Unique identifier pour retrouver l'analyse

---

## 🔧 Utilisation du ResponseFormatter

### Installation

```python
from src.response_formatter import ResponseFormatter
import json
```

### Exemple: Diagnostic

```python
# Données de l'entreprise (provenant de SerpAPI)
company_data = {
    "id": "apple_001",
    "name": "Apple Inc.",
    "address": "1 Apple Park Way",
    "rating": 4.7,
    "review_count": 2543
}

# Réponse texte de Gemini
gemini_response = """
POINTS FORTS:
1. Prestige et valeur de marque exceptionnelle (critique)
   Apple jouit d'une reconnaissance mondiale...

POINTS FAIBLES:
1. Dépendance aux services externes (majeur)
   ...

OPPORTUNITÉS:
1. Expansion dans l'IA et ML (très élevé)
   ...
"""

# Formatter la réponse
formatter = ResponseFormatter(company_name="Apple", version_prompt="2.1")
structured_response = formatter.format_diagnostic_response(gemini_response, company_data)

# Valider
is_valid, errors = formatter.validate_against_schema(structured_response)
if is_valid:
    print("✓ Structure valide!")
    
    # Sauvegarder
    with open("apple_analysis.json", "w") as f:
        json.dump(structured_response, f, indent=2, ensure_ascii=False)
```

### Exemple: Plan d'action

```python
formatter = ResponseFormatter(company_name="Apple", prompt_type="plan_action")
plan = formatter.format_plan_action_response(gemini_response, company_data)
```

---

## ✅ Validation & Qualité

### Schéma JSON
- Fichier: `src/schemas/company_analysis_schema.json`
- Validation avec JSON Schema Draft 7
- Champs requis vs optionnels clairement définis

### Checklists avant sauvegarde

```python
# 1. Tous les champs requis présents
required = ["entreprise", "diagnostic", "plan_action", "metadonnees"]

# 2. Types de données corrects
# - notes_moyenne: float 0-5 ou null
# - nombre_avis: integer ou null

# 3. Enums respectés
impacts = ["critique", "majeur", "modéré", "faible"]
priorites = ["P0", "P1", "P2", "P3"]

# 4. Pas de strings vides (utiliser null)
```

---

## 📊 Cas d'usage: Génération PDF

```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

def generate_pdf_report(json_data, output_path):
    """Génère un PDF à partir du JSON structuré"""
    
    # Titre
    title = f"Rapport d'Analyse - {json_data['entreprise']['nom']}"
    
    # Diagnostic
    for point in json_data['diagnostic']['points_forts']:
        add_section(f"✓ {point['titre']}", point['description'])
    
    # Plan d'action
    for action in json_data['plan_action']['court_terme']:
        add_action(action['action'], action['description'], action['priorite'])
    
    # Métadonnées
    add_footer(json_data['metadonnees']['id_analyse'])
```

---

## 🌐 Cas d'usage: Interface Web

```javascript
// React/Vue component
async function loadAnalysis(companyId) {
    const response = await fetch(`/api/analysis/${companyId}`);
    const data = await response.json();
    
    // Afficher entreprise
    displayCompany(data.entreprise);
    
    // Afficher diagnostic
    displayDiagnostic(data.diagnostic);
    
    // Afficher plan d'action
    displayPlanAction(data.plan_action);
    
    // Indicateurs de qualité
    displayMetadata(data.metadonnees);
}
```

---

## 🔄 Scalabilité & Évolutions Futures

### Ajouter une nouvelle section

Exemple: Section "Benchmark Compétitif"

```json
{
  "benchmark": {
    "concurrents": ["Google", "Samsung", "Microsoft"],
    "postes_marche": {
      "Apple": "1er (45%)",
      "Google": "2eme (30%)"
    },
    "forces_relatives": [...]
  }
}
```

**Étapes:**
1. Ajouter au JSON Schema
2. Ajouter method `_extract_benchmark()` dans ResponseFormatter
3. Ajouter à la validation
4. Mettre à jour la version du prompt

---

## 📝 Checklist Intégration

- [ ] Copier `src/schemas/company_analysis_schema.json`
- [ ] Copier `src/response_formatter.py`
- [ ] Importer ResponseFormatter dans `gemini_analyzer.py`
- [ ] Remplacer les sauvegarde .txt par JSON
- [ ] Ajouter validation avant sauvegarde
- [ ] Tester avec données réelles
- [ ] Mettre à jour les prompts Gemini pour meilleur parsing
- [ ] Ajouter logging pour chaque analyse

---

## 📚 Fichiers de référence

- **Schema JSON:** `src/schemas/company_analysis_schema.json`
- **Exemple complet:** `src/schemas/example_company_report.json`
- **Classe Formatter:** `src/response_formatter.py`
- **Tests:** `tests/test_response_formatter.py` (à créer)

---

## ❓ Questions Fréquentes

**Q: Que faire si un champ est manquant?**
R: Utiliser `null` plutôt qu'une chaîne vide. Voir le schéma pour les champs optionnels.

**Q: Comment versioner les changements de prompts?**
R: Utiliser `version_prompt` (ex: 1.0 → 2.0). Consulter l'historique via `metadonnees.id_analyse`.

**Q: Comment stocker les analyses en base de données?**
R: Le JSON est directement stockable dans MongoDB, ou convertissable en SQL avec une clé `id_analyse`.

**Q: Comment améliorer les extractions texte?**
R: Enrichir les patterns regex dans ResponseFormatter, ou utiliser LLMs plus puissants pour le parsing.

---

**Document créé:** 2026-03-30  
**Version:** 1.0  
**Auteur:** Architecture Data & IA
