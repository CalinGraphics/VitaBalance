"""
Stările raportate de utilizator (greață, amețeli, oboseală...) — ce face aplicația cu ele.

Un simptom NU e un deficit și nu se transformă niciodată într-o nevoie de nutrient (deficitele vin doar din analize
sau din afirmații explicite, vezi services/nutrition/needs.py). Simptomele recente (ultimele RECENT_DAYS zile) pot:
- ajusta alegerea alimentelor pentru confort (ex. mai puțin gras la greață) — factori de scor, cu sursă;
- sugera ce analize să discute utilizatorul cu medicul, dacă nu le are deja;
- recomanda un consult medical când sunt puternice sau persistente.
Aplicația oferă îndrumare generală; nu pune diagnostice.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable, Dict, FrozenSet, Iterable, List, Optional, Tuple

from domain.models import FoodItem

RECENT_DAYS = 14
PERSISTENT_DAYS = 4          # același simptom în ≥ 4 zile din ultimele 14 -> consult medical
FAT_HIGH_PER_PORTION_G = 15.0
FIBER_GOOD_PER_PORTION_G = 3.0

SYMPTOM_CODES: Tuple[str, ...] = (
    "greata", "varsaturi", "ameteli", "oboseala", "dureri_cap", "crampe_musculare",
    "constipatie", "diaree", "balonare", "arsuri", "lipsa_poftei",
)

GAS_FORMING_KEYS = {"onion", "cabbage", "brussels_sprouts", "broccoli_raw", "broccoli_cooked", "cauliflower"}


def _per_portion(food: FoodItem, attr: str) -> float:
    v = getattr(food, attr, None)
    return 0.0 if v is None or not food.portion_g else float(v) * float(food.portion_g) / 100.0


@dataclass(frozen=True)
class SymptomRule:
    symptom: str
    id: str
    source: str
    factor: Optional[Callable[[FoodItem], float]] = None     # <1 penalizare, >1 preferință
    lab_hints: Tuple[str, ...] = ()                          # markeri de discutat cu medicul, dacă lipsesc


def _low_fat(food: FoodItem) -> float:
    return 0.6 if _per_portion(food, "fat") > FAT_HIGH_PER_PORTION_G else 1.0


SYMPTOM_RULES: Tuple[SymptomRule, ...] = (
    # NHS, „Feeling sick (nausea)” (2023): mese mici, alimente ușoare; evită mâncarea grasă, prăjită sau condimentată.
    SymptomRule("greata", "nausea_lighter_foods", "NHS 2023 Feeling sick (nausea)", factor=_low_fat),
    SymptomRule("lipsa_poftei", "appetite_lighter_foods", "NHS 2023 Feeling sick (nausea)", factor=_low_fat),
    # NHS, „Diarrhoea and vomiting” (2023): mese mici și ușoare; consult dacă vărsăturile durează peste 2 zile.
    SymptomRule("varsaturi", "vomiting_lighter_foods", "NHS 2023 Diarrhoea and vomiting", factor=_low_fat),
    SymptomRule("diaree", "diarrhoea_lighter_foods", "NHS 2023 Diarrhoea and vomiting", factor=_low_fat),
    # NHS, „Heartburn and acid reflux” (2023): mâncarea grasă și ciocolata pot agrava simptomele.
    SymptomRule("arsuri", "heartburn_less_fat_chocolate", "NHS 2023 Heartburn and acid reflux",
                factor=lambda f: _low_fat(f) * (0.5 if f.food_key in ("dark_chocolate", "milk_chocolate") else 1.0)),
    # NHS, „Constipation” (2023): mai multe fibre și lichide.
    SymptomRule("constipatie", "constipation_more_fibre", "NHS 2023 Constipation",
                factor=lambda f: 1.2 if _per_portion(f, "fiber") >= FIBER_GOOD_PER_PORTION_G else 1.0),
    # NHS, „Bloating” (2023): unele alimente produc gaze (fasole, varză, ceapă, broccoli).
    SymptomRule("balonare", "bloating_fewer_gassy_foods", "NHS 2023 Bloating",
                factor=lambda f: 0.8 if (f.category_key == "legumes" or f.food_key in GAS_FORMING_KEYS) else 1.0),
    # NHS, „Tiredness and fatigue” (2023): medicul poate cere analize pentru anemie și alte cauze.
    SymptomRule("oboseala", "fatigue_lab_hints", "NHS 2023 Tiredness and fatigue",
                lab_hints=("hemoglobin", "ferritin", "vitamin_b12", "vitamin_d")),
    # NHS, „Iron deficiency anaemia” (2023): amețelile pot fi un semn de anemie.
    SymptomRule("ameteli", "dizziness_lab_hints", "NHS 2023 Iron deficiency anaemia", lab_hints=("hemoglobin", "ferritin")),
    # MedlinePlus, „Muscle cramps” (2023): nivelurile scăzute de potasiu, calciu sau magneziu pot da crampe.
    SymptomRule("crampe_musculare", "cramps_lab_hints", "MedlinePlus 2023 Muscle cramps",
                lab_hints=("magnesium", "potassium", "calcium")),
)
RULES_BY_SYMPTOM: Dict[str, List[SymptomRule]] = {}
for _r in SYMPTOM_RULES:
    RULES_BY_SYMPTOM.setdefault(_r.symptom, []).append(_r)


@dataclass(frozen=True)
class CheckInLike:
    checked_on: date
    symptoms: Tuple[str, ...]
    severity: Optional[int] = None


@dataclass(frozen=True)
class SymptomInsights:
    recent: FrozenSet[str] = frozenset()
    lab_suggestions: Tuple[str, ...] = ()
    see_doctor: bool = False
    see_doctor_reasons: Tuple[str, ...] = ()
    adjustments: Tuple[str, ...] = ()        # id-urile regulilor care schimbă recomandările


def _as_date(v) -> date:
    return v if isinstance(v, date) else date.fromisoformat(str(v)[:10])


def recent_checkins(checkins: Iterable, today: Optional[date] = None) -> List[CheckInLike]:
    today = today or date.today()
    start = today - timedelta(days=RECENT_DAYS - 1)
    out = []
    for c in checkins:
        d = _as_date(c.checked_on)
        if start <= d <= today:
            out.append(CheckInLike(d, tuple(s for s in (c.symptoms or ()) if s in SYMPTOM_CODES), c.severity))
    return out


def analyse(checkins: Iterable, lab_values: Dict[str, Optional[float]], today: Optional[date] = None) -> SymptomInsights:
    recent = recent_checkins(checkins, today)
    symptoms = frozenset(s for c in recent for s in c.symptoms)
    reasons: List[str] = []
    if any(c.severity == 3 and c.symptoms for c in recent):
        reasons.append("severe")
    days_with = {s: sum(1 for c in recent if s in c.symptoms) for s in symptoms}
    if any(n >= PERSISTENT_DAYS for n in days_with.values()):
        reasons.append("persistent")
    vomiting_days = sorted(c.checked_on for c in recent if "varsaturi" in c.symptoms)
    if len(vomiting_days) >= 2 and (vomiting_days[-1] - vomiting_days[0]).days <= 2:
        reasons.append("vomiting_2_days")  # NHS: consult dacă vărsăturile durează peste 2 zile
    hints: List[str] = []
    for s in sorted(symptoms):
        for r in RULES_BY_SYMPTOM.get(s, []):
            hints.extend(m for m in r.lab_hints if lab_values.get(m) is None and m not in hints)
    adjustments = tuple(r.id for s in sorted(symptoms) for r in RULES_BY_SYMPTOM.get(s, []) if r.factor is not None)
    return SymptomInsights(symptoms, tuple(hints), bool(reasons), tuple(reasons), adjustments)


def symptom_factors(food: FoodItem, symptoms: FrozenSet[str]) -> List[Tuple[str, float]]:
    """
    Același sfat („mâncare mai puțin grasă”) se aplică o singură dată, oricâte simptome îl cer: greața, vărsăturile
    și diareea împreună nu fac un aliment gras de trei ori mai puțin potrivit (0,6³ ≈ 0,2).
    """
    out = []
    applied = set()
    for s in sorted(symptoms):
        for r in RULES_BY_SYMPTOM.get(s, []):
            if r.factor is not None and r.factor not in applied:
                applied.add(r.factor)
                f = r.factor(food)
                if f != 1.0:
                    out.append((r.id, f))
    return out
