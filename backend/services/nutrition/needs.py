"""
Nevoile nutriționale ale utilizatorului — de unde vin și cât de serioase sunt.

Un deficit poate veni DOAR din:
  (a) o valoare de laborator sub limita minimă (source = "lab"), sau
  (b) o afirmație explicită a utilizatorului în profil / observații (source = "notes"), de tipul
      „deficit de magneziu”, „vitamina D scăzută”, „anemie feriprivă” sau codurile de profil
      (anemie, deficienta_vitamin_d, deficienta_b12).
Nu mai estimăm deficite din profil („aport estimat”) și nu tratăm simpla mențiune a unui nutrient ca nevoie
(„iau vitamina D” NU e un deficit).

Când există o valoare de laborator în interval pentru același nutrient, ea are prioritate față de text: analiza e
obiectivă, iar afirmația poate fi veche. Hemocromatoza anulează orice nevoie de fier.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

from data.lab_ranges import LAB_RANGES, MILD, SEVERITY_WEIGHT, severity_for
from data.reference_values import reference_intake
from domain.models import LabResultItem, UserProfile
from services.nutrition.profile_context import ProfileContext, build_profile_context, user_text

NUTRIENTS = (
    "iron", "calcium", "vitamin_d", "vitamin_b12", "magnesium", "protein", "zinc", "folate",
    "vitamin_a", "vitamin_c", "iodine", "vitamin_k", "potassium",
)

# Pentru fier: feritina (rezervele) are prioritate față de hemoglobină.
LAB_MARKERS_BY_NUTRIENT: Dict[str, List[str]] = {
    "iron": ["ferritin", "hemoglobin"],
    **{n: [n] for n in ("calcium", "vitamin_d", "vitamin_b12", "magnesium", "protein", "zinc", "folate",
                        "vitamin_a", "vitamin_c", "iodine", "potassium")},
}

_NUTRIENT_WORDS = {
    "iron": r"fier|iron",
    "calcium": r"calciu|calcium",
    "vitamin_d": r"vitamina d|vitamin d|vit d|vit\. d",
    "vitamin_b12": r"vitamina b12|vitamin b12|b12|cobalamina",
    "magnesium": r"magneziu|magnesium",
    "protein": r"proteine|protein",
    "zinc": r"zinc",
    "folate": r"folat|acid folic|vitamina b9|folate",
    "vitamin_a": r"vitamina a|vitamin a",
    "vitamin_c": r"vitamina c|vitamin c",
    "iodine": r"iod|iodine",
    "vitamin_k": r"vitamina k|vitamin k",
    "potassium": r"potasiu|potassium",
}
_DEFICIT_BEFORE = r"(deficit|deficienta|carenta|lipsa|insuficienta|nivel scazut|niveluri scazute|am nevoie de( mai mult)?|deficiency of|low)"
_DEFICIT_AFTER = r"(scazut|scazuta|scazute|redus|redusa|sub limita|sub interval|deficiency|deficient|low)"
_EXTRA_EXPLICIT = {
    "iron": r"\b(anemie feripriva|anemie prin deficit de fier|iron deficiency anaemia|iron deficiency anemia|sideropeni\w*)\b",
    "vitamin_d": r"\bhipovitaminoza d\b",
    "magnesium": r"\bhipomagneziemi\w*\b",
    "potassium": r"\bhipokaliemi\w*\b",
    "calcium": r"\bhipocalcemi\w*\b",
}
# Codurile de profil care sunt afirmații explicite (vezi medicalConditions.ts)
PROFILE_CODE_NEEDS = {"anemie": "iron", "deficienta_vitamin_d": "vitamin_d", "deficienta_b12": "vitamin_b12"}


@dataclass(frozen=True)
class Need:
    nutrient: str
    source: str                     # "lab" | "notes"
    severity: str                   # mild | moderate | severe
    daily_reference: float          # necesarul zilnic EFSA, în unitatea catalogului
    marker: Optional[str] = None    # doar pentru "lab"
    value: Optional[float] = None
    threshold: Optional[float] = None
    unit: Optional[str] = None

    @property
    def weight(self) -> float:
        return SEVERITY_WEIGHT[self.severity]

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass(frozen=True)
class NeedsResult:
    needs: List[Need]
    context: ProfileContext
    # nutrienți de limitat (nu de crescut), din analize: ex. {"potassium": "lab_high"}
    limits: Dict[str, str]

    def by_nutrient(self) -> Dict[str, Need]:
        return {n.nutrient: n for n in self.needs}


def explicit_note_nutrients(user: UserProfile, lab_results: Optional[LabResultItem]) -> List[str]:
    """Nutrienții pentru care utilizatorul a afirmat explicit o nevoie (text sau cod de profil)."""
    text = user_text(user, lab_results)
    codes = {c.strip().lower() for c in (user.medical_conditions or "").split(",") if c.strip()}
    found = [PROFILE_CODE_NEEDS[c] for c in codes if c in PROFILE_CODE_NEEDS]
    for nutrient, words in _NUTRIENT_WORDS.items():
        patterns = [rf"\b{_DEFICIT_BEFORE} (de |of )?({words})\b", rf"\b({words}) (seric(a)? |serum )?{_DEFICIT_AFTER}\b"]
        if nutrient in _EXTRA_EXPLICIT:
            patterns.append(_EXTRA_EXPLICIT[nutrient])
        if any(_affirmed(m, text) for p in patterns for m in re.finditer(p, text)):
            found.append(nutrient)
    return list(dict.fromkeys(found))


_NEGATION = re.compile(r"\b(nu am|nu are|nu mai am|fara|no|not)\s*$")


def _affirmed(match: re.Match, text: str) -> bool:
    """„nu am deficit de fier” / „fără anemie feriprivă” nu sunt afirmații de nevoie."""
    return not _NEGATION.search(text[max(0, match.start() - 12):match.start()])


def _reference(nutrient: str, ctx: ProfileContext) -> float:
    return float(reference_intake(nutrient, sex=ctx.sex, age=ctx.age, weight_kg=ctx.weight_kg,
                                  pregnant=ctx.pregnant, lactating=ctx.lactating, diet=ctx.diet) or 0)


def detect_needs(user: UserProfile, lab_results: Optional[LabResultItem] = None) -> NeedsResult:
    ctx = build_profile_context(user, lab_results)
    needs: Dict[str, Need] = {}
    lab_in_range: set[str] = set()

    if lab_results is not None:
        for nutrient, markers in LAB_MARKERS_BY_NUTRIENT.items():
            for marker in markers:
                value = getattr(lab_results, marker, None)
                if value is None:
                    continue
                lab = LAB_RANGES[marker]
                severity = severity_for(lab, float(value), ctx.sex, ctx.pregnant)
                if severity is None:
                    lab_in_range.add(nutrient)
                else:
                    needs[nutrient] = Need(nutrient, "lab", severity, _reference(nutrient, ctx), marker=marker,
                                           value=float(value), threshold=lab.low(ctx.sex, ctx.pregnant), unit=lab.unit)
                break  # primul marker disponibil decide (feritina înaintea hemoglobinei)

    for nutrient in explicit_note_nutrients(user, lab_results):
        if nutrient in needs or nutrient in lab_in_range:
            continue
        # Fără o valoare de laborator nu știm cât de mare e deficitul: îl tratăm ca ușor.
        needs[nutrient] = Need(nutrient, "notes", MILD, _reference(nutrient, ctx))

    limits: Dict[str, str] = {}
    if ctx.hyperkalemia:
        limits["potassium"] = "lab_high"
        needs.pop("potassium", None)
    if "hemochromatosis" in ctx.conditions:
        needs.pop("iron", None)

    ordered = sorted(needs.values(), key=lambda n: (-n.weight, NUTRIENTS.index(n.nutrient)))
    return NeedsResult(needs=ordered, context=ctx, limits=limits)
