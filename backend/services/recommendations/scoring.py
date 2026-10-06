"""
Scorul și ierarhizarea recomandărilor — sistem bazat pe reguli, explicabil.

Pentru fiecare aliment permis (după filtrele de dietă, alergii, restricții scrise și contraindicații):

1. Pentru fiecare nevoie n (deficit din analize sau din observații):
     densitate_n   = (cantitatea la 100 kcal) / necesarul zilnic EFSA      -> fracție din necesar la 100 kcal
     porție_n      = (cantitatea în porția realistă) / necesarul zilnic    -> fracție din necesar per porție
   Nutrientul „contează” doar dacă porția acoperă cel puțin MIN_PORTION_SHARE din necesar (altfel urmele dintr-un
   aliment ar ridica scorul) și dacă valoarea e cunoscută (None = exclus de la scorul pentru acel nutrient).
     contribuție_n = pondere_severitate_n × min(densitate_n, DENSITY_CAP)
2. scor_bază = Σ contribuții; bonus pentru deficite multiple: × (1 + MULTI_DEFICIT_BONUS × (k − 1)).
3. Penalizări de calitate (ultraprocesat, făină rafinată, zahăr adăugat, sare multă) și penalizările regulilor de
   contraindicații (ex. diabet); feedback-ul utilizatorului (like/dislike).

Fiecare cifră de mai sus e salvată în `trace`, împreună cu recomandarea. Ponderile sunt constantele de mai jos:
schimbarea lor cere actualizarea testelor golden (tests/golden) și o explicație în commit.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, FrozenSet, Iterable, List, Optional, Tuple

from domain.models import FoodItem
from rules.contraindications import active_rules, exclusion_reasons, no_target_nutrients, penalty_factors
from services.nutrition.needs import NUTRIENTS, Need, NeedsResult
from data.reference_values import reference_intake

SCORING_VERSION = 1

DENSITY_CAP = 1.0            # o densitate peste 100% din necesar la 100 kcal nu mai adaugă (evită ficatul „infinit”)
MIN_PORTION_SHARE = 0.10     # porția trebuie să aducă ≥ 10% din necesarul zilnic ca nutrientul să conteze
MULTI_DEFICIT_BONUS = 0.25   # +25% pentru fiecare deficit acoperit în plus
MIN_KCAL_FOR_DENSITY = 10.0  # sub 10 kcal/100 g densitatea „la 100 kcal” explodează; folosim 10 ca podea

# Penalizări de calitate (alegeri ale aplicației; sursele motivează direcția, nu mărimea factorului):
# - ultraprocesat: Lane et al., BMJ 2024;384:e077310 (umbrella review, asocieri cu efecte adverse);
# - făină rafinată: WHO, „Healthy diet” fact sheet (2020) — cereale integrale în locul celor rafinate;
# - zahăr adăugat: WHO, „Guideline: Sugars intake for adults and children” (2015);
# - sare: UK FSA/DH 2016, „high” > 600 mg sodiu/100 g.
QUALITY_PENALTIES = {
    # crude de origine animală: FDA, „Food safety for older adults and people with weakened immune systems” (2020) —
    # risc microbiologic (Vibrio, Listeria); pentru grupele cu risc ridicat sunt excluse în rules/contraindications.py.
    "raw_animal": 0.7,
    "ultra_processed": 0.5,
    "refined_grain": 0.7,
    "added_sugar": 0.6,
    "high_sodium": 0.7,
}
HIGH_SODIUM_PER_100G = 600.0

# Biodisponibilitate: în legumele bogate în oxalați fierul și calciul se absorb slab (Gillooly et al., Br J Nutr
# 1983;49:331 — fier; Weaver et al., J Food Sci 1987;52:1029 — calciu din spanac ~5% față de ~27% din lapte).
# Factorul 0,5 e alegerea aplicației (direcția e susținută de surse, mărimea nu).
OXALATE_BIOAVAILABILITY = {"iron": 0.5, "calcium": 0.5}

MAX_PER_CATEGORY = 3          # diversitate: maximum 3 alimente din aceeași categorie
# Categorii de consumat rar: cel mult un aliment pe listă. Ficat: NHS, „Vitamin A” (2023) — cel mult o dată pe
# săptămână; mezeluri, dulciuri, patiserie: aceleași motive ca penalizările de calitate de mai sus.
CATEGORY_CAPS = {"offal": 1, "processed_meat": 1, "sweets_snacks": 1, "bakery": 1}
MAX_RECOMMENDATIONS = 20
MIN_RECOMMENDATIONS = 10
MAX_ALTERNATIVES = 3
FILL_SCORE_FACTOR = 0.5       # completările „generale” stau mereu după alimentele care acoperă un deficit

FEEDBACK_FACTORS = {"like": 1.2, "dislike": 0.4}


@dataclass
class Component:
    nutrient: str
    per100: float
    per100kcal: float
    daily_reference: float
    density: float
    portion_amount: float
    portion_share: float
    weight: float
    contribution: float
    bioavailability: float = 1.0

    def to_dict(self) -> dict:
        r = lambda v: round(v, 4)  # noqa: E731
        return {"nutrient": self.nutrient, "per100": r(self.per100), "per100kcal": r(self.per100kcal),
                "daily_reference": self.daily_reference, "density": r(self.density),
                "portion_amount": r(self.portion_amount), "portion_share": r(self.portion_share),
                "weight": self.weight, "bioavailability": self.bioavailability, "contribution": r(self.contribution)}


@dataclass
class ScoredFood:
    food: FoodItem
    score: float
    components: List[Component]       # doar nutrienții care contează (porție ≥ prag)
    penalties: List[Tuple[str, float]]
    bonus: float
    feedback_factor: float
    fill: bool = False                # completare generală (fără deficit acoperit)
    alternatives: List[int] = field(default_factory=list)

    @property
    def primary(self) -> Optional[Component]:
        return max(self.components, key=lambda c: c.contribution) if self.components else None

    @property
    def coverage_pct(self) -> float:
        """% din necesarul zilnic al nutrientului principal acoperit de porție (aceeași cifră peste tot în UI)."""
        p = self.primary
        return round(min(100.0, p.portion_share * 100), 1) if p else 0.0

    def trace(self, rule_ids: Iterable[str]) -> dict:
        return {
            "v": SCORING_VERSION,
            "score": round(self.score, 4),
            "components": [c.to_dict() for c in self.components],
            "multi_deficit_bonus": round(self.bonus, 4),
            "penalties": [{"id": pid, "factor": f} for pid, f in self.penalties],
            "feedback_factor": self.feedback_factor,
            "fill": self.fill,
            "active_rules": sorted(rule_ids),
            "constants": {"density_cap": DENSITY_CAP, "min_portion_share": MIN_PORTION_SHARE,
                          "multi_deficit_bonus": MULTI_DEFICIT_BONUS},
        }


def _value(food: FoodItem, nutrient: str) -> Optional[float]:
    v = getattr(food, nutrient, None)
    return None if v is None else float(v)


def _component(food: FoodItem, nutrient: str, daily_ref: float, weight: float) -> Optional[Component]:
    v100 = _value(food, nutrient)
    kcal = _value(food, "calories")
    if v100 is None or v100 <= 0 or kcal is None or daily_ref <= 0 or not food.portion_g:
        return None
    per100kcal = v100 / max(kcal, MIN_KCAL_FOR_DENSITY) * 100.0
    density = per100kcal / daily_ref
    amount = v100 * food.portion_g / 100.0
    share = amount / daily_ref
    if share < MIN_PORTION_SHARE:
        return None
    bio = OXALATE_BIOAVAILABILITY.get(nutrient, 1.0) if food.has_flag("high_oxalate") else 1.0
    return Component(nutrient, v100, per100kcal, daily_ref, density, amount, share, weight,
                     weight * min(density, DENSITY_CAP) * bio, bio)


def quality_penalties(food: FoodItem) -> List[Tuple[str, float]]:
    out = [(flag, QUALITY_PENALTIES[flag]) for flag in ("raw_animal", "ultra_processed", "refined_grain", "added_sugar")
           if food.has_flag(flag)]
    if (food.sodium or 0) > HIGH_SODIUM_PER_100G:
        out.append(("high_sodium", QUALITY_PENALTIES["high_sodium"]))
    return out


@dataclass
class Ranking:
    items: List[ScoredFood]
    needs: List[Need]
    targeted: List[Need]
    rule_ids: List[str]
    excluded: Dict[int, List[str]]     # food_id -> motive (pentru audit/teste)
    eligible: List[ScoredFood]         # toate alimentele permise, cu scor (pentru alternative)
    diet: str = "omnivore"
    allergies: FrozenSet[str] = frozenset()
    conditions: FrozenSet[str] = frozenset()


def rank_foods(
    foods: Iterable[FoodItem],
    needs_result: NeedsResult,
    *,
    text_allows: Optional[Callable[[FoodItem], bool]] = None,
    feedback: Optional[Dict[int, str]] = None,
) -> Ranking:
    ctx = needs_result.context
    rules = active_rules(ctx)
    blocked = no_target_nutrients(rules)
    targeted = [n for n in needs_result.needs if n.nutrient not in blocked]
    feedback = feedback or {}

    excluded: Dict[int, List[str]] = {}
    scored: List[ScoredFood] = []
    for food in foods:
        if not food.validated:
            continue
        reasons = exclusion_reasons(food, ctx, rules)
        if text_allows is not None and not text_allows(food):
            reasons.append("user_text_restriction")
        if reasons:
            excluded[food.id] = reasons
            continue
        if targeted:
            comps = [c for n in targeted if (c := _component(food, n.nutrient, n.daily_reference, n.weight))]
        else:
            comps = _general_components(food, ctx)
        base = sum(c.contribution for c in comps)
        bonus = 1.0 + MULTI_DEFICIT_BONUS * (len(comps) - 1) if targeted and len(comps) > 1 else 1.0
        penalties = quality_penalties(food) + penalty_factors(food, rules)
        factor = 1.0
        for _, f in penalties:
            factor *= f
        fb = FEEDBACK_FACTORS.get(feedback.get(food.id, ""), 1.0)
        scored.append(ScoredFood(food, base * bonus * factor * fb, comps, penalties, bonus, fb))

    scored.sort(key=lambda s: (-s.score, s.food.food_key or "", s.food.id))
    covering = [s for s in scored if s.components and s.score > 0]
    items = _diversify(covering)

    if len(items) < MIN_RECOMMENDATIONS and targeted:
        # Prea puține alimente acoperă deficitele (ex. vegan + alergii): completăm cu alimente dense nutritiv,
        # marcate ca „fill”, cu scor mereu sub ultimul aliment care acoperă un deficit.
        floor = min((s.score for s in items), default=1.0)
        general = []
        for s in scored:
            if s in items:
                continue
            comps = _general_components(s.food, ctx)
            g = sum(c.contribution for c in comps) / len(NUTRIENTS)
            if g <= 0:
                continue
            general.append(_fill(s, comps, g))
        general.sort(key=lambda s: (-s.score, s.food.food_key or ""))
        top_g = max((s.score for s in general), default=1.0) or 1.0
        for s in general:
            s.score = floor * FILL_SCORE_FACTOR * (s.score / top_g)
        items = _diversify(items + general)

    for s in items:
        s.alternatives = _alternatives(s, scored)
    return Ranking(items=items, needs=needs_result.needs, targeted=targeted, rule_ids=[r.id for r in rules],
                   excluded=excluded, eligible=scored, diet=ctx.diet, allergies=ctx.allergies,
                   conditions=ctx.conditions)


def _fill(s: ScoredFood, comps: List[Component], g: float) -> ScoredFood:
    factor = 1.0
    for _, f in s.penalties:
        factor *= f
    return ScoredFood(s.food, g * factor * s.feedback_factor, comps, s.penalties, 1.0, s.feedback_factor, fill=True)


def _general_components(food: FoodItem, ctx) -> List[Component]:
    """Fără deficite: contribuția la necesarul zilnic al tuturor micronutrienților cunoscuți (pondere 1)."""
    comps = []
    for n in NUTRIENTS:
        ref = reference_intake(n, sex=ctx.sex, age=ctx.age, weight_kg=ctx.weight_kg, pregnant=ctx.pregnant,
                               lactating=ctx.lactating, diet=ctx.diet)
        c = _component(food, n, float(ref or 0), 1.0)
        if c:
            comps.append(c)
    return comps


def _diversify(ordered: List[ScoredFood]) -> List[ScoredFood]:
    """Păstrează ordinea după scor și maximum MAX_PER_CATEGORY pe categorie (lista rămâne descrescătoare)."""
    ordered = sorted(ordered, key=lambda s: (-s.score, s.food.food_key or "", s.food.id))
    out: List[ScoredFood] = []
    per_cat: Dict[str, int] = {}
    for s in ordered:
        cat = s.food.category_key or "other"
        if per_cat.get(cat, 0) >= CATEGORY_CAPS.get(cat, MAX_PER_CATEGORY):
            continue
        out.append(s)
        per_cat[cat] = per_cat.get(cat, 0) + 1
        if len(out) >= MAX_RECOMMENDATIONS:
            break
    return out


def _alternatives(item: ScoredFood, eligible: List[ScoredFood]) -> List[int]:
    """Aceeași categorie, același nutrient principal (porție ≥ prag), aceleași filtre (doar alimente permise)."""
    primary = item.primary
    if primary is None:
        return []
    out = []
    for s in eligible:  # deja ordonate după scor
        if s.food.id == item.food.id or s.food.category_key != item.food.category_key:
            continue
        if any(c.nutrient == primary.nutrient for c in s.components):
            out.append(s.food.id)
        if len(out) >= MAX_ALTERNATIVES:
            break
    return out
