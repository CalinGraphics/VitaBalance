"""
Fapte structurate, independente de limbă, care stau la baza explicației unei recomandări.

Explicația NU e text liber: e derivată strict din nevoile utilizatorului (analize sau afirmații explicite, cu sursa
salvată), din alimentul recomandat și din regulile care s-au aplicat. Faptele se salvează în
`recommendations.explanation_json.facts`; textul RO/EN se construiește în frontend (locales), deci schimbarea limbii
nu cere regenerarea recomandărilor. `trace` conține toate cifrele scorului (scoring.py), ca fiecare recomandare
să poată fi urmărită până la regulă și numere.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from services.nutrition.needs import NUTRIENTS, Need
from services.nutrition.food_validation import portion_kcal
from services.recommendations.scoring import Ranking, ScoredFood

FACTS_VERSION = 4
MAX_NUTRIENTS = 3
LIQUID_KEYS = {"milk_whole", "milk_semi", "soy_milk_fortified", "almond_milk"}

NUTRIENT_KEYS = list(NUTRIENTS)


def portion_unit(food) -> str:
    return "ml" if (food.food_key in LIQUID_KEYS or food.category_key == "plant_milks") else "g"


def build_facts(item: ScoredFood, ranking: Ranking, *, has_lab_data: bool) -> Dict[str, Any]:
    food = item.food
    needs_by_nutrient: Dict[str, Need] = {n.nutrient: n for n in ranking.needs}
    comps = sorted(item.components, key=lambda c: -c.contribution)[:MAX_NUTRIENTS]
    nutrients: List[Dict[str, Any]] = []
    for c in comps:
        need = needs_by_nutrient.get(c.nutrient)
        nutrients.append({
            "key": c.nutrient,
            "amount": round(c.portion_amount, 2),
            "per100": round(c.per100, 2),
            "daily_reference": c.daily_reference,
            "pct": int(min(100, round(c.portion_share * 100))),
            "need": need.to_dict() if (need is not None and not item.fill) else {"source": "general"},
        })
    kcal = portion_kcal(food.calories, food.portion_g or 0)
    return {
        "v": FACTS_VERSION,
        "food_id": food.id,
        "food_key": food.food_key,
        "category": food.category_key,
        "animal": food.animal_source,
        "portion": {"amount": int(round(food.portion_g or 0)), "unit": portion_unit(food),
                    "label_ro": food.portion_label_ro, "label_en": food.portion_label_en},
        "kcal_portion": round(kcal) if kcal is not None else None,
        "has_lab_data": bool(has_lab_data),
        "nutrients": nutrients,
        "primary": item.primary.nutrient if item.primary else None,
        "coverage_pct": item.coverage_pct,
        "profile": {"diet": ranking.diet if ranking.diet in ("vegan", "vegetarian", "pescatarian") else None,
                    "allergies": sorted(ranking.allergies),
                    "conditions": sorted(ranking.conditions)},
        "safety_rules": ranking.rule_ids,
        "flags": list(food.flags),
        "alternatives": list(item.alternatives),
        "trace": item.trace(ranking.rule_ids),
    }


def parse_explanation_json(value: Any) -> Optional[Dict[str, Any]]:
    """`explanation_json` vine ca dict (jsonb) sau, uneori, ca șir JSON; None dacă nu e un obiect valid."""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return None
    return value if isinstance(value, dict) else None


def has_facts(explanation_json: Any) -> bool:
    """True dacă explicația salvată e în formatul curent (cu fapte) și poate fi randată în orice limbă."""
    data = parse_explanation_json(explanation_json)
    facts = data.get("facts") if data else None
    return isinstance(facts, dict) and facts.get("v") == FACTS_VERSION
