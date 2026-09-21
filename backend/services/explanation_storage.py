"""
Serializare / deserializare explicații recomandări pentru DB și API.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional

from services.explanation_facts import has_facts
from services.explanation_renderer import render_explanation


def explanation_to_db_fields(expl: Dict[str, Any]) -> Dict[str, Any]:
    """Câmpuri pentru insert/update Supabase recommendations."""
    text = str(expl.get("text") or "")
    portion = float(expl.get("portion") or 150)
    portion_unit = str(expl.get("portion_unit") or "g").lower().strip() or "g"
    if portion_unit not in ("g", "ml"):
        portion_unit = "g"
    reasons: List[str] = list(expl.get("reasons") or [])
    tips_raw = expl.get("tips")
    tips: List[str] = list(tips_raw) if tips_raw else []
    alts = expl.get("alternatives")
    payload = {
        "text": text,
        "portion": portion,
        "portion_unit": portion_unit,
        "reasons": reasons,
        "tips": tips if tips else None,
        "alternatives": list(alts) if alts else None,
    }
    if expl.get("facts"):
        # Faptele (limba-neutre) sunt sursa de adevăr; text/reasons/tips de mai sus sunt randarea RO, pentru compatibilitate.
        payload["facts"] = expl["facts"]
    return {
        "explanation": text,
        "portion_suggested": portion,
        "explanation_json": payload,
        "reasons": reasons,
        "tips": tips,
    }


def explanation_from_db_row(
    row: Dict[str, Any],
    *,
    fallback_text: str = "",
    fallback_portion: float = 150.0,
    lang: str = "ro",
    food_name: Optional[str] = None,
    name_of: Optional[Callable[[int], Optional[str]]] = None,
) -> Dict[str, Any]:
    """
    Reconstruiește dict-ul explanation pentru API din rând DB.

    Dacă rândul are fapte (explanation_json.facts) și se cunoaște numele alimentului, explicația se randează în
    `lang`. Rândurile vechi, fără fapte, rămân în textul salvat (RO) până la următoarea regenerare.
    """
    expl_json = row.get("explanation_json")
    if isinstance(expl_json, str):
        try:
            expl_json = json.loads(expl_json)
        except json.JSONDecodeError:
            expl_json = None

    if food_name and has_facts(expl_json):
        return render_explanation(expl_json["facts"], food_name=food_name, lang=lang, name_of=name_of)

    if isinstance(expl_json, dict) and expl_json.get("text"):
        unit = str(expl_json.get("portion_unit") or "g").lower().strip() or "g"
        if unit not in ("g", "ml"):
            unit = "g"
        return {
            "text": str(expl_json.get("text") or ""),
            "portion": float(expl_json.get("portion") or fallback_portion),
            "portion_unit": unit,
            "reasons": list(expl_json.get("reasons") or []),
            "tips": list(expl_json["tips"]) if expl_json.get("tips") else None,
            "alternatives": list(expl_json["alternatives"])
            if expl_json.get("alternatives")
            else None,
        }

    reasons = row.get("reasons")
    if reasons is not None and not isinstance(reasons, list):
        reasons = list(reasons) if reasons else []
    tips = row.get("tips")
    if tips is not None and not isinstance(tips, list):
        tips = list(tips) if tips else []

    text = str(row.get("explanation") or fallback_text or "")
    portion = float(row.get("portion_suggested") or fallback_portion or 150)

    if (reasons and len(reasons) > 0) or (tips and len(tips) > 0):
        return {
            "text": text,
            "portion": portion,
            "portion_unit": "g",
            "reasons": list(reasons or []),
            "tips": list(tips) if tips else None,
            "alternatives": None,
        }

    return {
        "text": text,
        "portion": portion,
        "portion_unit": "g",
        "reasons": [],
        "tips": None,
        "alternatives": None,
    }
