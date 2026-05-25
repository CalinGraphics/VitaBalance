"""
Porție sugerată (gramaj) — sursă unică pentru motor, reguli și explicații.
Ține cont de categorie aliment, sex, greutate și activitate.
"""
from __future__ import annotations

import unicodedata
from typing import Optional

from domain.models import FoodItem, UserProfile
from services.medical_rules_loader import normalize_clinical_text

# Gramaj de referință per 100g aliment (porție „standard” la greutate 70 kg, activitate moderată)
_CATEGORY_PORTION_G: dict[str, float] = {
    "peste & fructe de mare": 130,
    "carne": 130,
    "oua": 120,
    "leguminoase": 170,
    "legume": 200,
    "fructe": 180,
    "lactate": 200,
    "nuci & seminte": 40,
    "cereale": 150,
    "alte": 140,
    "altele": 140,
}

# Ajustări ușoare pe categorii dense în proteine / energie (față de sex global)
_CATEGORY_SEX_BIAS: dict[str, tuple[float, float]] = {
    # (factor M, factor F) — înmulțit cu factorul de sex de bază
    "carne": (1.03, 0.97),
    "peste & fructe de mare": (1.03, 0.97),
    "oua": (1.02, 0.98),
    "nuci & seminte": (1.0, 1.0),
}


def normalize_category(category: str) -> str:
    raw = (category or "").strip().lower()
    return unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")


def normalized_sex(user: UserProfile) -> str:
    """M / F / other — aliniat cu DeficitCalculator."""
    raw = normalize_clinical_text(user.sex or "")
    if not raw or raw == "other":
        return "other"
    if raw in ("m", "male", "man"):
        return "M"
    if raw in ("f", "female", "woman"):
        return "F"
    if raw.startswith("fem") or raw.startswith("mascul"):
        return "F" if raw.startswith("fem") else "M"
    if "barbat" in raw or raw.startswith("mascul"):
        return "M"
    if len(raw) == 1 and raw in "mf":
        return raw.upper()
    return "other"


def _activity_factor(user: UserProfile) -> float:
    return {
        "sedentary": 0.95,
        "moderate": 1.0,
        "active": 1.1,
        "very_active": 1.2,
    }.get((user.activity_level or "moderate").lower(), 1.0)


def _weight_factor(user: UserProfile) -> float:
    """Scalare ușoară față de 70 kg (±12%)."""
    w = float(user.weight or 70)
    if w <= 0:
        return 1.0
    delta = (w - 70.0) * 0.004
    return max(0.88, min(1.12, 0.92 + delta))


def _base_sex_factor(sex: str) -> float:
    return {"M": 1.06, "F": 0.94, "other": 1.0}.get(sex, 1.0)


def suggest_portion_grams(
    food: FoodItem,
    user: Optional[UserProfile] = None,
    *,
    category: Optional[str] = None,
) -> int:
    """
    Gramaj porție pentru afișare și calcule de acoperire.
    Masculin: porții ușor mai mari; feminin: ușor mai mici; + greutate și activitate.
    """
    cat = normalize_category(category if category is not None else (food.category or ""))
    base = float(_CATEGORY_PORTION_G.get(cat, 150))

    if user is None:
        return max(30, int(round(base)))

    sex = normalized_sex(user)
    sex_f = _base_sex_factor(sex)
    cat_bias = _CATEGORY_SEX_BIAS.get(cat)
    if cat_bias:
        m_mul, f_mul = cat_bias
        if sex == "M":
            sex_f *= m_mul
        elif sex == "F":
            sex_f *= f_mul

    grams = base * sex_f * _weight_factor(user) * _activity_factor(user)
    return max(30, int(round(grams)))


def suggest_portion_for_category(category: str, user: Optional[UserProfile] = None) -> int:
    """Variantă când nu există obiect FoodItem complet."""
    dummy = FoodItem(
        id=0,
        name="",
        category=category or "alte",
        iron=0,
        calcium=0,
        vitamin_d=0,
        vitamin_b12=0,
        magnesium=0,
        protein=0,
        zinc=0,
        vitamin_c=0,
        fiber=0,
        calories=0,
    )
    return suggest_portion_grams(dummy, user, category=category)
