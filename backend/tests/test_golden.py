"""
Teste golden: pacienți-tip (tests/golden/*.json) cu „trebuie să apară”, „nu are voie să apară” și primele 3
categorii așteptate, verificate pe catalogul real. O schimbare de scor care strică unul dintre ele nu se
integrează (CI rulează acest fișier); dacă schimbarea e intenționată, actualizează JSON-ul și explică de ce în commit.
"""
import pytest

from domain.models import LabResultItem, UserProfile
from services.nutrition.energy import caloric_goal_warning
from services.recommendations.recommender import RecommenderService
from tests.catalog_fixture import all_foods
from tests.golden.patients import PATIENTS

FOODS = all_foods()
TOP_N = 10


def _patient(p):
    user = UserProfile(**p["user"])
    labs = LabResultItem(id=1, user_id=user.id, **p["labs"]) if p["labs"] is not None else None
    return user, labs


@pytest.fixture(scope="module", params=PATIENTS, ids=[p["id"] for p in PATIENTS])
def case(request):
    p = request.param
    user, labs = _patient(p)
    return p, user, RecommenderService().rank(user, FOODS, labs)


def test_needs(case):
    p, _, ranking = case
    assert {n.nutrient: n.severity for n in ranking.needs} == p["expect"]["needs"]


def test_must_include(case):
    p, _, ranking = case
    top = {s.food.food_key for s in ranking.items[:TOP_N]}
    for group in p["expect"].get("must_include_any", []):
        assert top & set(group), f"niciunul din {group} în top {TOP_N}: {sorted(top)}"


def test_must_not_include_anywhere(case):
    p, _, ranking = case
    listed = {s.food.food_key for s in ranking.items}
    banned = set(p["expect"].get("must_not_include", []))
    assert not (listed & banned), sorted(listed & banned)
    banned_cats = set(p["expect"].get("must_not_include_categories", []))
    assert not ({s.food.category_key for s in ranking.items} & banned_cats)


def test_per_portion_limits(case):
    p, _, ranking = case
    for nutrient, limit in p["expect"].get("max_per_portion", {}).items():
        for s in ranking.items:
            value = (getattr(s.food, nutrient) or 0) * s.food.portion_g / 100
            assert value <= limit, f"{s.food.food_key}: {nutrient} {value:.0f} > {limit}"


def test_top3_categories(case):
    p, _, ranking = case
    allowed = p["expect"].get("top3_categories_subset_of")
    if allowed is None:
        return
    top3 = [s.food.category_key for s in ranking.items[:3]]
    assert set(top3) <= set(allowed), top3


def test_at_least_ten_recommendations(case):
    _, _, ranking = case
    assert len(ranking.items) >= 10


def test_caloric_warning():
    for p in PATIENTS:
        user, _ = _patient(p)
        warning = caloric_goal_warning(user)
        assert (warning or {}).get("code") == p["expect"].get("caloric_warning"), p["id"]
