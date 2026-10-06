"""
Estimarea consumului energetic și verificarea obiectivului caloric.

Metabolism bazal (BMR) — ecuația Mifflin-St Jeor (Mifflin et al., Am J Clin Nutr 1990;51:241):
    bărbați: 10·kg + 6,25·cm − 5·ani + 5
    femei:   10·kg + 6,25·cm − 5·ani − 161
Sexul „other”: media celor două constante (−78), alegere de modelare a aplicației.

Consum zilnic total (TDEE) = BMR × factor de activitate. Factorii (1,2 / 1,55 / 1,725 / 1,9) sunt cei folosiți
uzual împreună cu Mifflin-St Jeor (McArdle, Katch & Katch, „Exercise Physiology”). Corespondența cu nivelurile
din profil (sedentary / moderate / active / very_active) e o alegere a aplicației.

Avertismentul NU blochează salvarea: obiectivul e doar informativ.
"""
from __future__ import annotations

from typing import Optional

from domain.models import UserProfile
from services.nutrition.profile_context import normalized_sex

ACTIVITY_FACTORS = {"sedentary": 1.2, "moderate": 1.55, "active": 1.725, "very_active": 1.9}
MAX_DEVIATION_FROM_TDEE = 0.40


def mifflin_st_jeor(sex: str, weight_kg: float, height_cm: float, age: int) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + (5 if sex == "M" else -161 if sex == "F" else -78)


def energy_estimate(user: UserProfile) -> Optional[dict]:
    """{bmr, tdee, activity_factor} rotunjite, sau None dacă lipsesc greutatea/înălțimea/vârsta."""
    if not (user.weight and user.height and user.age):
        return None
    sex = normalized_sex(user.sex)
    bmr = mifflin_st_jeor(sex, float(user.weight), float(user.height), int(user.age))
    factor = ACTIVITY_FACTORS.get((user.activity_level or "moderate").lower(), ACTIVITY_FACTORS["moderate"])
    return {"bmr": round(bmr), "tdee": round(bmr * factor), "activity_factor": factor}


def caloric_goal_warning(user: UserProfile) -> Optional[dict]:
    """
    Date independente de limbă pentru avertisment (textul e în frontend):
    - code "below_bmr": obiectivul e sub metabolismul bazal;
    - code "far_from_tdee": obiectivul diferă cu peste ±40% de consumul zilnic estimat.
    None dacă nu există obiectiv, lipsesc datele sau obiectivul e rezonabil.
    """
    goal = user.caloric_goal
    est = energy_estimate(user)
    if not goal or est is None:
        return None
    deviation = (float(goal) - est["tdee"]) / est["tdee"]
    if goal < est["bmr"]:
        code = "below_bmr"
    elif abs(deviation) > MAX_DEVIATION_FROM_TDEE:
        code = "far_from_tdee"
    else:
        return None
    return {"code": code, "goal": round(float(goal)), "bmr": est["bmr"], "tdee": est["tdee"],
            "deviation_pct": round(deviation * 100)}
