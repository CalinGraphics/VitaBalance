from __future__ import annotations

from typing import Dict, Optional, Tuple, Any
import threading
import time

from services.medical_rules_loader import normalize_clinical_text


_CACHE_LOCK = threading.Lock()
_CACHE: Dict[str, Tuple[float, Optional[bool]]] = {}
_TTL_SECONDS = 60 * 60 * 6  # 6h
_INFLIGHT: set[str] = set()

_ALLERGEN_MARKERS: Dict[str, Tuple[str, ...]] = {
    "soia": (
        "soia", "soy", "soja", "lecitina de soia", "soy lecithin", "proteina de soia",
        "isolat proteic din soia", "tofu", "miso", "edamame", "tamari",
    ),
    "lactoza": (
        "lapte", "lactate", "dairy", "milk", "lactose", "lactoza", "casein", "whey",
        "iaurt", "branza", "brânză", "smantana", "unt", "mozzarella", "cheddar",
        "ricotta", "parmezan", "feta", "gorgonzola",
    ),
    "lactate": (
        "lapte", "lactate", "dairy", "milk", "lactose", "lactoza", "casein", "whey",
        "iaurt", "branza", "brânză", "smantana", "unt", "mozzarella", "cheddar",
        "ricotta", "parmezan", "feta", "gorgonzola",
    ),
    "gluten": (
        "gluten", "wheat", "barley", "rye", "grau", "grâu", "faina", "făină",
        "seitan", "malț", "malt",
    ),
    "sesam": ("sesam", "sezam", "sesame", "tahini"),
    "arahide": ("arahide", "peanut", "peanuts"),
    "nuci": (
        "nuci", "nuts", "almond", "walnut", "hazelnut", "pecan", "pistachio",
        "cashew", "macadamia", "pinoli", "nuci de pin",
    ),
    "oua": ("ou", "oua", "ouă", "egg", "eggs", "albumin"),
    "crustacee": ("crustacee", "shrimp", "prawn", "crab", "lobster", "crevet", "homar", "langusta"),
    "peste": ("peste", "pește", "fish", "seafood", "somon", "ton", "macrou", "cod", "tilapia"),
    "mustar": ("mustar", "muștar", "mustard"),
}

_ALLERGEN_TAG_MARKERS: Dict[str, Tuple[str, ...]] = {
    "soia": ("en:soybeans", "soy", "soja"),
    "lactoza": ("en:milk", "milk", "dairy"),
    "lactate": ("en:milk", "milk", "dairy"),
    "gluten": ("en:gluten", "wheat", "barley", "rye"),
    "sesam": ("en:sesame-seeds", "sesame"),
    "arahide": ("en:peanuts", "peanut"),
    "nuci": ("en:nuts", "nut"),
    "oua": ("en:eggs", "egg"),
    "crustacee": ("en:crustaceans", "crustacean", "shrimp", "prawn", "crab", "lobster"),
    "peste": ("en:fish", "fish", "seafood"),
    "mustar": ("en:mustard", "mustard"),
}


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


def _fetch_openfoodfacts_verdict(food_name: str, timeout_seconds: float, allergy_token: str = "soia") -> Optional[bool]:
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

    token = normalize_clinical_text(allergy_token or "")
    markers = _ALLERGEN_MARKERS.get(token) or _ALLERGEN_MARKERS["soia"]
    tag_markers = _ALLERGEN_TAG_MARKERS.get(token) or _ALLERGEN_TAG_MARKERS["soia"]

    if any(m in ingredients for m in markers) or any(m in allergens for m in markers):
        return True
    if any(m in allergens_tags for m in tag_markers):
        return True

    free_markers = {
        "soia": ("en:soy-free", "soy free", "fara soia", "fără soia"),
        "lactoza": ("en:lactose-free", "lactose free", "fara lactoza", "fără lactoză"),
        "lactate": ("en:dairy-free", "dairy free", "fara lactate", "fără lactate"),
        "gluten": ("en:gluten-free", "gluten free", "fara gluten", "fără gluten"),
        "sesam": ("en:sesame-free", "sesame free"),
        "arahide": ("en:peanut-free", "peanut free"),
        "nuci": ("en:nut-free", "nut free"),
        "oua": ("en:egg-free", "egg free", "fara oua", "fără ouă"),
        "crustacee": ("en:crustacean-free",),
        "peste": ("en:fish-free", "fish free"),
        "mustar": ("en:mustard-free",),
    }.get(token, ())
    if any(m in labels_tags for m in free_markers):
        # Pentru soia păstrăm verdictul explicit "safe" (folosit deja în producție).
        # Pentru ceilalți alergeni folosim strategie conservatoare: evităm false-safe
        # din potriviri aproximative OFF și lăsăm decizia pe safety-first în caller.
        if token == "soia":
            return False
        return None
    return None


def _start_background_fetch(cache_key: str, food_name: str, timeout_seconds: float, allergy_token: str = "soia") -> None:
    def _runner() -> None:
        try:
            verdict = _fetch_openfoodfacts_verdict(food_name, timeout_seconds, allergy_token=allergy_token)
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

    cache_key = f"{name_norm}|{cat_norm}|soia"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    if not settings.openfoodfacts_blocking_mode:
        _start_background_fetch(
            cache_key, food_name, settings.openfoodfacts_timeout_seconds, allergy_token="soia"
        )
        return None

    verdict = _fetch_openfoodfacts_verdict(
        food_name, settings.openfoodfacts_timeout_seconds, allergy_token="soia"
    )
    _cache_set(cache_key, verdict)
    return verdict


def assess_hidden_allergen_risk_from_api(
    food_name: str,
    allergy_token: str,
    food_category: str = "",
) -> Optional[bool]:
    """
    Returnează:
      - True: API indică prezența alergenului dat
      - False: API indică explicit variantă fără acel alergen
      - None: necunoscut / API indisponibil
    """
    token = normalize_clinical_text(allergy_token or "")
    if token not in _ALLERGEN_MARKERS:
        return None
    try:
        from config import get_settings
        settings = get_settings()
    except Exception:
        return None
    if not settings.openfoodfacts_enabled:
        return None
    name_norm = normalize_clinical_text(food_name or "")
    cat_norm = normalize_clinical_text(food_category or "")
    if not name_norm:
        return None
    cache_key = f"{name_norm}|{cat_norm}|{token}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    if not settings.openfoodfacts_blocking_mode:
        _start_background_fetch(
            cache_key, food_name, settings.openfoodfacts_timeout_seconds, allergy_token=token
        )
        return None
    verdict = _fetch_openfoodfacts_verdict(
        food_name, settings.openfoodfacts_timeout_seconds, allergy_token=token
    )
    _cache_set(cache_key, verdict)
    return verdict
