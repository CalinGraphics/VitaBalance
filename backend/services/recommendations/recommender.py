"""
Punctul de intrare al motorului de recomandări.

Pașii (fiecare în modulul lui, ca să poată fi citit și testat separat):
1. nevoi: services/nutrition/needs.py (analize sub interval + afirmații explicite, cu sursa salvată);
2. filtre stricte înainte de scor: dietă, alergii, restricții scrise (services/rules/text_restrictions.py) și
   contraindicații (rules/contraindications.py);
3. scor și ierarhizare: services/recommendations/scoring.py (densitate la 100 kcal, diversitate, alternative).
Doar alimentele din catalogul validat (FoodItem.validated) pot fi recomandate.
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from domain.models import FeedbackItem, FoodItem, LabResultItem, UserProfile
from services.nutrition.needs import NeedsResult, detect_needs
from services.recommendations.scoring import Ranking, rank_foods
from services.rules.text_restrictions import text_restriction_filter


def feedback_map(user_feedbacks: Optional[Iterable[FeedbackItem]]) -> Dict[int, str]:
    """Votul utilizatorului pe aliment: rating ≥ 4 = like, ≤ 2 = dislike (ca în RecommendationCard)."""
    out: Dict[int, str] = {}
    for fb in user_feedbacks or []:
        if fb.rating is None:
            continue
        if fb.rating >= 4:
            out[fb.food_id] = "like"
        elif fb.rating <= 2:
            out[fb.food_id] = "dislike"
    return out


class RecommenderService:
    def rank(
        self,
        user: UserProfile,
        foods: List[FoodItem],
        lab_results: Optional[LabResultItem] = None,
        user_feedbacks: Optional[List[FeedbackItem]] = None,
        exclude_food_ids: Iterable[int] = (),
        needs: Optional[NeedsResult] = None,
    ) -> Ranking:
        excluded = set(exclude_food_ids)
        pool = [f for f in foods if f.id not in excluded] if excluded else foods
        return rank_foods(
            pool,
            needs or detect_needs(user, lab_results),
            text_allows=text_restriction_filter(user, lab_results),
            feedback=feedback_map(user_feedbacks),
        )
