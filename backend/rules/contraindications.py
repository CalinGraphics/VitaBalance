"""
Reguli de contraindicații — aplicate ÎNAINTE de scor.

Fiecare regulă are: un id stabil (salvat împreună cu recomandarea, ca să se vadă ce s-a exclus și de ce), condiția
în care se activează, efectul asupra alimentelor și sursa. Efectele posibile:
- `excludes(food)`  -> alimentul nu poate fi recomandat;
- `penalty(food)`   -> factor de scor < 1 (preferință, nu interdicție);
- `no_target`       -> nutrienți pe care NU îi creștem activ, chiar dacă par „în deficit”.

Pragurile marcate cu TODO sunt alegeri ale aplicației acolo unde sursa nu dă o cifră per aliment.
Aplicația oferă îndrumare generală; nu înlocuiește sfatul medicului.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, FrozenSet, List, Optional, Tuple

from domain.models import FoodItem
from services.nutrition.profile_context import ProfileContext


def per_portion(food: FoodItem, nutrient: str) -> Optional[float]:
    value = getattr(food, nutrient, None)
    if value is None or not food.portion_g:
        return None
    return float(value) * float(food.portion_g) / 100.0


def available_carbs_per_portion(food: FoodItem) -> Optional[float]:
    if food.carbs is None or not food.portion_g:
        return None
    return max(0.0, float(food.carbs) - float(food.fiber or 0)) * float(food.portion_g) / 100.0


@dataclass(frozen=True)
class Rule:
    id: str
    applies: Callable[[ProfileContext], bool]
    source: str
    excludes: Optional[Callable[[FoodItem], bool]] = None
    penalty: Optional[Callable[[FoodItem], float]] = None
    no_target: FrozenSet[str] = field(default_factory=frozenset)


def _has(cond: str) -> Callable[[ProfileContext], bool]:
    return lambda ctx: cond in ctx.conditions


def _any(*conds: str) -> Callable[[ProfileContext], bool]:
    return lambda ctx: any(c in ctx.conditions for c in conds)


# Praguri
VITAMIN_K_MAX_PER_PORTION_UG = 60.0   # TODO: alegere a aplicației (~AI 70 µg/zi); sursa cere aport constant, nu o cifră.
POTASSIUM_MAX_PER_PORTION_MG = 200.0  # NKF: alimentele cu > 200 mg potasiu/porție sunt „bogate în potasiu”.
PHOSPHORUS_HIGH_PER_PORTION_MG = 250.0  # TODO: KDOQI 2020 nu dă un prag per aliment; penalizare, nu excludere.
SODIUM_HIGH_PER_100G_MG = 600.0       # UK FSA/DH 2016: „high” > 1,5 g sare/100 g ≈ 600 mg sodiu/100 g.
AVAILABLE_CARBS_HIGH_PER_PORTION_G = 30.0  # TODO: aproximare a încărcăturii glicemice (nu avem indicele glicemic).

RULES: Tuple[Rule, ...] = (
    # --- Sarcină / imunitate scăzută ---
    # NHS, „Foods to avoid in pregnancy” (2023): pește și fructe de mare crude (sushi cu pește crud, stridii crude).
    # FDA, „Food Safety for Older Adults and People with Weakened Immune Systems” (2020): fără pește/fructe de mare crude.
    Rule("pregnancy_immuno_no_raw_animal", _any("pregnancy", "immunocompromised"),
         "NHS 2023 Foods to avoid in pregnancy; FDA 2020 Food safety for people with weakened immune systems",
         excludes=lambda f: f.has_flag("raw_animal")),
    # FDA/EPA, „Advice about Eating Fish” (2021), lista „Choices to Avoid” (pește-spadă, macrou regal, tilefish,
    # rechin, marlin, orange roughy, ton bigeye) — pentru persoanele însărcinate sau care alăptează.
    Rule("pregnancy_lactation_no_high_mercury", _any("pregnancy", "lactation"),
         "FDA/EPA 2021 Advice about Eating Fish",
         excludes=lambda f: f.has_flag("high_mercury")),
    # NHS 2023: fără ficat sau produse din ficat în sarcină (vitamina A preformată în cantități mari, teratogenă).
    Rule("pregnancy_no_liver", _has("pregnancy"), "NHS 2023 Foods to avoid in pregnancy (vitamin A)",
         excludes=lambda f: f.has_flag("liver")),
    # NHS 2023 și FDA 2020: brânzeturi moi cu mucegai (Brie, Camembert) — risc de Listeria monocytogenes.
    Rule("pregnancy_immuno_no_soft_mould_cheese", _any("pregnancy", "immunocompromised"),
         "NHS 2023; FDA 2020 (Listeria)",
         excludes=lambda f: f.has_flag("soft_mould_cheese")),
    # --- Anticoagulante antivitamină K (warfarină, acenocumarol) ---
    # NIH ODS, „Vitamin K – Health Professional Fact Sheet” (2021): aportul de vitamina K trebuie menținut constant;
    # creșterile mari reduc efectul warfarinei. Nu creștem activ vitamina K și evităm porțiile foarte bogate.
    Rule("anticoagulant_steady_vitamin_k", _has("anticoagulant"), "NIH ODS 2021 Vitamin K fact sheet",
         excludes=lambda f: (per_portion(f, "vitamin_k") or 0) > VITAMIN_K_MAX_PER_PORTION_UG,
         no_target=frozenset({"vitamin_k"})),
    # --- Boală cronică de rinichi / potasiu mare în analize ---
    # National Kidney Foundation, „Potassium and Your CKD Diet”: > 200 mg/porție = aliment bogat în potasiu.
    # KDOQI Clinical Practice Guideline for Nutrition in CKD, Am J Kidney Dis 2020;76(3 Suppl 1):S1 — potasiul și
    # fosforul se ajustează individual; proteinele se stabilesc cu medicul (nu le creștem activ).
    Rule("ckd_limit_potassium", lambda ctx: "ckd" in ctx.conditions or ctx.hyperkalemia,
         "NKF Potassium and your CKD diet; KDOQI 2020",
         excludes=lambda f: (per_portion(f, "potassium") or 0) > POTASSIUM_MAX_PER_PORTION_MG,
         no_target=frozenset({"potassium"})),
    Rule("ckd_limit_phosphorus", _has("ckd"), "KDOQI 2020",
         penalty=lambda f: 0.5 if (per_portion(f, "phosphorus") or 0) > PHOSPHORUS_HIGH_PER_PORTION_MG else 1.0,
         no_target=frozenset({"protein", "potassium"})),
    # --- Hemocromatoză ---
    # EASL Clinical Practice Guidelines on haemochromatosis, J Hepatol 2022;77:479: fără suplimente de fier sau
    # alimente fortificate cu fier; nu e nevoie de o dietă strictă. Nu recomandăm alimente PENTRU creșterea fierului
    # și excludem ficatul (cel mai concentrat în fier). CDC, „Vibrio vulnificus” (2023): risc crescut la persoanele
    # cu încărcare cu fier — fără fructe de mare crude.
    Rule("hemochromatosis_no_iron_boost", _has("hemochromatosis"), "EASL 2022 J Hepatol 77:479; CDC 2023 Vibrio",
         excludes=lambda f: f.has_flag("liver") or (f.has_flag("raw_animal") and f.animal_source == "shellfish"),
         no_target=frozenset({"iron"})),
    # --- Hipertensiune ---
    # WHO, „Guideline: Sodium intake for adults and children” (2012): < 2 g sodiu/zi. Excludem alimentele „high”
    # în sare după criteriile UK FSA/DH 2016 (> 600 mg sodiu/100 g).
    Rule("hypertension_limit_sodium", _has("hypertension"), "WHO 2012 sodium guideline; UK FSA/DH 2016 front-of-pack",
         excludes=lambda f: (f.sodium or 0) > SODIUM_HIGH_PER_100G_MG),
    # --- Diabet ---
    # ADA, „Standards of Care in Diabetes—2024”, secțiunea 5: carbohidrați din surse minim procesate, bogate în fibre;
    # reducerea zahărului adăugat. Fără indice glicemic în date, folosim carbohidrații disponibili per porție.
    Rule("diabetes_low_glycemic_load", _has("diabetes"), "ADA Standards of Care 2024, section 5",
         penalty=lambda f: (0.6 if (available_carbs_per_portion(f) or 0) > AVAILABLE_CARBS_HIGH_PER_PORTION_G else 1.0)
         * (0.3 if f.has_flag("added_sugar") else 1.0)),
    # --- Gută ---
    # ACR Guideline for the Management of Gout, Arthritis Care Res 2020;72:744: limitarea alimentelor bogate în purine
    # (organe, fructe de mare) și a cărnii roșii.
    Rule("gout_limit_purines", _has("gout"), "ACR 2020 gout guideline",
         excludes=lambda f: f.category_key in ("offal", "shellfish"),
         penalty=lambda f: 0.6 if f.category_key == "meat" else 1.0),
    # --- Colesterol ridicat / boli cardiovasculare ---
    # ESC Guidelines on cardiovascular disease prevention, Eur Heart J 2021;42:3227: limitarea cărnii procesate.
    Rule("cardiovascular_no_processed_meat", _has("cardiovascular"), "ESC 2021 CVD prevention guideline",
         excludes=lambda f: f.category_key == "processed_meat"),
)

RULES_BY_ID: Dict[str, Rule] = {r.id: r for r in RULES}

# --- Dietă (filtru strict) ---
DIET_EXCLUDED_ANIMALS = {
    "omnivore": set(),
    "pescatarian": {"meat", "poultry"},
    "vegetarian": {"meat", "poultry", "fish", "shellfish"},
    "vegan": {"meat", "poultry", "fish", "shellfish", "dairy", "egg"},
}


def active_rules(ctx: ProfileContext) -> List[Rule]:
    return [r for r in RULES if r.applies(ctx)]


def no_target_nutrients(rules: List[Rule]) -> FrozenSet[str]:
    out: set = set()
    for r in rules:
        out |= r.no_target
    return frozenset(out)


def exclusion_reasons(food: FoodItem, ctx: ProfileContext, rules: List[Rule]) -> List[str]:
    """Id-urile motivelor pentru care alimentul nu poate fi recomandat (listă goală = permis)."""
    reasons: List[str] = []
    if food.animal_source in DIET_EXCLUDED_ANIMALS.get(ctx.diet, set()):
        reasons.append(f"diet_{ctx.diet}")
    blocked = set(food.allergen_codes) & set(ctx.allergies)
    reasons.extend(f"allergy_{a}" for a in sorted(blocked))
    reasons.extend(r.id for r in rules if r.excludes is not None and r.excludes(food))
    return reasons


def penalty_factors(food: FoodItem, rules: List[Rule]) -> List[Tuple[str, float]]:
    out = []
    for r in rules:
        if r.penalty is not None:
            factor = r.penalty(food)
            if factor < 1.0:
                out.append((r.id, factor))
    return out
