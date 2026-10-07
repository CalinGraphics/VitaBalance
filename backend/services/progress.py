"""
Progresul utilizatorului: evoluția analizelor în timp, jurnalul de stare (simptome, energie, greutate) și ce
înseamnă ele pentru recomandări (rules/symptoms.py). Date independente de limbă: textul se construiește în frontend.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from data.lab_ranges import LAB_RANGES
from domain.models import CheckIn, LabResultItem, UserProfile
from rules.symptoms import RECENT_DAYS, SYMPTOM_CODES, analyse
from services.nutrition.profile_context import build_profile_context


def _lab_date(lab: LabResultItem) -> Optional[str]:
    v = getattr(lab, "updated_at", None) or getattr(lab, "created_at", None)
    return str(v)[:10] if v else None


def lab_series(user: UserProfile, history: List[LabResultItem]) -> Dict[str, dict]:
    """Pentru fiecare marker cu cel puțin o valoare: punctele (dată, valoare), limita minimă și unitatea."""
    ctx = build_profile_context(user, history[0] if history else None)
    out: Dict[str, dict] = {}
    for marker, rng in LAB_RANGES.items():
        points = []
        for lab in history:
            value = getattr(lab, marker, None)
            day = _lab_date(lab)
            if value is not None and day:
                points.append({"date": day, "value": float(value)})
        if points:
            points.sort(key=lambda p: p["date"])
            out[marker] = {"unit": rng.unit, "low": rng.low(ctx.sex, ctx.pregnant), "high": rng.high, "points": points}
    return out


def checkin_payload(c: CheckIn) -> dict:
    return {"id": c.id, "checked_on": c.checked_on, "symptoms": list(c.symptoms), "severity": c.severity,
            "energy": c.energy, "weight": c.weight, "notes": c.notes}


def build_progress(user: UserProfile, checkins: List[CheckIn], history: List[LabResultItem],
                   storage_available: bool = True) -> dict:
    # Un marker e „cunoscut” dacă apare în oricare set de analize (nu doar în ultimul): nu-l mai sugerăm.
    lab_values = {m: next((getattr(lab, m) for lab in history if getattr(lab, m, None) is not None), None)
                  for m in LAB_RANGES}
    insights = analyse(checkins, lab_values)
    ordered = sorted(checkins, key=lambda c: c.checked_on)
    return {
        "storage_available": storage_available,
        "symptom_codes": list(SYMPTOM_CODES),
        "recent_days": RECENT_DAYS,
        "checkins": [checkin_payload(c) for c in sorted(checkins, key=lambda c: c.checked_on, reverse=True)],
        "insights": {
            "recent_symptoms": sorted(insights.recent),
            "lab_suggestions": list(insights.lab_suggestions),
            "see_doctor": insights.see_doctor,
            "see_doctor_reasons": list(insights.see_doctor_reasons),
            "adjustments": list(insights.adjustments),
        },
        "series": {
            "labs": lab_series(user, history),
            "weight": [{"date": c.checked_on, "value": c.weight} for c in ordered if c.weight is not None],
            "energy": [{"date": c.checked_on, "value": c.energy} for c in ordered if c.energy is not None],
        },
    }
