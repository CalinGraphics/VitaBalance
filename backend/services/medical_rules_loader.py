"""Încărcare reguli clinice din JSON + normalizare text pentru matching robust."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, Optional


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
    "dairy": "lactate",
    "lactose": "lactoza",
    "casein": "lactate",
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


def normalize_diet_type(value: Optional[str]) -> str:
    """Valoare dietă din UI/DB: vegan, Vegan, OMNIVORE -> lowercase consistent."""
    if value is None or not str(value).strip():
        return "omnivore"
    return str(value).strip().lower()


def resolve_allergy_token(normalized_user_allergy: str) -> str:
    """Mapări comune (ex. fish → peste) după normalizare clinică."""
    return ALLERGY_TOKEN_ALIASES.get(normalized_user_allergy, normalized_user_allergy)


def load_medical_rules_config() -> Dict[str, Any]:
    cfg_path = Path(__file__).resolve().parents[1] / "config" / "medical_rules.json"
    if not cfg_path.exists():
        return {"condition_food_rules": [], "condition_trigger_rules": []}
    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"condition_food_rules": [], "condition_trigger_rules": []}
        data.setdefault("condition_food_rules", [])
        data.setdefault("condition_trigger_rules", [])
        return data
    except Exception:
        return {"condition_food_rules": [], "condition_trigger_rules": []}
