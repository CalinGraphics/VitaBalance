"""
Validarea valorilor nutriționale la 100 g.

Verificarea energiei (factori Atwater generali):
    kcal ≈ 4·proteine + 4·carbohidrați disponibili + 9·grăsimi + 2·fibre + 7·alcool
unde carbohidrații disponibili = carbohidrați totali (USDA „by difference”, care includ fibrele) − fibre.
Sursa factorilor: FAO, „Food energy – methods of analysis and conversion factors”, FAO Food and Nutrition Paper 77
(2003); 2 kcal/g pentru fibre: Regulamentul (UE) 1169/2011, anexa XIV.

Toleranța de ±15% e cea cerută pentru catalog. USDA folosește uneori factori specifici alimentului (ex. nuci,
unele legume), deci o abatere nu înseamnă automat o valoare greșită — e un semnal de verificat.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

ATWATER_TOLERANCE = 0.15
# Sub acest prag energia e prea mică pentru ca o abatere procentuală să însemne ceva (ex. 15 vs 18 kcal la castravete).
ATWATER_MIN_KCAL_ABS_DIFF = 10.0


def _num(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def atwater_kcal(protein: float, carbs_total: float, fat: float, fiber: float = 0.0, alcohol: float = 0.0) -> float:
    available_carbs = max(0.0, carbs_total - fiber)
    return 4 * protein + 4 * available_carbs + 9 * fat + 2 * fiber + 7 * alcohol


def portion_kcal(kcal_per_100g: Optional[float], grams: float) -> Optional[float]:
    """Caloriile porției: kcal_la_100g × grame / 100 (None dacă nu știm kcal)."""
    if kcal_per_100g is None or grams is None or grams <= 0:
        return None
    return kcal_per_100g * grams / 100.0


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    issues: List[str]
    atwater_kcal: Optional[float]
    deviation: Optional[float]  # (declarat − calculat) / declarat


def validate_per_100g(values: Mapping[str, Any]) -> ValidationResult:
    """`values`: calories, protein, carbs, fat, fiber, alcohol (la 100 g). Lipsurile sunt raportate, nu completate."""
    issues: List[str] = []
    kcal = _num(values.get("calories"))
    protein, carbs, fat = (_num(values.get(k)) for k in ("protein", "carbs", "fat"))
    fiber = _num(values.get("fiber")) or 0.0
    alcohol = _num(values.get("alcohol")) or 0.0

    if kcal is None:
        issues.append("missing_kcal")
    missing_macros = [k for k, v in (("protein", protein), ("carbs", carbs), ("fat", fat)) if v is None]
    if missing_macros:
        issues.append("missing_macros:" + ",".join(missing_macros))
    if None not in (protein, carbs, fat) and protein + carbs + fat + alcohol > 100.5:
        issues.append("macros_over_100g")

    calc = dev = None
    if kcal is not None and not missing_macros:
        calc = atwater_kcal(protein, carbs, fat, fiber, alcohol)
        if kcal > 0:
            dev = (kcal - calc) / kcal
            if abs(dev) > ATWATER_TOLERANCE and abs(kcal - calc) > ATWATER_MIN_KCAL_ABS_DIFF:
                issues.append(f"atwater_out_of_tolerance:{dev:+.0%}")
        elif calc > ATWATER_MIN_KCAL_ABS_DIFF:
            issues.append("atwater_out_of_tolerance:kcal_zero")
    return ValidationResult(ok=not issues, issues=issues, atwater_kcal=calc, deviation=dev)


def validation_report(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Doar rândurile cu probleme, pentru rapoarte (catalog vechi, produse Open Food Facts)."""
    out = []
    for row in rows:
        res = validate_per_100g(row)
        if not res.ok:
            out.append({"id": row.get("id"), "name": row.get("name"), "issues": res.issues,
                        "calories": _num(row.get("calories")),
                        "atwater_kcal": round(res.atwater_kcal, 1) if res.atwater_kcal is not None else None})
    return out
