"""
Punctul de intrare al motorului de recomandări.

Pașii (fiecare în modulul lui, ca să poată fi citit și testat separat):
1. nevoi: services/nutrition/needs.py (analize sub interval + afirmații explicite, cu sursa salvată);
2. filtre stricte înainte de scor: dietă, alergii, restricții scrise (services/rules/text_restrictions.py) și
   contraindicații (rules/contraindications.py);
3. scor și ierarhizare: services/recommendations/scoring.py (densitate la 100 kcal, vectorizat, diversitate,
   alternative).
Doar alimentele din catalogul validat (FoodItem.validated) pot fi recomandate. Clasamentele recente stau în cache
(services/recommendations/cache.py), cu cheia = hash(profil + analize + catalog + voturi).
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from domain.models import FeedbackItem, FoodItem, LabResultItem, UserProfile
from services.explanations.facts import FACTS_VERSION
from services.nutrition.needs import NeedsResult, detect_needs
from services.recommendations.cache import RANKING_CACHE, catalog_signature, inputs_hash
from services.recommendations.scoring import SCORING_VERSION, Ranking, rank_foods
from services.rules.text_restrictions import text_restriction_filter

VERSIONS = f"scoring{SCORING_VERSION}-facts{FACTS_VERSION}"


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


def recommendation_inputs_hash(user: UserProfile, foods: List[FoodItem], lab_results: Optional[LabResultItem]) -> str:
    return inputs_hash(user, lab_results, catalog_signature(foods), VERSIONS)


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
        exclude = set(exclude_food_ids)
        feedback = feedback_map(user_feedbacks)
        inputs = recommendation_inputs_hash(user, foods, lab_results)
        key = RANKING_CACHE.key(inputs, feedback, exclude)
        cached = None if needs is not None else RANKING_CACHE.get(key)
        if cached is not None:
            return cached
        ranking = rank_foods(
            foods,
            needs or detect_needs(user, lab_results),
            text_allows=text_restriction_filter(user, lab_results),
            feedback=feedback,
            exclude_food_ids=exclude,
        )
        ranking.inputs_hash = inputs
        if needs is None:
            RANKING_CACHE.put(key, ranking)
        return ranking
