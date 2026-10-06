"""Cache pe recomandări: cheia = hash(profil + analize + catalog), invalidat la orice schimbare relevantă."""
from dataclasses import replace

from domain.models import LabResultItem, RecommendationItem, UserProfile
from services.explanations.storage import explanation_to_db_fields
from services.explanations.facts import build_facts
from services.recommendations.cache import RANKING_CACHE
from services.recommendations.materialize import _needs_regeneration
from services.recommendations.recommender import RecommenderService, recommendation_inputs_hash
from tests.catalog_fixture import all_foods

FOODS = all_foods()
USER = UserProfile(id=1, email="c@c.ro", name="C", age=34, sex="M", weight=79, height=182,
                   activity_level="moderate", diet_type="omnivore", allergies="", medical_conditions="",
                   updated_at="2026-01-01T00:00:00+00:00")
LABS = LabResultItem(id=1, user_id=1, vitamin_d=18, created_at="2026-01-01T00:00:00+00:00")


def _stored(user=USER, labs=LABS):
    ranking = RecommenderService().rank(user, FOODS, labs)
    out = []
    for i, item in enumerate(ranking.items, 1):
        fields = explanation_to_db_fields(build_facts(item, ranking, has_lab_data=True))
        out.append(RecommendationItem(id=i, user_id=1, food_id=item.food.id, score=item.score, explanation="",
                                      portion_suggested=fields["portion_suggested"],
                                      explanation_json=fields["explanation_json"],
                                      created_at="2026-02-01T00:00:00+00:00"))
    return out


def test_hash_changes_with_profile_and_labs_but_not_with_name_or_timestamps():
    base = recommendation_inputs_hash(USER, FOODS, LABS)
    assert recommendation_inputs_hash(replace(USER, name="Alt nume", updated_at="2027-01-01"), FOODS, LABS) == base
    assert recommendation_inputs_hash(replace(USER, weight=80), FOODS, LABS) != base
    assert recommendation_inputs_hash(replace(USER, medical_conditions="sarcina"), FOODS, LABS) != base
    assert recommendation_inputs_hash(USER, FOODS, replace(LABS, vitamin_d=25)) != base
    assert recommendation_inputs_hash(USER, FOODS, None) != base


def test_no_regeneration_when_only_timestamps_moved():
    stored = _stored()
    newer_user = replace(USER, updated_at="2026-06-01T00:00:00+00:00")  # ex. schimbarea pozei sau a numelui
    current = recommendation_inputs_hash(newer_user, FOODS, LABS)
    assert not _needs_regeneration(stored, newer_user, LABS, current)


def test_regeneration_when_profile_or_labs_change():
    stored = _stored()
    changed = replace(USER, diet_type="vegan")
    assert _needs_regeneration(stored, changed, LABS, recommendation_inputs_hash(changed, FOODS, LABS))
    new_labs = replace(LABS, magnesium=1.4)
    assert _needs_regeneration(stored, USER, new_labs, recommendation_inputs_hash(USER, FOODS, new_labs))


def test_ranking_cache_hit_returns_same_result():
    RANKING_CACHE.clear()
    first = RecommenderService().rank(USER, FOODS, LABS)
    hits = RANKING_CACHE.hits
    second = RecommenderService().rank(USER, FOODS, LABS)
    assert second is first and RANKING_CACHE.hits == hits + 1
    other = RecommenderService().rank(replace(USER, diet_type="vegan"), FOODS, LABS)
    assert other is not first
