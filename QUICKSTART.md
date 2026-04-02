# ⚡ QUICK START - Utiliser ResponseFormatter en 5 min


Tu as une réponse texte de Gemini? La convertir en JSON structuré en 3 lignes:

```python
from src.response_formatter import ResponseFormatter
formatter = ResponseFormatter("NomEntreprise", prompt_type="diagnostic")
json_structure = formatter.format_diagnostic_response(gemini_texte, company_data)
```

---

## 🚀 Démarrage Rapide

### Étape 1: Copier fichiers

```bash
# Copier les classes
cp src/response_formatter.py votre_projet/
cp src/text_cleaner.py votre_projet/

# Copier le schéma (référence)
cp src/schemas/company_analysis_schema.json votre_projet/
```

### Étape 2: Importer et utiliser

```python
from response_formatter import ResponseFormatter
from text_cleaner import TextCleaner
import json

# 1. Données de l'entreprise (venant de SerpAPI)
company_data = {
    "name": "Apple Inc.",
    "address": "1 Apple Park Way",
    "rating": 4.7,
    "review_count": 2543
}

# 2. Réponse brute de Gemini (peut être sale!)
gemini_response = """
🔥 POINTS FORTS!!!
apple has strong brand (CRITICAL) and innovation (HIGH)
"""

# 3. NETTOYER (nouveau!)
cleaner = TextCleaner()
clean_result = cleaner.full_pipeline(gemini_response)
clean_text = clean_result['clean_text']
print(f"Qualité: {clean_result['quality_score']}/100")

# 4. Formatter la réponse nettoyée
formatter = ResponseFormatter("Apple", prompt_type="diagnostic")
result = formatter.format_diagnostic_response(clean_text, company_data)

# 5. Valider
is_valid, errors = formatter.validate_against_schema(result)

# 6. Sauvegarder
if is_valid:
    with open("apple_analysis.json", "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
```

### Étape 3: Valider

```python
is_valid, errors = formatter.validate_against_schema(result)
print("✓ Valide!" if is_valid else f"❌ Erreurs: {errors}")
```

---

## 📝 Structure Obtenue

Le JSON retourné contient:

```json
{
  "entreprise": {...},          // Données SerpAPI normalisées
  "diagnostic": {
    "points_forts": [...],
    "points_faibles": [...],
    "opportunites": [...]
  },
  "metadonnees": {
    "date_analyse": "2026-03-30T14:35:22Z",
    "id_analyse": "ANAL-APPLE-20260330-001"
  }
}
```

---

## 💡 Cas d'Usage Courants

### Diagnostic uniquement

```python
formatter = ResponseFormatter("Apple", prompt_type="diagnostic")
diagnostic_json = formatter.format_diagnostic_response(
    gemini_text_response, 
    company_data
)
```

### Plan d'action uniquement

```python
formatter = ResponseFormatter("Apple", prompt_type="plan_action")
plan_json = formatter.format_plan_action_response(
    gemini_text_response, 
    company_data
)
```

### Les deux (rapport complet)

```python
# 1. Diagnostic
diag_formatter = ResponseFormatter("Apple", prompt_type="diagnostic")
diag = diag_formatter.format_diagnostic_response(diag_text, company_data)

# 2. Plan
plan_formatter = ResponseFormatter("Apple", prompt_type="plan_action")
plan = plan_formatter.format_plan_action_response(plan_text, company_data)

# 3. Fusionner
rapport_complet = {
    "entreprise": diag["entreprise"],
    "diagnostic": diag["diagnostic"],
    "plan_action": plan["plan_action"],
    "metadonnees": diag["metadonnees"]
}

# 4. Sauvegarder
with open("rapport_complet.json", "w") as f:
    json.dump(rapport_complet, f, indent=2, ensure_ascii=False)
```

---

## 🔧 Configuration

### Version du modèle Gemini

```python
formatter = ResponseFormatter(
    company_name="Apple",
    model="gemini-2.0-flash",      # ← Changez si nécessaire
    version_prompt="2.1",           # ← Version du prompt
    prompt_type="diagnostic"
)
```

### Couleurs de retour (pour logs)

```python
is_valid, errors = formatter.validate_against_schema(result)

if is_valid:
    print("✅ Structure JSON valide!")
    print(f"   ID: {result['metadonnees']['id_analyse']}")
    print(f"   Points forts: {len(result['diagnostic']['points_forts'])}")
else:
    print("❌ Erreurs de validation:")
    for error in errors:
        print(f"   - {error}")
```

---

## ⚠️ Pièges Courants

### ❌ Pièges (Avant TextCleaner)

```python
# MAUVAIS: Texte brut sale (non structuré)
gemini_response = """
🔥 POINTS FORTS
apple is great and has strong brand...
"""
formatter.format_diagnostic_response(gemini_response, data)
# Résultat: Parser échoue ❌

# MAUVAIS: Oublier validation
json_result = formatter.format_diagnostic_response(text, data)
# Pas de vérification du schéma ❌
```

### ✅ Bonne Pratique (Avec TextCleaner)

```python
# BON: Nettoyer d'abord, même si texte brut!
gemini_response = """
🔥 POINTS FORTS!!!
apple has strong brand (CRITICAL) and does innovation (high)
"""

cleaner = TextCleaner()
clean_result = cleaner.full_pipeline(gemini_response)
clean_text = clean_result['clean_text']

# BON: Vérifier la qualité du nettoyage
if clean_result['quality_score'] < 50:
    print("⚠️  Qualité faible. Relancer Gemini?")

# BON: Formatter + valider
formatter = ResponseFormatter("Apple", prompt_type="diagnostic")
result = formatter.format_diagnostic_response(clean_text, company_data)
is_valid, errors = formatter.validate_against_schema(result)

if is_valid:
    print("✓ OK - Sauvegarder")
else:
    print(f"❌ Erreur: {errors}")
```

---

## 📊 Intégrer dans main.py Existant

### Avant (Sprint 1)

```python
from src.json_extractor import JSONExtractor

# Récupérer données
raw_data = rechercher("Apple")
company_data = JSONExtractor().extract_company_info(raw_data, "Apple")
```

### Après (Sprint 2)

```python
from src.json_extractor import JSONExtractor
from src.response_formatter import ResponseFormatter  # ← NEW

# Récupérer données (inchangé)
raw_data = rechercher("Apple")
company_data = JSONExtractor().extract_company_info(raw_data, "Apple")

# NEW: Formatter les réponses Gemini
gemini_diagnostic = prompt_diagnostic(company_data)      # Appel Gemini
formatter = ResponseFormatter("Apple", prompt_type="diagnostic")
diagnostic_json = formatter.format_diagnostic_response(gemini_diagnostic, company_data)

gemini_plan = prompt_plan_action(company_data)           # Appel Gemini
formatter = ResponseFormatter("Apple", prompt_type="plan_action")
plan_json = formatter.format_plan_action_response(gemini_plan, company_data)

# Sauvegarder JSON au lieu de TXT
with open(f"data/apple_diagnostic.json", "w") as f:
    json.dump(diagnostic_json, f, indent=2, ensure_ascii=False)

with open(f"data/apple_plan.json", "w") as f:
    json.dump(plan_json, f, indent=2, ensure_ascii=False)
```

---

## 🧪 Test Rapide (5 secondes)

```python
# Run test demo
python tests/test_response_formatter.py

# Voir aussi exemple:
# python tests/test_response_formatter.py --demo
```

Cela génère 2 fichiers:
- `samsung_diagnostic_demo.json`
- `microsoft_plan_action_demo.json`

Ouvrez-les pour voir la structure exacte!

---


## 🎓 Exemple Complet (Copier/Coller)

```python
"""
Exemple complet du début à la fin
"""
import json
from datetime import datetime
from src.response_formatter import ResponseFormatter

def analyze_company_complete(company_name: str):
    """Analyse complète d'une entreprise"""
    
    # 1. Données de l'entreprise (SerpAPI)
    company_data = {
        "id": "samsung_001",
        "name": "Samsung Electronics",
        "address": "129 Samsung-ro, Maetan-dong, Yeongtong-gu, Suwon",
        "phone": "+82 31-200-1114",
        "website": "https://www.samsung.com",
        "type": "Électronique",
        "rating": 4.5,
        "review_count": 1256
    }
    
    # 2. Réponse diagnostic Gemini
    diagnostic_response = """
    POINTS FORTS:
    1. Diversification produits (CRITIQUE)
       Description: Large portefeuille allant des smartphones aux semiconductors
    
    2. R&D robuste (MAJEUR)
       Description: Investissements importants en innovation
    
    POINTS FAIBLES:
    1. Marché saturé (MAJEUR)
       Description: Concurrence féroce dans le smartphone
    
    OPPORTUNITÉS:
    1. IA et IoT (TRÈS ÉLEVÉ)
       Description: Leadership dans les technologies émergentes
    """
    
    # 3. Parser diagnostic
    print(f"📊 Analyse de {company_name}...")
    formatter_diag = ResponseFormatter(company_name, prompt_type="diagnostic")
    diag_json = formatter_diag.format_diagnostic_response(diagnostic_response, company_data)
    
    # 4. Réponse plan d'action Gemini
    plan_response = """
    RÉSUMÉ EXÉCUTIF:
    Samsung doit se concentrer sur l'IA et les marchés émergents.
    
    ACTIONS COURT TERME (0-3 mois):
    1. Lancer Copilot pour PMEs (P0)
       Responsable: VP Product
       Délai: 90 jours
       Budget: 2.5M EUR
       Description: Package IA localisé
    
    ACTIONS MOYEN TERME (3-6 mois):
    1. Centre excellence IA (P1)
       Délai: 5 mois
       Budget: 5M EUR
       Description: Centre d'innovation
    
    ACTIONS LONG TERME (6-12 mois):
    1. Acquisition startup (P2)
       Description: Acquérir tech innovante
    
    KPIs:
    - Revenue IA: baseline 0, target 50M EUR (trimestriel)
    - Market share: baseline 15%, target 20% (annuel)
    
    RISQUES:
    - Concurrence accrue (Probabilité: très élevé, Impact: critique)
      Mitigation: Différenciation IA
    """
    
    # 5. Parser plan
    formatter_plan = ResponseFormatter(company_name, prompt_type="plan_action")
    plan_json = formatter_plan.format_plan_action_response(plan_response, company_data)
    
    # 6. Valider
    is_valid_diag, errors_diag = formatter_diag.validate_against_schema(diag_json)
    is_valid_plan, errors_plan = formatter_plan.validate_against_schema(plan_json)
    
    print(f"\n✓ Diagnostic: {'VALID' if is_valid_diag else 'INVALID'}")
    print(f"✓ Plan: {'VALID' if is_valid_plan else 'INVALID'}")
    
    # 7. Fusionner
    rapport = {
        "entreprise": diag_json["entreprise"],
        "diagnostic": diag_json["diagnostic"],
        "plan_action": plan_json["plan_action"],
        "metadonnees": diag_json["metadonnees"]
    }
    
    # 8. Sauvegarder
    output = f"{company_name.lower()}_rapport_complet.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(rapport, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Sauvegardé: {output}")
    print(f"✓ Points forts: {len(rapport['diagnostic']['points_forts'])}")
    print(f"✓ Actions court-terme: {len(rapport['plan_action']['court_terme'])}")
    
    return rapport


if __name__ == "__main__":
    # À exécuter!
    analyze_company_complete("Samsung")
```


