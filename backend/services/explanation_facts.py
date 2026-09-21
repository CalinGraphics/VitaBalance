"""
Fapte structurate, independente de limbă, care stau la baza explicației unei recomandări.

Explicația NU e text liber: e derivată strict din datele pacientului (analize, observații, profil) și din alimentul
recomandat. Faptele se salvează în `recommendations.explanation_json.facts`; textul RO/EN se randează la citire
(vezi explanation_renderer.py), deci schimbarea limbii nu cere regenerarea recomandărilor.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from domain.models import FoodItem, LabResultItem, UserProfile
from services.deficit_calculator import DeficitCalculator
from services.explanation_i18n import ALLERGY_LABELS, NUTRIENT_UNITS
from services.medical_rules_loader import normalize_clinical_text
from services.portion_calculator import PortionSuggestion

FACTS_VERSION = 2
MAX_NUTRIENTS = 3
MAX_ALTERNATIVES = 3
MIN_GENERAL_PCT = 10  # fără deficite: menționăm doar nutrienți care contribuie măcar cu 10% din necesar

NUTRIENT_KEYS = [
    "iron", "calcium", "vitamin_d", "vitamin_b12", "magnesium", "protein", "zinc", "folate",
    "vitamin_a", "vitamin_c", "iodine", "vitamin_k", "potassium",
]

# Afecțiuni cu restricții alimentare, detectate în textul normalizat (fără diacritice) din profil și observații.
CONDITION_PATTERNS: Dict[str, str] = {
    "celiac": r"celiac|gluten",
    "lactose": r"lactoz",
    "reflux": r"reflux|gerd|arsuri gastrice",
    "gastritis": r"gastrit|ulcer",
    "gout": r"\bgota\b|\bgout\b|hiperuricemi",
    "renal": r"rinichi|renal",
    "diabetes": r"diabet|glicemi",
    "hypertension": r"hipertensiun|\bhta\b|tensiune mare",
    "ibs": r"\bibs\b|colon iritabil|iritatii intestinale",
    "colitis": r"colit|crohn",
    "diverticulitis": r"diverticulit",
    "liver_pancreas": r"ficat gras|steatoz|hepatit|pancreat|colecist",
    "cholesterol_cardio": r"colesterol|dislipidemi|cardiovascular|cord ischemic|ateroscleroz",
}


def food_nutrient_value(food: FoodItem, nutrient: str) -> float:
    """Valoarea per 100 g (100 ml) din catalog; 0 dacă lipsește."""
    try:
        return float(getattr(food, nutrient, 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def _rdi_reference(calc: DeficitCalculator, nutrient: str, user: UserProfile) -> float:
    """Reperul zilnic în unitatea catalogului (vitamina D: catalog în µg, VNR în UI => /40)."""
    rdi = calc.get_rdi(nutrient, user)
    if nutrient == "vitamin_d" and rdi > 0:
        return rdi / 40.0
    return rdi


def detect_conditions(user: UserProfile, lab_results: Optional[LabResultItem]) -> List[str]:
    """Id-urile afecțiunilor cu restricții alimentare menționate de pacient (profil + observații analize)."""
    text = normalize_clinical_text(
        f"{user.medical_conditions or ''} {(lab_results.notes if lab_results else '') or ''}"
    )
    return [cid for cid, pattern in CONDITION_PATTERNS.items() if re.search(pattern, text)]


def detect_allergies(user: UserProfile) -> List[str]:
    known = set(ALLERGY_LABELS["ro"])
    out: List[str] = []
    for part in re.split(r"[,;]", user.allergies or ""):
        code = normalize_clinical_text(part)
        if code in known and code not in out:
            out.append(code)
    return out


def _selected_nutrients(
    food: FoodItem, deficits: Dict[str, float], covered: List[str]
) -> List[str]:
    """Nutrienții cu deficit modelat > 0 pe care alimentul îi conține; cei creditați de motor primii."""
    ranked = []
    for key in NUTRIENT_KEYS:
        v100 = food_nutrient_value(food, key)
        deficit = float(deficits.get(key) or 0)
        if v100 > 0 and deficit > 0:
            ranked.append((key not in covered, -(v100 * deficit), key))
    ranked.sort()
    return [k for _, _, k in ranked[:MAX_NUTRIENTS]]


def build_facts(
    *,
    food: FoodItem,
    user: UserProfile,
    lab_results: Optional[LabResultItem],
    deficits: Dict[str, float],
    rec: Dict[str, Any],
    portion: PortionSuggestion,
    has_lab_data: bool,
    alternatives: Optional[List[int]] = None,
) -> Dict[str, Any]:
    calc = DeficitCalculator()
    covered = [k for k in (rec.get("nutrients_covered") or []) if k in NUTRIENT_KEYS]
    grams = float(portion.grams_equivalent)

    def entry(key: str, need: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        ref = _rdi_reference(calc, key, user)
        amount = food_nutrient_value(food, key) * grams / 100.0
        if ref <= 0 or amount <= 0:
            return None
        return {
            "key": key,
            "amount": round(amount, 2),
            "pct": int(min(100, round(amount / ref * 100))),
            "need": need,
        }

    nutrients: List[Dict[str, Any]] = []
    for key in _selected_nutrients(food, deficits, covered):
        e = entry(key, calc.describe_need(key, user, lab_results))
        if e:
            nutrients.append(e)

    if not nutrients:
        # Fără deficite modelate (ex. nu există analize): doar contribuțiile reale ale alimentului, marcate „general".
        general = [entry(k, {"source": "general"}) for k in NUTRIENT_KEYS if food_nutrient_value(food, k) > 0]
        general = [e for e in general if e and e["pct"] >= MIN_GENERAL_PCT]
        general.sort(key=lambda e: -e["pct"])
        nutrients = general[:2]

    diet = calc._normalized_diet(user)
    return {
        "v": FACTS_VERSION,
        "food_id": food.id,
        "portion": {"amount": portion.amount, "unit": portion.unit},
        "has_lab_data": bool(has_lab_data),
        "nutrients": nutrients,
        "profile": {
            "diet": diet if diet in ("vegan", "vegetarian", "pescatarian") else None,
            "allergies": detect_allergies(user),
            "conditions": detect_conditions(user, lab_results),
        },
        "alternatives": [int(a) for a in (alternatives or [])][:MAX_ALTERNATIVES],
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
    """True dacă explicația salvată e în formatul nou (cu fapte) și poate fi randată în orice limbă."""
    data = parse_explanation_json(explanation_json)
    facts = data.get("facts") if data else None
    return isinstance(facts, dict) and facts.get("v") == FACTS_VERSION


def alternatives_for(rec_dicts: List[Dict[str, Any]], nutrients_by_food: Dict[int, List[str]]) -> Dict[int, List[int]]:
    """
    Pentru fiecare aliment recomandat: alte alimente din aceeași listă care acoperă același nutrient principal
    (deja compatibile cu profilul pacientului, deci alternative valide).
    """
    out: Dict[int, List[int]] = {}
    ordered = [int(r["food_id"]) for r in rec_dicts]
    for fid in ordered:
        primary = (nutrients_by_food.get(fid) or [None])[0]
        if primary is None:
            out[fid] = []
            continue
        out[fid] = [
            other for other in ordered
            if other != fid and primary in (nutrients_by_food.get(other) or [])
        ][:MAX_ALTERNATIVES]
    return out
