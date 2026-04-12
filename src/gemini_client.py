"""
╔══════════════════════════════════════════════════════════════╗
║  gemini_client.py — Sprint 2 : Intégration API Groq/Llama   ║
║  Responsable : Anis                                          ║
║  Modèle      : llama-3.3-70b (+ fallback chain) via Groq    ║
╚══════════════════════════════════════════════════════════════╝

Ce module est le point d'entrée UNIQUE pour tout appel LLM.
Tous les autres modules (gemini_analyzer, diagnostic_engine) passent
obligatoirement par call_gemini() défini ici.

Fonctionnalités :
  ✓ Initialisation sécurisée du client (clé depuis .env)
  ✓ Cache mémoire  → évite les appels redondants
  ✓ Fallback automatique vers modèles alternatifs
  ✓ Logging structuré de chaque appel
  ✓ Compteur d'appels pour contrôle de quota
"""

import os
import logging
import hashlib
from dotenv import load_dotenv
from groq import Groq

# ── Charger .env ───────────────────────────────────────────────────────────────
load_dotenv()

logger = logging.getLogger("projet-pfa")

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DES MODÈLES
# Chaîne de fallback : si le premier dépasse son quota → on essaie le suivant
# Tous sont gratuits sur Groq free tier
# ══════════════════════════════════════════════════════════════════════════════
FALLBACK_MODELS = [
    "llama-3.3-70b-versatile",    # Modèle principal — puissant et rapide
    "llama-3.1-8b-instant",       # Fallback 1 — très rapide
    "gemma2-9b-it",               # Fallback 2 — dernier recours
]

# ══════════════════════════════════════════════════════════════════════════════
# CACHE MÉMOIRE
# ══════════════════════════════════════════════════════════════════════════════
_CACHE: dict[str, str] = {}
_CALL_STATS = {"total": 0, "cache_hits": 0, "quota_errors": 0, "success": 0}


def _make_cache_key(model: str, prompt: str) -> str:
    """Génère une clé de cache unique pour un couple (model, prompt)."""
    return hashlib.md5(f"{model}:{prompt}".encode("utf-8")).hexdigest()


def get_client() -> Groq:
    """
    Crée et retourne un client Groq initialisé.
    La clé API est lue depuis la variable d'environnement GROQ_API_KEY.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY introuvable.\n"
            "Ajoutez GROQ_API_KEY=gsk_... dans votre fichier .env\n"
            "Créez une clé sur https://console.groq.com/keys"
        )
    return Groq(api_key=api_key)


# ══════════════════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE : call_gemini()
# Interface identique à l'ancienne version — aucun autre fichier à modifier
# ══════════════════════════════════════════════════════════════════════════════
def call_gemini(
    prompt: str,
    model: str = FALLBACK_MODELS[0],
    max_retries: int = 1,
    base_delay: float = 5.0,
    use_cache: bool = True,
) -> str:
    """
    Appelle l'API Groq avec gestion complète des erreurs et du quota.

    Mécanismes intégrés :
      1. Cache : prompt déjà envoyé → réponse immédiate sans appel API
      2. Fallback : quota épuisé sur un modèle → essai du modèle suivant

    Args:
        prompt      : Le texte du prompt à envoyer
        model       : Modèle préféré (défaut : llama-3.3-70b-versatile)
        max_retries : Nombre de tentatives par modèle avant fallback
        base_delay  : Délai de base en secondes (gardé pour compatibilité)
        use_cache   : Utiliser le cache mémoire (True recommandé)

    Returns:
        Réponse textuelle du modèle

    Raises:
        RuntimeError : Si tous les modèles ont épuisé leur quota
    """
    _CALL_STATS["total"] += 1

    # ── 1. Vérification du cache ───────────────────────────────────────────
    cache_key = _make_cache_key(model, prompt)
    if use_cache and cache_key in _CACHE:
        _CALL_STATS["cache_hits"] += 1
        logger.info(f"[CACHE] Réponse mise en cache retournée ({model})")
        return _CACHE[cache_key]

    # ── 2. Chaîne de fallback des modèles ─────────────────────────────────
    start_idx = FALLBACK_MODELS.index(model) if model in FALLBACK_MODELS else 0
    models_to_try = FALLBACK_MODELS[start_idx:]

    client = get_client()

    for current_model in models_to_try:
        logger.info(f"[GEMINI] Appel → {current_model}")

        try:
            response = client.chat.completions.create(
                model=current_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
            )
            text = response.choices[0].message.content

            _CACHE[_make_cache_key(current_model, prompt)] = text
            _CALL_STATS["success"] += 1
            logger.info(f"[OK] {current_model} | {len(text)} caractères reçus")
            return text

        except Exception as e:
            err_str = str(e).lower()

            is_quota = any(kw in err_str for kw in (
                "429", "quota", "rate_limit", "rate limit", "resource_exhausted"
            ))
            is_not_found = "404" in err_str or "not_found" in err_str

            if is_quota:
                _CALL_STATS["quota_errors"] += 1
                logger.warning(
                    f"[QUOTA] {current_model} → passage immédiat au modèle suivant "
                    f"(pas d'attente pour ne pas bloquer)"
                )
                continue

            elif is_not_found:
                logger.warning(
                    f"[MODÈLE INTROUVABLE] {current_model} n'existe pas sur l'API → modèle suivant..."
                )
                continue

            else:
                logger.error(f"[ERREUR] {current_model}: {e}")
                raise

    raise RuntimeError(
        "Tous les modèles Groq ont atteint leur quota.\n"
        "Solutions :\n"
        "  1. Attendez ~1 minute (reset automatique du free tier)\n"
        "  2. Vérifiez votre GROQ_API_KEY dans .env\n"
        "  3. Créez une nouvelle clé sur https://console.groq.com/keys"
    )


# ══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ══════════════════════════════════════════════════════════════════════════════
def get_stats() -> dict:
    """Retourne les statistiques d'utilisation de l'API."""
    return dict(_CALL_STATS)


def clear_cache() -> None:
    """Vide le cache mémoire (utile en tests)."""
    _CACHE.clear()
    logger.info("[CACHE] Cache vidé")


def test_connection() -> bool:
    """Teste la connexion à l'API Groq avec un prompt minimal."""
    logger.info("[TEST] Vérification de la connexion Groq...")
    try:
        response = call_gemini(
            prompt="Réponds uniquement par OK.",
            use_cache=False,
        )
        if response and len(response.strip()) > 0:
            logger.info(f"[TEST OK] Connexion établie → réponse: '{response.strip()[:50]}'")
            return True
        return False
    except Exception as e:
        logger.error(f"[TEST ÉCHOUÉ] {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# TEST RAPIDE (exécution directe)
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))

    print("\n" + "=" * 60)
    print("  TEST GROQ CLIENT — Sprint 2 (Anis)")
    print("=" * 60)

    print("\n[1] Test de connexion...")
    ok = test_connection()
    print(f"    → {'✓ Connexion OK' if ok else '✗ Connexion échouée'}")

    if not ok:
        print("\n⚠  Vérifiez votre GROQ_API_KEY dans .env")
        sys.exit(1)

    print("\n[2] Test analyse Samsung...")
    test_prompt = "Analyse brièvement Samsung en 3 points forts et 2 points faibles. Max 200 mots."
    result = call_gemini(test_prompt)
    print(f"    → Réponse reçue ({len(result)} caractères)")
    print(f"\n{result[:300]}...")

    print("\n[3] Test cache (même prompt)...")
    result2 = call_gemini(test_prompt)
    print(f"    → Retourné depuis cache : {'✓' if result == result2 else '✗'}")

    print(f"\n[4] Statistiques d'appels:")
    for k, v in get_stats().items():
        print(f"    {k:15} : {v}")

    print("\n" + "=" * 60)
    print("  Tests terminés avec succès!")
    print("=" * 60)
    