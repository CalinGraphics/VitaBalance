from __future__ import annotations

from typing import Dict, Optional, Tuple, Any
import threading
import time

from services.medical_rules_loader import normalize_clinical_text


_CACHE_LOCK = threading.Lock()
_CACHE: Dict[str, Tuple[float, Optional[bool]]] = {}
_TTL_SECONDS = 60 * 60 * 6  # 6h
_INFLIGHT: set[str] = set()


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


def _fetch_openfoodfacts_verdict(food_name: str, timeout_seconds: float) -> Optional[bool]:
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
            return None
        timeout = max(0.2, float(timeout_seconds))
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data: Dict[str, Any] = resp.json()
    except Exception:
        return None

    products = data.get("products") or []
    if not isinstance(products, list):
        return None
    chosen = products[0] if products else None
    if not chosen:
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
        return True
    if "en:soybeans" in allergens_tags or "soja" in allergens_tags or "soy" in allergens_tags:
        return True

    soy_free_markers = ("en:soy-free", "soy free", "fara soia", "fără soia")
    if any(m in labels_tags for m in soy_free_markers):
        return False
    return None


def _start_background_fetch(cache_key: str, food_name: str, timeout_seconds: float) -> None:
    def _runner() -> None:
        try:
            verdict = _fetch_openfoodfacts_verdict(food_name, timeout_seconds)
            _cache_set(cache_key, verdict)
        finally:
            with _CACHE_LOCK:
                _INFLIGHT.discard(cache_key)

    with _CACHE_LOCK:
        if cache_key in _INFLIGHT:
            return
        _INFLIGHT.add(cache_key)
    t = threading.Thread(target=_runner, daemon=True)
    t.start()


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

    if not settings.openfoodfacts_blocking_mode:
        _start_background_fetch(cache_key, food_name, settings.openfoodfacts_timeout_seconds)
        return None

    verdict = _fetch_openfoodfacts_verdict(food_name, settings.openfoodfacts_timeout_seconds)
    _cache_set(cache_key, verdict)
    return verdict
