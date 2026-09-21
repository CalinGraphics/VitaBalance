"""Calorii afișate informativ: doar valori plauzibile per 100 g (preparatele per porție sunt excluse)."""
from domain.models import FoodItem
from services.recommendation_materialize import kcal_per_100g_for_display


def _food(**kw) -> FoodItem:
    base = dict(id=1, name="X", category="Legume")
    base.update(kw)
    return FoodItem(**base)


def test_plausible_per_100g_value_is_returned():
    assert kcal_per_100g_for_display(_food(calories=114, protein=8, fat=0.5, carbs=20)) == 114


def test_meal_with_per_serving_values_is_excluded():
    # Macronutrienți însumați > 100 g la "100 g" => rând per porție (ex. Paste Alfredo)
    assert kcal_per_100g_for_display(_food(calories=680, protein=35, fat=38, carbs=45)) is None


def test_missing_or_zero_calories_is_none():
    assert kcal_per_100g_for_display(_food(calories=0)) is None
    assert kcal_per_100g_for_display(_food()) is None
