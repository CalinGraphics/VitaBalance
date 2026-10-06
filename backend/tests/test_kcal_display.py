"""Caloriile porției: kcal_la_100g × grame / 100, doar pe valori validate."""
import pytest

from domain.models import FoodItem
from services.nutrition.food_validation import portion_kcal
from services.recommendations.materialize import kcal_per_100g_for_display
from tests.catalog_fixture import food


def test_portion_kcal_formula():
    assert portion_kcal(579, 30) == pytest.approx(173.7)
    assert portion_kcal(100, 0) is None
    assert portion_kcal(None, 30) is None


@pytest.mark.parametrize("key, grams, expected", [
    ("almonds", 30, 174),          # 579 kcal/100 g (USDA 170567)
    ("mixed_nuts", 30, 182),       # 607 kcal/100 g — bug-ul vechi dădea 60 kcal
    ("croutons", 15, 70),          # 465 kcal/100 g — bug-ul vechi dădea 76 kcal pentru 152 g
    ("egg_boiled", 50, 78),        # 155 kcal/100 g, un ou = 50 g
    ("wholewheat_bread", 40, 101), # o felie = 40 g
])
def test_catalog_portion_kcal(key, grams, expected):
    f = food(key)
    assert f.portion_g == grams
    assert round(portion_kcal(kcal_per_100g_for_display(f), f.portion_g)) == expected


def test_croutons_at_the_old_buggy_portion_would_be_about_700_kcal():
    assert round(portion_kcal(food("croutons").calories, 152)) == 707


def test_legacy_unvalidated_food_has_no_kcal_estimate():
    legacy = FoodItem(id=1, name="Crutoane cu Usturoi", category="Cereale", calories=50)
    assert kcal_per_100g_for_display(legacy) is None
