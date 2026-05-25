"""
Porție sugerată — sursă unică pentru motor, reguli și explicații.
Băuturi: mililitri (nutrienți rămân per 100 ml ≈ per 100 g).
Deserturi și restul: grame, ajustate după sex, greutate, activitate și nume aliment.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from domain.models import FoodItem, UserProfile
from services.food_category_resolver import (
    beverage_hint_from_name,
    is_dessert_food_category,
    is_liquid_food_category,
    resolve_category_group,
)
from services.medical_rules_loader import normalize_clinical_text

# Gramaj de referință (porție standard ~70 kg, activitate moderată)
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
    "deserturi": 90,
    "alte": 140,
    "altele": 140,
}

# Mililitri de referință (categorie Băuturi din catalog)
_CATEGORY_PORTION_ML: dict[str, float] = {
    "bauturi": 200,
}

_CATEGORY_SEX_BIAS: dict[str, tuple[float, float]] = {
    "carne": (1.03, 0.97),
    "peste & fructe de mare": (1.03, 0.97),
    "oua": (1.02, 0.98),
    "nuci & seminte": (1.0, 1.0),
}


@dataclass(frozen=True)
class PortionSuggestion:
    amount: int
    unit: str  # "g" | "ml"
    grams_equivalent: int  # pentru calcule nutrienți (per 100g în DB)

    def display_label(self) -> str:
        return format_portion_label(self.amount, self.unit)


def format_portion_label(amount: int, unit: str = "g") -> str:
    u = (unit or "g").lower().strip()
    if u == "ml":
        return f"{amount} ml"
    return f"{amount} g"


def normalize_category(category: str) -> str:
    raw = (category or "").strip().lower()
    return unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")


def normalized_sex(user: UserProfile) -> str:
    raw = normalize_clinical_text(user.sex or "")
    if not raw or raw == "other":
        return "other"
    if raw in ("m", "male", "man"):
        return "M"
    if raw in ("f", "female", "woman"):
        return "F"
    if raw.startswith("fem"):
        return "F"
    if raw.startswith("mascul") or "barbat" in raw:
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
    w = float(user.weight or 70)
    if w <= 0:
        return 1.0
    return max(0.88, min(1.12, 0.92 + (w - 70.0) * 0.004))


def _base_sex_factor(sex: str) -> float:
    return {"M": 1.06, "F": 0.94, "other": 1.0}.get(sex, 1.0)


def _sex_multiplier(user: UserProfile, cat: str) -> float:
    sex = normalized_sex(user)
    sex_f = _base_sex_factor(sex)
    cat_bias = _CATEGORY_SEX_BIAS.get(cat)
    if cat_bias:
        m_mul, f_mul = cat_bias
        if sex == "M":
            sex_f *= m_mul
        elif sex == "F":
            sex_f *= f_mul
    return sex_f * _weight_factor(user) * _activity_factor(user)


def _name_norm(name: str) -> str:
    return normalize_category(name or "")


def _grams_from_food_name(name: str, *, dessert: bool) -> Optional[int]:
    n = _name_norm(name)
    if not n:
        return None
    m = re.search(r"\((\d+)\s*(buc|bucati|felii|felie|mare|medii|mediu|portie|portii)\)", n)
    if m:
        qty = int(m.group(1))
        kind = m.group(2)
        if "felie" in kind or "portie" in kind:
            return min(200, 95 * qty)
        if "buc" in kind:
            return min(180, 55 * qty)
        if "mare" in kind:
            return 50 * qty
        if "medi" in kind:
            return 70 * qty
    if dessert:
        if "felie" in n:
            return 110
        if "inghetata" in n:
            return 80
        if "biscuit" in n or "cookie" in n:
            return 45
        if "briosa" in n or "croissant" in n:
            return 75
        if "cheesecake" in n or "tiramisu" in n or "placinta" in n:
            return 105
        if "baton" in n and "lam" in n:
            return 35
    return None


def suggest_portion(
    food: FoodItem,
    user: Optional[UserProfile] = None,
    *,
    category: Optional[str] = None,
) -> PortionSuggestion:
    cat_raw = category if category is not None else (food.category or "")
    group = resolve_category_group(cat_raw)
    name = food.name or ""

    if is_liquid_food_category(cat_raw):
        base_ml = float(_CATEGORY_PORTION_ML.get("bauturi", 200))
        hinted = beverage_hint_from_name(name)
        if hinted is not None:
            base_ml = float(hinted)
        if user is not None:
            base_ml *= _sex_multiplier(user, "bauturi")
        amount = max(50, int(round(base_ml)))
        return PortionSuggestion(amount=amount, unit="ml", grams_equivalent=amount)

    if is_dessert_food_category(cat_raw):
        base = float(_CATEGORY_PORTION_G.get("deserturi", 90))
        hinted = _grams_from_food_name(name, dessert=True)
        if hinted is not None:
            base = float(hinted)
        if user is not None:
            base *= _sex_multiplier(user, "deserturi")
        amount = max(25, int(round(base)))
        return PortionSuggestion(amount=amount, unit="g", grams_equivalent=amount)

    # Cereale integrale / ovăz etc. — porție de cereale, nu lactate
    if group == "cereale" and re.search(r"\b(integral|ovaz|terci|quinoa|orez|paine|bagel|paste|spaghetti)\b", _name_norm(name)):
        base = float(_CATEGORY_PORTION_G.get("cereale", 150))
        if "paine" in _name_norm(name) or "felie" in _name_norm(name):
            base = 80.0
        if user is not None:
            base *= _sex_multiplier(user, "cereale")
        amount = max(30, int(round(base)))
        return PortionSuggestion(amount=amount, unit="g", grams_equivalent=amount)

    base = float(_CATEGORY_PORTION_G.get(group, 150))
    if user is not None:
        base *= _sex_multiplier(user, group)
    amount = max(30, int(round(base)))
    return PortionSuggestion(amount=amount, unit="g", grams_equivalent=amount)


def suggest_portion_grams(
    food: FoodItem,
    user: Optional[UserProfile] = None,
    *,
    category: Optional[str] = None,
) -> int:
    """Compatibilitate: întotdeauna echivalentul în grame/ml pentru formule per 100g."""
    return suggest_portion(food, user, category=category).grams_equivalent


def suggest_portion_for_category(category: str, user: Optional[UserProfile] = None) -> int:
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
    return suggest_portion(dummy, user, category=category).grams_equivalent
