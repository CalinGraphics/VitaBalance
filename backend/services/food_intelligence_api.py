from __future__ import annotations

from typing import Dict, Optional, Tuple, Any
import threading
import time

from services.medical_rules_loader import normalize_clinical_text


_CACHE_LOCK = threading.Lock()
_CACHE: Dict[str, Tuple[float, Optional[bool]]] = {}
_TTL_SECONDS = 60 * 60 * 6  # 6h


def _cache_get(key: str) -> Optional[Optional[bool]]:
    now = time.time()
    with _CACHE_LOCK:
        item = _CACHE.get(key)
        if not item:
            return None
        ts, val = item
        if now - ts > _TTL_SECONDS:
            _CACHE.pop(key, None)
            return None
        return val


def _cache_set(key: str, value: Optional[bool]) -> None:
    with _CACHE_LOCK:
        _CACHE[key] = (time.time(), value)


def assess_hidden_soy_risk_from_api(food_name: str, food_category: str = "") -> Optional[bool]:
    """
    Returnează:
      - True: API indică derivate de soia (risc prezent)
      - False: API indică explicit soy-free (risc scăzut)
      - None: necunoscut / API indisponibil
    """
    try:
        from config import get_settings
        settings = get_settings()
    except Exception:
        _cache_set(f"{normalize_clinical_text(food_name or '')}|{normalize_clinical_text(food_category or '')}", None)
        return None
    if not settings.openfoodfacts_enabled:
        return None

    name_norm = normalize_clinical_text(food_name or "")
    cat_norm = normalize_clinical_text(food_category or "")
    if not name_norm:
        return None

    cache_key = f"{name_norm}|{cat_norm}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    url = "https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": food_name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 5,
    }
    try:
        try:
            import httpx  # import lazy: API-ul rămâne opțional
        except Exception:
            _cache_set(cache_key, None)
            return None
        timeout = max(0.3, float(settings.openfoodfacts_timeout_seconds))
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data: Dict[str, Any] = resp.json()
    except Exception:
        _cache_set(cache_key, None)
        return None

    products = data.get("products") or []
    if not isinstance(products, list):
        _cache_set(cache_key, None)
        return None

    # Heuristic simplu: primul produs cu nume relevant.
    chosen = None
    for p in products:
        p_name = normalize_clinical_text((p or {}).get("product_name") or "")
        if not p_name:
            continue
        if any(tok in p_name for tok in name_norm.split()[:2]):
            chosen = p
            break
    if not chosen and products:
        chosen = products[0]
    if not chosen:
        _cache_set(cache_key, None)
        return None

    ingredients = normalize_clinical_text(chosen.get("ingredients_text") or "")
    allergens = normalize_clinical_text(chosen.get("allergens") or "")
    allergens_tags = " ".join(chosen.get("allergens_tags") or [])
    allergens_tags = normalize_clinical_text(allergens_tags)
    labels_tags = " ".join(chosen.get("labels_tags") or [])
    labels_tags = normalize_clinical_text(labels_tags)

    soy_markers = (
        "soia", "soy", "soja", "lecitina de soia", "soy lecithin", "proteina de soia",
        "isolat proteic din soia", "tofu", "miso", "edamame", "tamari",
    )
    if any(m in ingredients for m in soy_markers) or any(m in allergens for m in soy_markers):
        _cache_set(cache_key, True)
        return True
    if "en:soybeans" in allergens_tags or "soja" in allergens_tags or "soy" in allergens_tags:
        _cache_set(cache_key, True)
        return True

    soy_free_markers = ("en:soy-free", "soy free", "fara soia", "fără soia")
    if any(m in labels_tags for m in soy_free_markers):
        _cache_set(cache_key, False)
        return False

    _cache_set(cache_key, None)
    return None
