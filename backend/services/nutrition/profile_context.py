"""
Contextul clinic al utilizatorului, într-o formă structurată: etapa de viață, afecțiunile cu reguli alimentare,
dieta și alergiile. Sursele, în ordine:
1. codurile alese în profil (users.medical_conditions = „cod1, cod2, …”, valorile din
   frontend/src/shared/constants/medicalConditions.ts);
2. textul liber scris de utilizator (profil + observațiile de la analize) — pentru profilurile vechi și pentru
   cine scrie în loc să bifeze. Potrivirea e pe cuvinte întregi, fără diacritice.
3. analizele (ex. potasiu peste interval => restricție de potasiu).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import FrozenSet, Optional

from domain.models import LabResultItem, UserProfile
from services.rules.medical_rules_loader import normalize_clinical_text, resolve_allergy_token

# Coduri de profil -> condiție internă
CONDITION_CODES = {
    "sarcina": "pregnancy",
    "alaptare": "lactation",
    "anticoagulante": "anticoagulant",
    "hemocromatoza": "hemochromatosis",
    "imunitate_scazuta": "immunocompromised",
    "insuficienta_renala": "ckd",
    "hipertensiune": "hypertension",
    "diabet": "diabetes",
    "celiachie": "celiac",
    "gout": "gout",
    "colesterol_ridicat": "cardiovascular",
    "boli_cardiovasculare": "cardiovascular",
}

# Text liber (normalizat, fără diacritice) -> condiție internă
TEXT_PATTERNS = {
    "pregnancy": r"\b(insarcinata|gravida|sarcina|sarcinii|pregnant|pregnancy)\b",
    "lactation": r"\b(alaptez|alaptare|breastfeeding|lactation)\b",
    "anticoagulant": r"\b(warfarin\w*|acenocumarol\w*|sintrom|trombostop|anticoagulant\w*|coumadin)\b",
    "hemochromatosis": r"\b(hemocromatoz\w*|haemochromatosis|hemochromatosis)\b",
    "immunocompromised": r"\b(imunosupres\w*|imunitate scazuta|chimioterapie|transplant\w*|immunocompromised)\b",
    "ckd": r"\b(boala cronica de rinichi|boala renala|insuficienta renala|nefropat\w*|dializ\w*|ckd)\b",
    "hypertension": r"\b(hipertensiun\w*|hta|tensiune mare|hypertension)\b",
    "diabetes": r"\b(diabet\w*|prediabet\w*|diabetes)\b",
    "celiac": r"\b(celiachie|boala celiaca|celiac)\b",
    "gout": r"\b(guta|gout|hiperuricemi\w*)\b",
    "cardiovascular": r"\b(colesterol (ridicat|mare|marit)|hipercolesterolemi\w*|dislipidemi\w*|boli cardiovasculare)\b",
}


@dataclass(frozen=True)
class ProfileContext:
    sex: str                      # "M" | "F" | "other"
    age: int
    weight_kg: Optional[float]
    diet: str                     # omnivore | vegetarian | vegan | pescatarian
    allergies: FrozenSet[str]
    conditions: FrozenSet[str] = field(default_factory=frozenset)
    hyperkalemia: bool = False

    @property
    def pregnant(self) -> bool:
        return "pregnancy" in self.conditions

    @property
    def lactating(self) -> bool:
        return "lactation" in self.conditions


def normalized_sex(raw: Optional[str]) -> str:
    s = normalize_clinical_text(raw or "")
    if s in ("m", "male", "man", "masculin", "barbat"):
        return "M"
    if s in ("f", "female", "woman", "feminin", "femeie"):
        return "F"
    return "other"


def normalized_diet(raw: Optional[str]) -> str:
    d = (raw or "").strip().lower()
    return d if d in ("omnivore", "vegetarian", "vegan", "pescatarian") else "omnivore"


def user_text(user: UserProfile, lab_results: Optional[LabResultItem]) -> str:
    """Textul scris de utilizator (afecțiuni din profil + observații analize), normalizat."""
    notes = getattr(lab_results, "notes", None) if lab_results is not None else None
    return normalize_clinical_text(f"{user.medical_conditions or ''} {notes or ''}")


def build_profile_context(user: UserProfile, lab_results: Optional[LabResultItem] = None) -> ProfileContext:
    sex = normalized_sex(user.sex)
    codes = {c.strip().lower() for c in (user.medical_conditions or "").split(",") if c.strip()}
    conditions = {CONDITION_CODES[c] for c in codes if c in CONDITION_CODES}
    text = user_text(user, lab_results)
    for cond, pattern in TEXT_PATTERNS.items():
        if re.search(pattern, text):
            conditions.add(cond)
    if sex == "M":
        conditions.discard("pregnancy")
        conditions.discard("lactation")
    allergies = frozenset(
        resolve_allergy_token(normalize_clinical_text(a)) for a in (user.allergies or "").split(",") if a.strip()
    )
    if "celiac" in conditions:
        allergies = allergies | {"gluten"}
    if re.search(r"\b(intoleranta la lactoza|intoleranta lactoza|lactose intolerance)\b", text):
        allergies = allergies | {"lactoza"}
    potassium = getattr(lab_results, "potassium", None) if lab_results is not None else None
    hyperkalemia = potassium is not None and float(potassium) > 5.0
    return ProfileContext(
        sex=sex,
        age=int(user.age or 30),
        weight_kg=float(user.weight) if user.weight else None,
        diet=normalized_diet(user.diet_type),
        allergies=allergies,
        conditions=frozenset(conditions),
        hyperkalemia=hyperkalemia,
    )
