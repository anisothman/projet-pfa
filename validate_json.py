"""
validate_json.py
================
Tâche de Nourhene – Sprint 1 : Validation finale + correction JSON
CORRECTION A2 – Sprint 2+: Validation renforcée avec regex patterns
-----------------------------------------------------------------
Ce script :
  1. Charge le fichier business.json produit par l'équipe
  2. Vérifie la présence de tous les champs obligatoires
  3. Détecte les valeurs manquantes / mal formées
  4. Corrige automatiquement ce qui peut l'être
  5. Génère un rapport de validation (validation_report.json)
  6. Sauvegarde le JSON corrigé (business_clean.json)

AMÉLIORATIONS A2:
  - Validation des formats (URL, téléphone)
  - Validation des longueurs minimales/maximales
  - Vérification des types stricts
  - Patterns regex pour les données structurées

Usage :
    python validate_json.py                        # utilise data/business.json
    python validate_json.py --input mon_fichier.json
"""

import json
import os
import sys
import argparse
import re
from datetime import datetime
from typing import Dict, List, Tuple, Any


# Écrire (pour compatibilité Python < 3.7) :
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ─────────────────────────────────────────────────────────────
# 1. CONFIGURATION – champs attendus et validations (A2)
# ─────────────────────────────────────────────────────────────

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

# ══════════════════════════════════════════════════════════════
# VALIDATEURS PAR TYPE DE CHAMP (NOUVEAU! - A2)
# ══════════════════════════════════════════════════════════════
FIELD_VALIDATORS = {
    "name": {
        "type": "string",
        "min_length": 3,
        "max_length": 255,
        "required": True,
        "description": "Nom de l'entreprise",
    },
    "address": {
        "type": "string",
        "min_length": 5,
        "max_length": 500,
        "required": True,
        "description": "Adresse complète",
    },
    "category": {
        "type": "string",
        "min_length": 2,
        "max_length": 100,
        "required": True,
        "description": "Catégorie d'activité",
    },
    "rating": {
        "type": "float",
        "min": 0.0,
        "max": 5.0,
        "required": True,
        "description": "Note Google (0-5)",
    },
    "reviews_count": {
        "type": "int",
        "min": 0,
        "required": True,
        "description": "Nombre d'avis",
    },
    "website": {
        "type": "string",
        "pattern": r"^https?://[^\s]+$",
        "required": False,
        "description": "URL du site web",
    },
    "phone": {
        "type": "string",
        "pattern": r"^\+?[\d\s\-()]{8,}$",
        "required": False,
        "description": "Numéro de téléphone",
    },
}

# Patterns regex réutilisables (A2)
PATTERNS = {
    "url": r"^https?://[^\s]+$",
    "phone": r"^\+?[\d\s\-()]{8,}$",
    "email": r"^[^\s@]+@[^\s@]+\.[^\s@]+$",
}


# ─────────────────────────────────────────────────────────────
# 2. FONCTIONS DE VALIDATION (A2 - RENFORCÉE)
# ─────────────────────────────────────────────────────────────

def load_json(path: str) -> Dict | List | None:
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


def validate_string_length(
    value: str, field_name: str, min_length: int = None, max_length: int = None
) -> List[str]:
    """
    Valide la longueur d'une chaîne de caractères (A2).
    Retourne une liste d'erreurs (vide si valide).
    """
    errors = []

    if not isinstance(value, str):
        errors.append(
            f"'{field_name}' doit être une chaîne, reçu {type(value).__name__}"
        )
        return errors

    value_length = len(value.strip())

    if min_length is not None and value_length < min_length:
        errors.append(
            f"'{field_name}' trop court ({value_length} < {min_length} caractères): {value!r}"
        )

    if max_length is not None and value_length > max_length:
        errors.append(
            f"'{field_name}' trop long ({value_length} > {max_length} caractères)"
        )

    return errors


def validate_pattern(value: str, field_name: str, pattern: str) -> List[str]:
    """
    Valide qu'une chaîne correspond à un pattern regex (A2).
    Retourne une liste d'erreurs.
    """
    errors = []

    if not isinstance(value, str):
        errors.append(f"'{field_name}' doit être une chaîne")
        return errors

    if not re.match(pattern, value):
        errors.append(
            f"'{field_name}' n'a pas le bon format: {value!r} (pattern: {pattern})"
        )

    return errors


def validate_number_range(
    value: Any,
    field_name: str,
    min_val: float = None,
    max_val: float = None,
    value_type: str = "float",
) -> List[str]:
    """
    Valide qu'un nombre est dans une plage (A2).
    Retourne une liste d'erreurs.
    """
    errors = []

    try:
        if value_type == "float":
            converted = float(value)
        else:
            converted = int(value)
    except (ValueError, TypeError):
        errors.append(f"'{field_name}' n'est pas un {value_type}: {value!r}")
        return errors

    if min_val is not None and converted < min_val:
        errors.append(
            f"'{field_name}' en dessous du minimum ({converted} < {min_val}): {value!r}"
        )

    if max_val is not None and converted > max_val:
        errors.append(
            f"'{field_name}' au-dessus du maximum ({converted} > {max_val}): {value!r}"
        )

    return errors


def validate_business(entry: dict, index: int = 0) -> dict:
    """
    Valide et corrige un enregistrement d'entreprise (A2 - AMÉLIORÉ).
    Retourne un dict avec :
      - 'data'     : données corrigées
      - 'errors'   : champs obligatoires manquants ou invalides
      - 'warnings' : champs optionnels manquants
      - 'fixes'    : corrections appliquées automatiquement
    """
    errors = []
    warnings = []
    fixes = []
    data = dict(entry)  # copie pour ne pas modifier l'original

    label = data.get("name", f"Entrée #{index}")

    # ══════════════════════════════════════════════════════════════
    # 1. VÉRIFICATION DES CHAMPS OBLIGATOIRES
    # ══════════════════════════════════════════════════════════════
    for field in REQUIRED_FIELDS:
        if field not in data or data[field] in [None, "", [], {}]:
            errors.append(f"Champ obligatoire manquant ou vide : '{field}'")

    # ══════════════════════════════════════════════════════════════
    # 2. VÉRIFICATION + CORRECTION DES CHAMPS OPTIONNELS
    # ══════════════════════════════════════════════════════════════
    for field in OPTIONAL_FIELDS:
        if field not in data or data[field] in [None, "", [], {}]:
            warnings.append(f"Champ optionnel absent : '{field}'")
            if field in DEFAULTS:
                data[field] = DEFAULTS[field]
                fixes.append(f"Valeur par défaut ajoutée pour '{field}'")

    # ══════════════════════════════════════════════════════════════
    # 3. VALIDATION DES TYPES ET VALEURS (A2 - RENFORCÉE!)
    # ══════════════════════════════════════════════════════════════

    # ── Rating: float 0-5 ──
    if "rating" in data and data["rating"] not in [None, "", [], {}]:
        range_errors = validate_number_range(
            data["rating"], "rating", min_val=0.0, max_val=5.0, value_type="float"
        )
        if range_errors:
            errors.extend(range_errors)
        else:
            # Conversion réussie
            data["rating"] = float(data["rating"])

    # ── Reviews_count: int >= 0 ──
    if "reviews_count" in data and data["reviews_count"] not in [None, "", [], {}]:
        range_errors = validate_number_range(
            data["reviews_count"], "reviews_count", min_val=0, value_type="int"
        )
        if range_errors:
            errors.extend(range_errors)
        else:
            # Conversion réussie
            data["reviews_count"] = int(data["reviews_count"])

    # ── Reviews: doit être une liste ──
    if "reviews" in data and not isinstance(data["reviews"], list):
        errors.append(
            f"'reviews' doit être une liste, reçu {type(data['reviews']).__name__}"
        )
        data["reviews"] = []
        fixes.append("'reviews' réinitialisé en liste vide")

    # ── Photos: doit être une liste ──
    if "photos" in data and not isinstance(data["photos"], list):
        errors.append(
            f"'photos' doit être une liste, reçu {type(data['photos']).__name__}"
        )
        data["photos"] = []
        fixes.append("'photos' réinitialisé en liste vide")

    # ── Hours: doit être un dict ──
    if "hours" in data and not isinstance(data["hours"], dict):
        errors.append(
            f"'hours' doit être un dictionnaire, reçu {type(data['hours']).__name__}"
        )
        data["hours"] = {}
        fixes.append("'hours' réinitialisé en dict vide")

    # ══════════════════════════════════════════════════════════════
    # 4. VALIDATION DES LONGUEURS (A2 - NOUVEAU!)
    # ══════════════════════════════════════════════════════════════
    for field in ["name", "address", "category"]:
        if field in data and isinstance(data[field], str):
            length_errors = validate_string_length(
                data[field],
                field,
                min_length=FIELD_VALIDATORS[field].get("min_length"),
                max_length=FIELD_VALIDATORS[field].get("max_length"),
            )
            errors.extend(length_errors)

    # ══════════════════════════════════════════════════════════════
    # 5. VALIDATION DES FORMATS (A2 - NOUVEAU!)
    # ══════════════════════════════════════════════════════════════

    # ── Website: vérifier format URL ──
    if "website" in data and data["website"] and data["website"] != "Non renseigné":
        pattern_errors = validate_pattern(data["website"], "website", PATTERNS["url"])
        if pattern_errors:
            warnings.extend(pattern_errors)

    # ── Phone: vérifier format téléphone ──
    if "phone" in data and data["phone"] and data["phone"] != "Non renseigné":
        pattern_errors = validate_pattern(data["phone"], "phone", PATTERNS["phone"])
        if pattern_errors:
            warnings.extend(pattern_errors)

    # ══════════════════════════════════════════════════════════════
    # 6. NETTOYAGE DES ESPACES
    # ══════════════════════════════════════════════════════════════
    for field in ["name", "address", "category", "website", "phone"]:
        if field in data and isinstance(data[field], str):
            stripped = data[field].strip()
            if stripped != data[field]:
                data[field] = stripped
                fixes.append(f"Espaces supprimés dans '{field}'")

    # ══════════════════════════════════════════════════════════════
    # 7. STATUT FINAL
    # ══════════════════════════════════════════════════════════════
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


# ─────────────────────────────────────────────────────────────
# 3. AFFICHAGE DU RAPPORT DANS LE TERMINAL
# ─────────────────────────────────────────────────────────────


def print_report(results: list):
    """Affiche un rapport détaillé de la validation"""
    print("\n" + "=" * 80)
    print("        RAPPORT DE VALIDATION JSON - A2 (RENFORCÉ)")
    print("=" * 80)

    total = len(results)
    valid = sum(1 for r in results if r["status"] == "VALIDE")
    invalid = total - valid

    print(f"\n   📊 RÉSUMÉ:")
    print(f"     • Entreprises analysées : {total}")
    print(f"     • ✅ Valides            : {valid}")
    print(f"     • ❌ Invalides          : {invalid}")
    print("=" * 80)

    for r in results:
        icon = "✅" if r["status"] == "VALIDE" else "❌"
        print(f"\n{icon}  {r['label']}  [{r['status']}]")

        if r["errors"]:
            print(f"   🚨 ERREURS ({len(r['errors'])}):")
            for e in r["errors"]:
                print(f"     ✗  {e}")

        if r["warnings"]:
            print(f"   ⚠️  AVERTISSEMENTS ({len(r['warnings'])}):")
            for w in r["warnings"]:
                print(f"     ⚠  {w}")

        if r["fixes"]:
            print(f"   🔧 CORRECTIONS APPLIQUÉES ({len(r['fixes'])}):")
            for f in r["fixes"]:
                print(f"     ✓  {f}")

    print("\n" + "=" * 80)


# ─────────────────────────────────────────────────────────────
# 4. SAUVEGARDE DES FICHIERS DE SORTIE
# ─────────────────────────────────────────────────────────────


def save_outputs(results: list, cleaned: list, output_dir: str = "data"):
    """Sauvegarde les fichiers de sortie validés et rapport"""
    os.makedirs(output_dir, exist_ok=True)

    # ── business_clean.json ──
    clean_path = os.path.join(output_dir, "business_clean.json")
    output_data = cleaned[0] if len(cleaned) == 1 else cleaned
    with open(clean_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"\n[✅ SAUVEGARDÉ] Données corrigées → {clean_path}")

    # ── validation_report.json ──
    report = {
        "generated_at": datetime.now().isoformat(),
        "version": "2.0 (A2 - Renforcée)",
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
    print(f"[✅ SAUVEGARDÉ] Rapport de validation → {report_path}")


# ─────────────────────────────────────────────────────────────
# 5. GÉNÉRATION D'UN JSON EXEMPLE (pour tester)
# ─────────────────────────────────────────────────────────────

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
            "dimanche": "Fermé",
        },
        "reviews": [
            {"author": "Ali", "rating": 5, "text": "Excellent café, service rapide !"},
            {"author": "Sara", "rating": 4, "text": "Bon endroit, un peu bruyant."},
        ],
        "photos": ["photo1.jpg", "photo2.jpg"],
    },
    {
        "name": "  Pharmacie El Amal  ",
        "address": "",
        "category": None,
        "rating": "6.0",
        "reviews_count": "not_a_number",
        "website": "invalid-url",
        "phone": "+216 71 999 888",
    },
    {
        "name": "Salon Nour",
        "address": "Rue de la Liberté, Sfax",
        "category": "Coiffure / Beauté",
        "rating": 4.7,
        "reviews_count": 55,
    },
]


def create_example_file(path: str):
    """Crée un fichier exemple pour tester"""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(EXAMPLE_JSON, f, ensure_ascii=False, indent=2)
    print(f"[  INFO] Fichier exemple créé : {path}")


# ─────────────────────────────────────────────────────────────
# 6. POINT D'ENTRÉE
# ─────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Validation + correction du fichier business.json (A2 - Renforcée)"
    )
    parser.add_argument(
        "--input", default="data/business.json", help="Chemin vers le JSON à valider"
    )
    parser.add_argument(
        "--output-dir", default="data", help="Dossier de sortie (défaut: data/)"
    )
    parser.add_argument(
        "--create-example",
        action="store_true",
        help="Créer un fichier exemple pour tester",
    )
    args = parser.parse_args()

    input_path = args.input

    # Créer un exemple si demandé OU si le fichier n'existe pas encore
    if args.create_example or not os.path.exists(input_path):
        print(
            f"[ INFO] Fichier '{input_path}' absent → création d'un exemple de test."
        )
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

    # Compter les résultats
    total = len(results)
    valid_count = sum(1 for r in results if r["status"] == "VALIDE")
    invalid_count = total - valid_count

    if all_valid:
        print(f"\n SUCCÈS: Tous les {total} enregistrements sont valides!")
        sys.exit(0)
    else:
        print(
            f"\n RÉSUMÉ FINAL: {valid_count}/{total} valides, {invalid_count} invalides"
        )
        if invalid_count > 0:
            print(" Certains enregistrements nécessitent correction")
        sys.exit(1)


if __name__ == "__main__":
    main()