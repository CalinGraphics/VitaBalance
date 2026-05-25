"""
Rezolvă categoria principală pentru alimente cu path-uri compuse din catalog (ex. Cereale/Procesate, Mese/Cereale).
Evită confuzia cereale ↔ lactate (ex. „cu lapte” nu face ca pâinea integrală să fie lactate).
"""
from __future__ import annotations

import re
import unicodedata
from typing import Optional

# Ordinea contează: primul segment potrivit din path câștigă (cereale înainte de lactate).
_SEGMENT_TO_GROUP: tuple[tuple[str, str], ...] = (
    ("bauturi", "Băuturi"),
    ("deserturi", "Deserturi"),
    ("cereale", "Cereale"),
    ("leguminoase", "Leguminoase"),
    ("legume", "Legume"),
    ("fructe", "Fructe"),
    ("peste", "Pește"),
    ("carne", "Carne"),
    ("oua", "Ouă"),
    ("ouă", "Ouă"),
    ("nuci", "Nuci"),
    ("semin", "Semințe"),
    ("lactate", "Lactate"),
    ("lapte", "Lactate"),
    ("suplimente", "Suplimente"),
    ("condimente", "Condimente"),
    ("gustari", "Gustări"),
    ("mese", "Mese"),
    ("proteine", "Proteine"),
    ("vegetarian", "Vegetarian"),
    ("vegan", "Vegan"),
    ("paste", "Paste"),
)


def normalize_category_token(category: str) -> str:
    raw = (category or "").strip().lower()
    return unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")


def split_category_path(category: str) -> list[str]:
    norm = normalize_category_token(category)
    if not norm:
        return []
    return [p.strip() for p in norm.split("/") if p.strip()]


def resolve_category_group(category: str) -> str:
    """
    Cheie normalizată pentru porții / filtre (cereale, lactate, bauturi, ...).
    Prioritatea globală (cereale înainte de lactate/mese) se aplică pe toate segmentele path-ului.
    """
    parts = split_category_path(category)
    if not parts:
        return "alte"

    for needle, group_key in _SEGMENT_TO_GROUP:
        for part in parts:
            if needle in part:
                return normalize_category_token(group_key)

    return parts[0]


def resolve_category_display_label(category: str) -> str:
    """Etichetă UI lizibilă pentru badge-ul de categorie."""
    key = resolve_category_group(category)
    labels = {
        "bauturi": "Băuturi",
        "deserturi": "Deserturi",
        "cereale": "Cereale",
        "leguminoase": "Leguminoase",
        "legume": "Legume",
        "fructe": "Fructe",
        "peste": "Pește",
        "carne": "Carne",
        "oua": "Ouă",
        "nuci": "Nuci",
        "semin": "Semințe",
        "lactate": "Lactate",
        "suplimente": "Suplimente",
        "condimente": "Condimente",
        "gustari": "Gustări",
        "mese": "Mese",
        "proteine": "Proteine",
        "vegetarian": "Vegetarian",
        "vegan": "Vegan",
        "paste": "Paste",
        "alte": "Altele",
    }
    if key in labels:
        return labels[key]
    if not category:
        return ""
    cleaned = category.replace("_", " ").strip()
    return cleaned[:1].upper() + cleaned[1:] if cleaned else ""


def is_liquid_food_category(category: str) -> bool:
    return resolve_category_group(category) == "bauturi"


def is_dessert_food_category(category: str) -> bool:
    return resolve_category_group(category) == "deserturi"


def beverage_hint_from_name(name: str) -> Optional[int]:
    """Doar băuturi reale — nu potrivi „lapte” din interiorul altor cuvinte."""
    n = normalize_category_token(name or "")
    if not n:
        return None
    if re.search(r"\bdoza\b", n) or "1 doza" in n:
        return 330
    if "cocktail" in n:
        return 200
    if re.search(r"\bvin\b", n) and "vinete" not in n:
        return 125
    if "bere" in n:
        return 330
    if any(x in n for x in ("cafea", "espresso", "latte", "mocha")):
        return 180
    if "ceai" in n:
        return 200
    if "smoothie" in n:
        return 300
    if "apa de cocos" in n or n.startswith("apa "):
        return 250
    if re.search(r"\blapte\b", n):
        if any(x in n for x in ("ovaz", "migdale", "soia", "cocos", "zer")):
            return 250
        if "ciocolata" in n:
            return 200
        return 200
    if re.search(r"\bsuc\b", n) or "limonada" in n:
        return 200
    if "kombucha" in n:
        return 250
    return None
