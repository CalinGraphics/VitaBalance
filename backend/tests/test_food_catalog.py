"""Catalogul validat: surse, porții realiste, valori lipsă păstrate ca null, verificarea energiei."""
import json

import pytest

from data.food_catalog_spec import CATEGORIES, FOODS
from services.nutrition.food_validation import atwater_kcal, validate_per_100g
from tests.catalog_fixture import CATALOG_PATH, catalog_entries, food


def test_catalog_json_matches_spec():
    entries = catalog_entries()
    assert [e["key"] for e in entries] == [s.key for s in FOODS]
    assert len({e["key"] for e in entries}) == len(entries)
    assert all(e["category"] in CATEGORIES for e in entries)
    assert all(e["fdc_id"] > 0 and e["usda_description"] for e in entries)


def test_every_food_passes_energy_check():
    bad = [e["key"] for e in catalog_entries() if not e["validation"]["ok"]]
    assert bad == []


def test_atwater_formula_and_tolerance():
    # migdale USDA: 21,15 g proteine, 49,93 g grăsimi, 21,55 g carbohidrați (din care 12,5 g fibre) -> ~595 kcal
    assert atwater_kcal(21.15, 21.55, 49.93, 12.5) == pytest.approx(595.0, abs=1)
    assert validate_per_100g({"calories": 579, "protein": 21.15, "carbs": 21.55, "fat": 49.93, "fiber": 12.5}).ok
    wrong = validate_per_100g({"calories": 200, "protein": 21.15, "carbs": 21.55, "fat": 49.93, "fiber": 12.5})
    assert not wrong.ok and wrong.issues[0].startswith("atwater_out_of_tolerance")
    assert "macros_over_100g" in validate_per_100g({"calories": 600, "protein": 40, "carbs": 40, "fat": 30}).issues
    assert "missing_kcal" in validate_per_100g({"protein": 1, "carbs": 1, "fat": 1}).issues


def test_missing_values_stay_null_never_zero():
    raw = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    assert all(e["per100g"]["iodine"] is None for e in raw)  # SR Legacy nu are iod
    assert food("salmon_wild").vitamin_d is None             # lipsă în USDA -> null, nu 0
    # Fortificarea obligatorie din SUA nu se aplică în România: fier/folat omise
    assert food("bagel").iron is None and food("bagel").folate is None


@pytest.mark.parametrize("key, grams", [
    ("almonds", 30), ("pumpkin_seeds", 30), ("salmon_farmed", 130), ("black_beans", 150),
    ("spinach_raw", 80), ("wholewheat_bread", 40), ("egg_boiled", 50),
])
def test_realistic_portions(key, grams):
    assert food(key).portion_g == grams


def test_no_global_default_portion():
    assert all(s.portion_g > 0 for s in FOODS)
    portions_by_category = {}
    for s in FOODS:
        portions_by_category.setdefault(s.category, set()).add(s.portion_g)
    # Porția vine din aliment, nu din categorie (ex. tofu 100 g, leguminoase 150 g, hummus 60 g)
    assert len(portions_by_category["legumes"]) > 1


def test_safety_flags_are_set():
    assert "raw_animal" in food("salmon_sashimi").flags and "raw_animal" in food("oysters_raw").flags
    assert "high_mercury" in food("swordfish").flags
    assert "liver" in food("beef_liver").flags
    assert "soft_mould_cheese" in food("brie").flags
    assert {"ultra_processed", "refined_grain"} <= set(food("bagel").flags)
