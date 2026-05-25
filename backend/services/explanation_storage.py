"""
Serializare / deserializare explicații recomandări pentru DB și API.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


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
) -> Dict[str, Any]:
    """Reconstruiește dict-ul explanation pentru API din rând DB."""
    expl_json = row.get("explanation_json")
    if isinstance(expl_json, str):
        try:
            expl_json = json.loads(expl_json)
        except json.JSONDecodeError:
            expl_json = None

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


def explanation_from_recommendation_item(rec: Any) -> Dict[str, Any]:
    """Din RecommendationItem + câmpuri opționale atașate pe obiect."""
    row = {
        "explanation": getattr(rec, "explanation", "") or "",
        "portion_suggested": getattr(rec, "portion_suggested", 150),
        "explanation_json": getattr(rec, "explanation_json", None),
        "reasons": getattr(rec, "reasons", None),
        "tips": getattr(rec, "tips", None),
    }
    return explanation_from_db_row(
        row,
        fallback_text=row["explanation"],
        fallback_portion=float(row["portion_suggested"] or 150),
    )
