import time
import random
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional

try:
    import requests
    REQUEST_EXCEPTIONS = (requests.Timeout, requests.ConnectionError)
    HTTP_ERROR_EXCEPTION = requests.HTTPError
except ImportError:
    requests = None
    REQUEST_EXCEPTIONS = (TimeoutError, ConnectionError)
    HTTP_ERROR_EXCEPTION = Exception

try:
    from src.logger_config import logger
except ImportError:
    logger = logging.getLogger("pfa.error_handler")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        logger.addHandler(logging.StreamHandler())

# ===== EXCEPTIONS =====
class SerpAPIError(Exception):
    pass

class QuotaExceededError(SerpAPIError):
    pass

class InvalidKeyError(SerpAPIError):
    pass

class NetworkError(SerpAPIError):
    pass

class EmptyResponseError(SerpAPIError):
    pass

class CompanyNotFoundError(SerpAPIError):
    pass

class MissingEnvFileError(SerpAPIError):
    pass

class EmptyQueryError(SerpAPIError):
    pass

class FileSaveError(SerpAPIError):
    pass

class InvalidURLError(SerpAPIError):
    pass

# ===== RETRY =====
def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retries = 0
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except REQUEST_EXCEPTIONS as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Echec apres {max_retries} tentatives {str(e)}")
                        raise NetworkError(f"Probleme reseau persistant {str(e)}")
                    delay = base_delay * (2 ** (retries - 1)) + random.uniform(0, 0.5)
                    logger.warning(f"Tentative {retries}/{max_retries} dans {delay:.1f}s")
                    time.sleep(delay)
                except HTTP_ERROR_EXCEPTION as e:
                    status_code = getattr(getattr(e, "response", None), "status_code", None)
                    if status_code == 401:
                        raise InvalidKeyError("Cle API invalide ou expiree")
                    elif status_code == 429:
                        raise QuotaExceededError("Quota API depasse")
                    else:
                        raise SerpAPIError(f"Erreur HTTP {status_code}")
                except Exception as e:
                    logger.error(f"Erreur fatale {str(e)}")
                    raise
            return None
        return wrapper
    return decorator

# ===== VALIDATION =====
def validate_response(data: Optional[Dict], company_name: str = "") -> Dict:
    if data is None:
        logger.error("Reponse None recue")
        raise EmptyResponseError("Aucune reponse recue de l'API")
    
    if not data:
        logger.error("Reponse vide recue")
        raise EmptyResponseError("Reponse vide de l'API")
    
    if not isinstance(data, dict):
        raise SerpAPIError("La reponse n'est pas un JSON valide")
    
    if 'error' in data:
        error_msg = data.get('error', 'Erreur inconnue')
        lowered_error = error_msg.lower()
        logger.error(f"API a retourne une erreur {error_msg}")
        if 'invalid' in lowered_error and 'key' in lowered_error:
            raise InvalidKeyError(f"Cle API invalide {error_msg}")
        elif 'quota' in lowered_error:
            raise QuotaExceededError(f"Quota depasse {error_msg}")
        else:
            raise SerpAPIError(f"Erreur API {error_msg}")
    
    organic_results = data.get('organic_results', [])
    if len(organic_results) == 0:
        raise CompanyNotFoundError(
            f"Entreprise '{company_name}' introuvable sur Google !"
        )
    
    for result in organic_results:
        url = result.get('link', '')
        if url and not url.startswith('http'):
            raise InvalidURLError(f"URL invalide : {url}")
    
    if 'place_results' not in data:
        logger.warning("'place_results' manquant dans la reponse")
        data['place_results'] = {}
    
    logger.info("Reponse API valide")
    return data

# ===== EXTRACTION SECURISEE =====
def safe_extract(data: Dict, key_path: str, default: Any = None) -> Any:
    try:
        keys = key_path.split('.')
        current = data
        for key in keys:
            if not isinstance(current, dict):
                logger.debug(f"Chemin {key_path} interrompu pas un dict")
                return default
            if key not in current:
                logger.debug(f"Cle {key} manquante dans {key_path}")
                return default
            current = current[key]
        if current is None:
            logger.debug(f"Valeur None pour {key_path}")
            return default
        return current
    except Exception as e:
        logger.debug(f"Erreur extraction {key_path} {str(e)}")
        return default