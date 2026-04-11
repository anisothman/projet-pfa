"""
validate_json.py
================
Tâche de Nourhene – Sprint 1 : Validation finale + correction JSON
-----------------------------------------------------------------
Ce script :
  1. Charge le fichier business.json produit par l'équipe
  2. Vérifie la présence de tous les champs obligatoires
  3. Détecte les valeurs manquantes / mal formées
  4. Corrige automatiquement ce qui peut l'être
  5. Génère un rapport de validation (validation_report.json)
  6. Sauvegarde le JSON corrigé (business_clean.json)

Usage :
    python validate_json.py                        # utilise data/business.json
    python validate_json.py --input mon_fichier.json
"""

import json
import os
import sys
import argparse
from datetime import datetime

# ─────────────────────────────────────────────
# 1. CONFIGURATION – champs attendus
# ─────────────────────────────────────────────

# Champs OBLIGATOIRES (le JSON doit les contenir)
REQUIRED_FIELDS = ["name", "address", "category", "rating", "reviews_count"]

# Champs OPTIONNELS (on signale s'ils manquent, sans bloquer)
OPTIONAL_FIELDS = ["website", "phone", "hours", "reviews", "photos"]

# Valeurs par défaut pour la correction automatique
DEFAULTS = {
    "website": "Non renseigné",
    "phone": "Non renseigné",
    "hours": {},
    "reviews": [],
    "photos": [],
    "category": "Non renseigné",
}


# ─────────────────────────────────────────────
# 2. FONCTIONS DE VALIDATION
# ─────────────────────────────────────────────

def load_json(path: str) -> dict | list | None:
    """Charge un fichier JSON et renvoie son contenu, ou None si erreur."""
    if not os.path.exists(path):
        print(f"[ERREUR] Fichier introuvable : {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"[OK] Fichier chargé : {path}")
        return data
    except json.JSONDecodeError as e:
        print(f"[ERREUR] JSON invalide : {e}")
        return None


def validate_business(entry: dict, index: int = 0) -> dict:
    """
    Valide et corrige un enregistrement d'entreprise.
    Retourne un dict avec :
      - 'data'     : données corrigées
      - 'errors'   : champs obligatoires manquants
      - 'warnings' : champs optionnels manquants
      - 'fixes'    : corrections appliquées automatiquement
    """
    errors = []
    warnings = []
    fixes = []
    data = dict(entry)  # copie pour ne pas modifier l'original

    label = data.get("name", f"Entrée #{index}")

    # ── Vérification des champs obligatoires ──
    for field in REQUIRED_FIELDS:
        if field not in data or data[field] in [None, "", [], {}]:
            errors.append(f"Champ obligatoire manquant ou vide : '{field}'")

    # ── Vérification + correction des champs optionnels ──
    for field in OPTIONAL_FIELDS:
        if field not in data or data[field] in [None, "", [], {}]:
            warnings.append(f"Champ optionnel absent : '{field}'")
            if field in DEFAULTS:
                data[field] = DEFAULTS[field]
                fixes.append(f"Valeur par défaut ajoutée pour '{field}'")

    # ── Vérifications de type ──
    if "rating" in data:
        try:
            data["rating"] = float(data["rating"])
            if not (0.0 <= data["rating"] <= 5.0):
                errors.append(f"'rating' hors plage [0-5] : {data['rating']}")
        except (ValueError, TypeError):
            errors.append(f"'rating' n'est pas un nombre : {data['rating']!r}")

    if "reviews_count" in data:
        try:
            data["reviews_count"] = int(data["reviews_count"])
        except (ValueError, TypeError):
            errors.append(f"'reviews_count' n'est pas un entier : {data['reviews_count']!r}")

    if "reviews" in data and not isinstance(data["reviews"], list):
        errors.append("'reviews' doit être une liste")
        data["reviews"] = []
        fixes.append("'reviews' réinitialisé en liste vide")

    if "photos" in data and not isinstance(data["photos"], list):
        errors.append("'photos' doit être une liste")
        data["photos"] = []
        fixes.append("'photos' réinitialisé en liste vide")

    # ── Nettoyage des espaces dans les champs texte ──
    for field in ["name", "address", "category", "website", "phone"]:
        if field in data and isinstance(data[field], str):
            stripped = data[field].strip()
            if stripped != data[field]:
                data[field] = stripped
                fixes.append(f"Espaces supprimés dans '{field}'")

    status = "VALIDE" if not errors else "INVALIDE"

    return {
        "label": label,
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "fixes": fixes,
        "data": data,
    }


def validate_all(raw: dict | list) -> tuple[list, list]:
    """
    Accepte un objet unique ou une liste d'entreprises.
    Retourne (résultats_validation, données_corrigées).
    """
    if isinstance(raw, dict):
        entries = [raw]
    elif isinstance(raw, list):
        entries = raw
    else:
        print("[ERREUR] Format JSON inattendu (ni objet ni liste)")
        return [], []

    results = []
    cleaned = []
    for i, entry in enumerate(entries):
        result = validate_business(entry, index=i)
        results.append(result)
        cleaned.append(result["data"])

    return results, cleaned


# ─────────────────────────────────────────────
# 3. AFFICHAGE DU RAPPORT DANS LE TERMINAL
# ─────────────────────────────────────────────

def print_report(results: list):
    print("\n" + "=" * 60)
    print("        RAPPORT DE VALIDATION JSON")
    print("=" * 60)

    total = len(results)
    valid = sum(1 for r in results if r["status"] == "VALIDE")
    invalid = total - valid

    print(f"  Entreprises analysées : {total}")
    print(f"  ✅ Valides            : {valid}")
    print(f"  ❌ Invalides          : {invalid}")
    print("=" * 60)

    for r in results:
        icon = "✅" if r["status"] == "VALIDE" else "❌"
        print(f"\n{icon}  {r['label']}  [{r['status']}]")

        if r["errors"]:
            print("   ERREURS :")
            for e in r["errors"]:
                print(f"     ✗  {e}")

        if r["warnings"]:
            print("   AVERTISSEMENTS :")
            for w in r["warnings"]:
                print(f"     ⚠  {w}")

        if r["fixes"]:
            print("   CORRECTIONS APPLIQUÉES :")
            for f in r["fixes"]:
                print(f"     🔧 {f}")

    print("\n" + "=" * 60)


# ─────────────────────────────────────────────
# 4. SAUVEGARDE DES FICHIERS DE SORTIE
# ─────────────────────────────────────────────

def save_outputs(results: list, cleaned: list, output_dir: str = "data"):
    os.makedirs(output_dir, exist_ok=True)

    # ── business_clean.json ──
    clean_path = os.path.join(output_dir, "business_clean.json")
    output_data = cleaned[0] if len(cleaned) == 1 else cleaned
    with open(clean_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"\n[SAUVEGARDÉ] Données corrigées → {clean_path}")

    # ── validation_report.json ──
    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total": len(results),
            "valid": sum(1 for r in results if r["status"] == "VALIDE"),
            "invalid": sum(1 for r in results if r["status"] == "INVALIDE"),
        },
        "details": [
            {
                "label": r["label"],
                "status": r["status"],
                "errors": r["errors"],
                "warnings": r["warnings"],
                "fixes": r["fixes"],
            }
            for r in results
        ],
    }
    report_path = os.path.join(output_dir, "validation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"[SAUVEGARDÉ] Rapport de validation → {report_path}")


# ─────────────────────────────────────────────
# 5. GÉNÉRATION D'UN JSON EXEMPLE (pour tester)
# ─────────────────────────────────────────────

EXAMPLE_JSON = [
    {
        "name": "Café Central",
        "address": "12 Avenue Habib Bourguiba, Tunis",
        "category": "Café / Restaurant",
        "rating": "4.3",
        "reviews_count": "128",
        "website": "https://cafecentral.tn",
        "phone": "+216 71 000 111",
        "hours": {
            "lundi": "08:00-22:00",
            "mardi": "08:00-22:00",
            "mercredi": "08:00-22:00",
            "jeudi": "08:00-22:00",
            "vendredi": "08:00-23:00",
            "samedi": "09:00-23:00",
            "dimanche": "Fermé"
        },
        "reviews": [
            {"author": "Ali", "rating": 5, "text": "Excellent café, service rapide !"},
            {"author": "Sara", "rating": 4, "text": "Bon endroit, un peu bruyant."}
        ],
        "photos": ["photo1.jpg", "photo2.jpg"]
    },
    {
        "name": "  Pharmacie El Amal  ",
        "address": "",
        "category": None,
        "rating": "6.0",
        "reviews_count": "not_a_number",
        "website": "",
        "phone": "+216 71 999 888"
    },
    {
        "name": "Salon Nour",
        "address": "Rue de la Liberté, Sfax",
        "category": "Coiffure / Beauté",
        "rating": 4.7,
        "reviews_count": 55
    }
]


def create_example_file(path: str):
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(EXAMPLE_JSON, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Fichier exemple créé : {path}")


# ─────────────────────────────────────────────
# 6. POINT D'ENTRÉE
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Validation + correction du fichier business.json")
    parser.add_argument("--input", default="data/business.json", help="Chemin vers le JSON à valider")
    parser.add_argument("--output-dir", default="data", help="Dossier de sortie (défaut: data/)")
    parser.add_argument("--create-example", action="store_true", help="Créer un fichier exemple pour tester")
    args = parser.parse_args()

    input_path = args.input

    # Créer un exemple si demandé OU si le fichier n'existe pas encore
    if args.create_example or not os.path.exists(input_path):
        print(f"[INFO] Fichier '{input_path}' absent → création d'un exemple de test.")
        create_example_file(input_path)

    # Charger le JSON
    raw = load_json(input_path)
    if raw is None:
        sys.exit(1)

    # Valider et corriger
    results, cleaned = validate_all(raw)
    if not results:
        sys.exit(1)

    # Afficher le rapport dans le terminal
    print_report(results)

    # Sauvegarder les fichiers de sortie
    save_outputs(results, cleaned, output_dir=args.output_dir)

    # Code de retour : 0 si tout est valide, 1 sinon
    all_valid = all(r["status"] == "VALIDE" for r in results)
    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
