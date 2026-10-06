"""Normalizarea textului clinic (fără diacritice, litere mici) și aliasurile de alergii."""
from __future__ import annotations

import re
import unicodedata
from typing import Dict


def normalize_clinical_text(value: str) -> str:
    raw = (value or "").strip().lower().replace("_", " ").replace("-", " ")
    folded = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", folded).strip()


# Aliasuri frecvente (EN / alternative) → token normalizat al unei chei din maparea de alergii.
ALLERGY_TOKEN_ALIASES: Dict[str, str] = {
    "fish": "peste",
    "seafood": "peste",
    "shellfish": "crustacee",
    "shrimp": "crustacee",
    "prawn": "crustacee",
    "langoustine": "crustacee",
    "lobster": "crustacee",
    "crab": "crustacee",
    "peanut": "arahide",
    "peanuts": "arahide",
    "milk": "lactoza",
    "lapte": "lactoza",
    "dairy": "lactoza",
    "lactate": "lactoza",
    "branza": "lactoza",
    "cheese": "lactoza",
    "lactose": "lactoza",
    "casein": "lactoza",
    "egg": "oua",
    "eggs": "oua",
    "wheat": "gluten",
    "celiac": "gluten",
    "coeliac": "gluten",
    "soy": "soia",
    "soya": "soia",
    "soja": "soia",
    "tree nuts": "nuci",
    "treenuts": "nuci",
}


def resolve_allergy_token(normalized_user_allergy: str) -> str:
    """Mapări comune (ex. fish → peste) după normalizare clinică."""
    return ALLERGY_TOKEN_ALIASES.get(normalized_user_allergy, normalized_user_allergy)
