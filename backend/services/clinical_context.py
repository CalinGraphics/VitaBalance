"""
Context clinic unificat: observații din analize + condiții profil → profil efectiv pentru recomandări.

Tag-urile din UI (MedicalLabResultsPage OBSERVATION_SUGGESTIONS) sunt mapate explicit aici,
astfel încât formulări precum „Nu pot consuma pește” să funcționeze la fel ca alergiile din profil.
"""
from __future__ import annotations

import re
from dataclasses import replace
from typing import Dict, List, Optional, Sequence, TypedDict

from domain.models import LabResultItem, UserProfile
from services.medical_rules_loader import normalize_clinical_text


class ObservationRule(TypedDict, total=False):
    match_any: List[str]
    allergy_tokens: List[str]
    condition_codes: List[str]
    restriction_phrases: List[str]


# Aliniat cu frontend/src/features/medical/pages/MedicalLabResultsPage.tsx (OBSERVATION_SUGGESTIONS)
OBSERVATION_TAG_RULES: List[ObservationRule] = [
    {
        "match_any": ["anemie feripriva confirmata", "anemie feripriva"],
        "condition_codes": ["anemie"],
    },
    {
        "match_any": ["deficienta de vitamina d", "deficit de vitamina d"],
    },
    {
        "match_any": ["deficienta de vitamina b12", "deficit de vitamina b12"],
    },
    {
        "match_any": ["deficienta de magneziu", "deficit de magneziu"],
    },
    {
        "match_any": ["deficienta de zinc", "deficit de zinc"],
    },
    {
        "match_any": ["deficienta de folat", "deficit de folat", "vitamina b9"],
    },
    {
        "match_any": ["deficienta de calciu", "deficit de calciu"],
    },
    {
        "match_any": ["deficienta de iod", "deficit de iod"],
    },
    {
        "match_any": ["deficienta de potasiu", "deficit de potasiu"],
    },
    {
        "match_any": ["intoleranta la lactoza", "intoleranta lactoza"],
        "allergy_tokens": ["lactoza"],
        "restriction_phrases": ["nu am voie lactate"],
    },
    {
        "match_any": [
            "intoleranta la gluten",
            "boala celiaca",
            "celiachie",
            "boala celiac",
        ],
        "allergy_tokens": ["gluten"],
        "condition_codes": ["celiachie"],
        "restriction_phrases": ["fara gluten"],
    },
    {
        "match_any": ["hipertensiune arteriala", "hipertensiune"],
        "condition_codes": ["hipertensiune"],
    },
    {
        "match_any": ["diabet zaharat", "prediabet", "diabet"],
        "condition_codes": ["diabet"],
    },
    {
        "match_any": ["reflux gastroesofagian", "reflux gastric", "reflux"],
        "condition_codes": ["reflux"],
    },
    {
        "match_any": [
            "boala renala cronica",
            "boala cronica de rinichi",
            "insuficienta renala",
        ],
        "condition_codes": ["insuficienta_renala"],
    },
    {
        "match_any": ["nu pot consuma peste", "nu pot consuma pesti"],
        "allergy_tokens": ["peste"],
        "restriction_phrases": ["nu mananc peste"],
    },
    {
        "match_any": ["nu pot consuma lactate", "nu pot consuma lapte"],
        "allergy_tokens": ["lactoza"],
        "restriction_phrases": ["nu am voie lactate"],
    },
    {
        "match_any": ["nu pot consuma seminte", "nu pot consuma seminte de"],
        "restriction_phrases": ["nu am voie seminte"],
    },
]

# Token singular după „nu pot consuma …”
CONSUMABLE_TOKEN_MAP: Dict[str, ObservationRule] = {
    "peste": {
        "allergy_tokens": ["peste"],
        "restriction_phrases": ["nu mananc peste"],
    },
    "pesti": {
        "allergy_tokens": ["peste"],
        "restriction_phrases": ["nu mananc peste"],
    },
    "lactate": {
        "allergy_tokens": ["lactoza"],
        "restriction_phrases": ["nu am voie lactate"],
    },
    "lapte": {
        "allergy_tokens": ["lactoza"],
        "restriction_phrases": ["nu am voie lactate"],
    },
    "seminte": {
        "restriction_phrases": ["nu am voie seminte"],
    },
    "semințe": {
        "restriction_phrases": ["nu am voie seminte"],
    },
    "oua": {
        "allergy_tokens": ["oua"],
        "restriction_phrases": ["nu mananc oua"],
    },
    "ou": {
        "allergy_tokens": ["oua"],
        "restriction_phrases": ["nu mananc oua"],
    },
    "nuci": {
        "allergy_tokens": ["nuci"],
        "restriction_phrases": ["nu mananc nuci"],
    },
    "soia": {
        "allergy_tokens": ["soia"],
        "restriction_phrases": ["nu mananc soia"],
    },
    "gluten": {
        "allergy_tokens": ["gluten"],
        "restriction_phrases": ["fara gluten"],
    },
    "carne": {
        "restriction_phrases": ["nu mananc carne"],
    },
    "pui": {
        "restriction_phrases": ["nu mananc pui"],
    },
    "porc": {
        "restriction_phrases": ["nu mananc porc"],
    },
}


def split_clinical_segments(text: str) -> List[str]:
    if not text or not text.strip():
        return []
    parts = re.split(r"[;\n|]+", text)
    return [p.strip() for p in parts if p.strip()]


def _merge_csv_tokens(existing: Optional[str], additions: Sequence[str]) -> str:
    items: List[str] = []
    seen: set[str] = set()
    for chunk in re.split(r"[,;/|&]+|\bsi\b", (existing or "").lower()):
        token = chunk.strip()
        if token and token not in seen:
            seen.add(token)
            items.append(token)
    for raw in additions:
        token = raw.strip().lower()
        if token and token not in seen:
            seen.add(token)
            items.append(token)
    return ", ".join(items)


def _segment_matches_rule(normalized_full: str, segments: Sequence[str], rule: ObservationRule) -> bool:
    needles = [normalize_clinical_text(x) for x in rule.get("match_any", [])]
    for needle in needles:
        if not needle:
            continue
        if needle in normalized_full:
            return True
        for seg in segments:
            if needle in normalize_clinical_text(seg):
                return True
    return False


def _apply_dynamic_consumption_rules(normalized_full: str) -> ObservationRule:
    out: ObservationRule = {
        "allergy_tokens": [],
        "condition_codes": [],
        "restriction_phrases": [],
    }
    patterns = (
        r"nu\s+pot\s+(?:consuma|manca|mananc)\s+([^.;!?]+)",
        r"nu\s+consum\s+([^.;!?]+)",
        r"nu\s+pot\s+tolera\s+([^.;!?]+)",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, normalized_full):
            segment = match.group(1)
            segment = re.split(r"\b(?:dar|insa|except|in afara de)\b", segment)[0]
            for part in re.split(r",|\bsi\b|\bsau\b", segment):
                token = normalize_clinical_text(part.strip())
                token = re.sub(r"\b(?:de|din|la|cu|pe)\b", " ", token).strip()
                token = re.sub(r"\s+", " ", token).strip()
                if not token:
                    continue
                mapped = CONSUMABLE_TOKEN_MAP.get(token)
                if mapped:
                    for key in ("allergy_tokens", "condition_codes", "restriction_phrases"):
                        out[key].extend(mapped.get(key, []))  # type: ignore[index]
                elif len(token) > 2:
                    out["restriction_phrases"].append(f"nu mananc {token}")  # type: ignore[index]
    return out


def infer_profile_adjustments_from_text(text: str) -> ObservationRule:
    """Extrage alergii / condiții / fraze canonice de restricție din text clinic liber."""
    if not text or not text.strip():
        return {
            "allergy_tokens": [],
            "condition_codes": [],
            "restriction_phrases": [],
        }

    normalized_full = normalize_clinical_text(text)
    segments = split_clinical_segments(text)
    if not segments:
        segments = [text.strip()]

    allergy_tokens: List[str] = []
    condition_codes: List[str] = []
    restriction_phrases: List[str] = []

    for rule in OBSERVATION_TAG_RULES:
        if _segment_matches_rule(normalized_full, segments, rule):
            allergy_tokens.extend(rule.get("allergy_tokens", []))
            condition_codes.extend(rule.get("condition_codes", []))
            restriction_phrases.extend(rule.get("restriction_phrases", []))

    dynamic = _apply_dynamic_consumption_rules(normalized_full)
    allergy_tokens.extend(dynamic.get("allergy_tokens", []))
    condition_codes.extend(dynamic.get("condition_codes", []))
    restriction_phrases.extend(dynamic.get("restriction_phrases", []))

    return {
        "allergy_tokens": allergy_tokens,
        "condition_codes": condition_codes,
        "restriction_phrases": restriction_phrases,
    }


def build_effective_user_profile(
    user: UserProfile,
    lab_results: Optional[LabResultItem] = None,
) -> UserProfile:
    """
    Îmbină profilul utilizatorului cu observațiile din analize într-un profil efectiv
    folosit la filtrare și generare recomandări.
    """
    notes = (lab_results.notes or "").strip() if lab_results else ""
    conditions = (user.medical_conditions or "").strip()
    full_text = " ".join(x for x in (conditions, notes) if x).strip()

    if not full_text:
        return user

    inferred = infer_profile_adjustments_from_text(full_text)
    merged_allergies = _merge_csv_tokens(user.allergies, inferred.get("allergy_tokens", []))

    condition_parts: List[str] = []
    if conditions:
        condition_parts.append(conditions)
    if notes:
        condition_parts.append(notes)
    for phrase in inferred.get("restriction_phrases", []):
        if phrase and phrase not in condition_parts:
            condition_parts.append(phrase)
    for code in inferred.get("condition_codes", []):
        if code and code not in condition_parts:
            condition_parts.append(code)

    merged_conditions = " ".join(condition_parts).strip()

    if merged_allergies == (user.allergies or "") and merged_conditions == conditions:
        if notes and f"{conditions} {notes}".strip() != conditions:
            return replace(user, medical_conditions=f"{conditions} {notes}".strip())
        return user

    return replace(
        user,
        allergies=merged_allergies or None,
        medical_conditions=merged_conditions or None,
    )
