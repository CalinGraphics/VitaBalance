"""
Randează explicația unei recomandări (RO/EN) din faptele structurate produse de explanation_facts.build_facts.

Format compatibil cu cardul din frontend: secțiuni separate cu SECTION_SEP, **bold**, liste pentru motive/sfaturi.
Fiecare propoziție are un fapt în spate (valoare din analize, alergie, afecțiune, dietă): nu se generează text liber.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from services.explanation_i18n import (
    ALLERGY_LABELS,
    CONDITION_LABELS,
    DEFAULT_LANG,
    DIET_LABELS,
    MARKER_LABELS,
    NUTRIENT_LABELS,
    NUTRIENT_UNITS,
    SENTENCES,
    TIPS,
    normalize_lang,
)

SECTION_SEP = "\x1e"  # același separator ca în UI (frontend ExplanationSections)
MAX_TIPS = 3


def _num(value: float, lang: str, decimals: int = 1) -> str:
    """12.0 -> '12'; 2.35 -> '2.4' (EN) / '2,4' (RO)."""
    text = f"{float(value):.{decimals}f}".rstrip("0").rstrip(".")
    return text.replace(".", ",") if lang == "ro" else text


def _join(items: List[str], lang: str) -> str:
    items = [i for i in items if i]
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + f" {SENTENCES[lang]['and']} " + items[-1]


def _portion_label(portion: Dict[str, Any]) -> str:
    return f"{int(portion.get('amount') or 0)} {portion.get('unit') or 'g'}"


def _tips_for(facts: Dict[str, Any], lang: str) -> List[str]:
    catalog = TIPS[lang]
    conditions = set((facts.get("profile") or {}).get("conditions") or [])
    diet = (facts.get("profile") or {}).get("diet")
    keys: List[str] = []
    for n in facts.get("nutrients") or []:
        key = n["key"]
        if key == "vitamin_b12" and diet == "vegan":
            keys.append("vitamin_b12_vegan")
        elif key in ("potassium", "protein") and "renal" in conditions:
            keys.append(f"{key}_renal")  # siguranță: fără îndemn generic de a crește aportul
        elif key in catalog:
            keys.append(key)
    tips = [catalog[k] for k in dict.fromkeys(keys)]
    return (tips or [catalog["default"]])[:MAX_TIPS]


def render_explanation(
    facts: Dict[str, Any],
    *,
    food_name: str,
    lang: str = DEFAULT_LANG,
    name_of: Optional[Callable[[int], Optional[str]]] = None,
) -> Dict[str, Any]:
    """
    Returnează {text, portion, portion_unit, reasons, tips, alternatives} în limba cerută.
    `name_of(food_id)` rezolvă numele alimentelor alternative în aceeași limbă (None -> alternativa se omite).
    """
    lang = normalize_lang(lang)
    s = SENTENCES[lang]
    nutrient_names = NUTRIENT_LABELS[lang]
    nutrients: List[Dict[str, Any]] = facts.get("nutrients") or []
    profile = facts.get("profile") or {}
    portion = facts.get("portion") or {}

    by_source: Dict[str, List[Dict[str, Any]]] = {"lab": [], "notes": [], "profile": [], "general": []}
    for n in nutrients:
        by_source.setdefault((n.get("need") or {}).get("source", "general"), []).append(n)

    def names(items: List[Dict[str, Any]]) -> str:
        return _join([nutrient_names[i["key"]] for i in items], lang)

    # --- Secțiunea 1: de ce acest aliment, pentru acest pacient ---
    if by_source["lab"]:
        headline = s["headline_lab"].format(food=food_name, list=names(by_source["lab"]))
        if by_source["notes"]:
            headline += " " + s["also_notes"].format(list=names(by_source["notes"]))
    elif by_source["notes"]:
        headline = s["headline_notes"].format(food=food_name, list=names(by_source["notes"]))
    elif by_source["profile"]:
        headline = s["headline_profile"].format(food=food_name, list=names(by_source["profile"]))
    elif by_source["general"]:
        headline = s["headline_general"].format(food=food_name, list=names(by_source["general"]))
    else:
        headline = s["headline_none"].format(food=food_name)
    sections = [headline]

    # --- Secțiunea 2: ce primește pacientul la porția sugerată ---
    if nutrients:
        parts = [
            s["portion_part"].format(
                nutrient=nutrient_names[n["key"]],
                amount=_num(n["amount"], lang),
                unit=NUTRIENT_UNITS.get(n["key"], ""),
                pct=int(n["pct"]),
            )
            for n in nutrients
        ]
        sections.append(s["portion_line"].format(portion=_portion_label(portion), parts=" · ".join(parts)))

    # --- Motive: fiecare cu faptul din spate ---
    reasons: List[str] = []
    def density(n: Dict[str, Any]) -> Dict[str, str]:
        """Cât conține alimentul la 100 g — răspunde la «de ce tocmai alimentul ăsta»."""
        return {
            "per100": _num(n.get("per100") or 0, lang),
            "nutrient_unit": NUTRIENT_UNITS.get(n["key"], ""),
        }

    for n in by_source["lab"]:
        need = n["need"]
        nutrient_label = nutrient_names[n["key"]]
        marker = MARKER_LABELS[lang].get(need.get("marker")) or (nutrient_label[0].upper() + nutrient_label[1:])
        reasons.append(
            s["reason_lab"].format(
                marker=marker,
                value=_num(need["value"], lang),
                unit=need.get("unit", ""),
                threshold=_num(need["threshold"], lang),
                food=food_name,
                nutrient=nutrient_label,
                **density(n),
            )
        )
    for key in ("notes", "profile", "general"):
        for n in by_source[key]:
            reasons.append(
                s[f"reason_{key}"].format(
                    nutrient=nutrient_names[n["key"]], food=food_name, **density(n)
                )
            )
    if profile.get("diet") in DIET_LABELS[lang]:
        reasons.append(s["reason_diet"].format(diet=DIET_LABELS[lang][profile["diet"]]))
    if profile.get("allergies"):
        reasons.append(
            s["reason_allergies"].format(
                list=_join([ALLERGY_LABELS[lang][a] for a in profile["allergies"] if a in ALLERGY_LABELS[lang]], lang)
            )
        )
    for cid in profile.get("conditions") or []:
        label = CONDITION_LABELS[lang].get(cid)
        if label:
            reasons.append(s["reason_condition"].format(condition=label[0], restriction=label[1]))
    if not facts.get("has_lab_data"):
        reasons.append(s["reason_no_labs"])

    # --- Alternative: alte alimente deja compatibile cu profilul, care acoperă același nutrient ---
    alternatives: List[str] = []
    if name_of is not None:
        for fid in facts.get("alternatives") or []:
            alt = name_of(int(fid))
            if alt:
                alternatives.append(alt)

    return {
        "text": SECTION_SEP.join(sections),
        "portion": portion.get("amount") or 0,
        "portion_unit": portion.get("unit") or "g",
        "reasons": reasons,
        "tips": _tips_for(facts, lang),
        "alternatives": alternatives or None,
    }
