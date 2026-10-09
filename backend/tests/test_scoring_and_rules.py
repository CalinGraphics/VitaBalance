"""Ierarhizarea pe catalogul real: densitate nutritivă, filtre stricte, contraindicații, diversitate, alternative."""
from domain.models import LabResultItem, UserProfile
from rules.contraindications import RULES
from services.nutrition.needs import detect_needs
from services.recommendations.recommender import RecommenderService
from services.recommendations.scoring import MAX_PER_CATEGORY, rank_foods
from tests.catalog_fixture import all_foods, food

FOODS = all_foods()
BY_ID = {f.id: f for f in FOODS}


def _user(**kw):
    base = dict(id=1, email="a@b.c", name="A", age=34, sex="M", weight=79, height=182,
                activity_level="moderate", diet_type="omnivore", allergies="", medical_conditions="")
    base.update(kw)
    return UserProfile(**base)


def _lab(**kw):
    return LabResultItem(id=1, user_id=1, **kw)


def _rank(user, lab=None, foods=FOODS):
    return RecommenderService().rank(user, foods, lab)


def _keys(ranking):
    return [s.food.food_key for s in ranking.items]


def _scores(ranking):
    return {s.food.food_key: s.score for s in ranking.eligible}


# ---------- densitate nutritivă ----------

def test_bagel_never_beats_real_magnesium_sources():
    r = _rank(_user(), _lab(magnesium=1.4))
    scores = _scores(r)
    for good in ("almonds", "pumpkin_seeds", "spinach_raw", "black_beans"):
        assert scores[good] > scores["bagel"], good
    for bad in ("bagel", "croutons", "pancakes", "blueberry_muffin"):
        assert bad not in _keys(r)


def test_processed_foods_are_penalised():
    s = {x.food.food_key: x for x in _rank(_user(), _lab(magnesium=1.4)).eligible}
    assert ("ultra_processed", 0.5) in s["bagel"].penalties and ("refined_grain", 0.7) in s["bagel"].penalties
    assert ("high_sodium", 0.7) in s["croutons"].penalties
    assert s["almonds"].penalties == []


def test_multi_deficit_bonus():
    r = _rank(_user(), _lab(vitamin_d=18, magnesium=1.6))
    salmon = next(s for s in r.eligible if s.food.food_key == "salmon_farmed")
    assert {c.nutrient for c in salmon.components} == {"vitamin_d", "magnesium"}
    assert salmon.bonus == 1.25


def test_unknown_value_is_excluded_from_that_nutrient_score():
    r = _rank(_user(), _lab(vitamin_d=18))
    wild = next(s for s in r.eligible if s.food.food_key == "salmon_wild")  # vitamina D lipsă în USDA
    assert all(c.nutrient != "vitamin_d" for c in wild.components)


def test_list_is_score_descending_and_trace_is_complete():
    r = _rank(_user(), _lab(vitamin_d=18, magnesium=1.6))
    scores = [s.score for s in r.items]
    assert scores == sorted(scores, reverse=True)
    trace = r.items[0].trace(r.rule_ids)
    assert trace["components"][0]["density"] > 0 and "daily_reference" in trace["components"][0]
    assert trace["score"] == round(r.items[0].score, 4)


# ---------- diversitate și alternative ----------

def test_at_most_three_per_category():
    for lab in (_lab(magnesium=1.4), _lab(ferritin=8), _lab(vitamin_d=15)):
        cats = [s.food.category_key for s in _rank(_user(), lab).items]
        assert all(cats.count(c) <= MAX_PER_CATEGORY for c in set(cats))


def test_alternatives_same_category_same_nutrient_same_filters():
    r = _rank(_user(diet_type="vegan", allergies="nuci"), _lab(magnesium=1.4))
    allowed = {s.food.id for s in r.eligible}
    for item in r.items:
        for alt_id in item.alternatives:
            alt = BY_ID[alt_id]
            assert alt.category_key == item.food.category_key
            assert alt_id in allowed and alt.animal_source is None and "nuci" not in alt.allergen_codes
            alt_scored = next(s for s in r.eligible if s.food.id == alt_id)
            assert item.primary.nutrient in {c.nutrient for c in alt_scored.components}
    nuts = next((i for i in r.items if i.food.category_key == "seeds"), None)
    assert nuts is not None and all(BY_ID[a].category_key == "seeds" for a in nuts.alternatives)


# ---------- filtre stricte ----------

def test_diet_filters():
    vegan = _rank(_user(diet_type="vegan"), _lab(vitamin_b12=150))
    assert all(s.food.animal_source is None for s in vegan.eligible)
    assert vegan.items[0].food.food_key == "soy_milk_fortified"
    pesc = _rank(_user(diet_type="pescatarian"), _lab(ferritin=8))
    assert all(s.food.animal_source not in ("meat", "poultry") for s in pesc.eligible)


def test_allergies_filter():
    r = _rank(_user(allergies="nuci, sesam, peste"), _lab(magnesium=1.4))
    for s in r.eligible:
        assert not ({"nuci", "sesam", "peste"} & set(s.food.allergen_codes)), s.food.food_key


def test_free_text_restriction():
    r = _rank(_user(medical_conditions="nu mănânc pește și nu am voie lactate"), _lab(vitamin_d=15))
    assert all(s.food.animal_source not in ("fish", "shellfish", "dairy") for s in r.eligible)


# ---------- contraindicații ----------

def test_every_rule_has_a_source():
    assert all(r.source for r in RULES) and len({r.id for r in RULES}) == len(RULES)


def test_pregnancy_excludes_raw_fish_mercury_liver_and_soft_cheese():
    r = _rank(_user(sex="F", age=31, diet_type="pescatarian", medical_conditions="sarcina"), _lab(vitamin_d=15))
    allowed = {s.food.food_key for s in r.eligible}
    for banned in ("salmon_sashimi", "oysters_raw", "swordfish", "king_mackerel", "tilefish", "brie", "camembert"):
        assert banned not in allowed, banned
    assert "salmon_farmed" in allowed  # somonul gătit rămâne
    r2 = _rank(_user(sex="F", age=31, medical_conditions="Sunt însărcinată"), _lab(ferritin=8))
    assert not {"beef_liver", "chicken_liver"} & {s.food.food_key for s in r2.eligible}


def test_pregnancy_detection_from_text_ignored_for_men():
    assert "pregnancy_no_liver" not in _rank(_user(medical_conditions="sarcina"), _lab(ferritin=8)).rule_ids


def test_immunocompromised_excludes_raw_animal_foods():
    r = _rank(_user(medical_conditions="imunitate_scazuta"), _lab(vitamin_b12=120))
    assert not {"salmon_sashimi", "oysters_raw"} & {s.food.food_key for s in r.eligible}


def test_warfarin_no_large_vitamin_k_and_never_targeted():
    r = _rank(_user(age=60, medical_conditions="anticoagulante"), _lab(magnesium=1.4))
    for s in r.eligible:
        k = (s.food.vitamin_k or 0) * s.food.portion_g / 100
        assert k <= 60, s.food.food_key
    assert "spinach_raw" not in {s.food.food_key for s in r.eligible}
    r2 = _rank(_user(medical_conditions="warfarină; deficit de vitamina K"), None)
    assert all(n.nutrient != "vitamin_k" for n in r2.targeted)


def test_ckd_and_high_potassium_exclude_potassium_rich_foods():
    r = _rank(_user(age=55, medical_conditions="insuficienta_renala"), _lab(potassium=5.8, magnesium=1.4))
    for s in r.eligible:
        assert (s.food.potassium or 0) * s.food.portion_g / 100 <= 200, s.food.food_key
    r2 = _rank(_user(), _lab(potassium=5.8))  # potasiu mare, fără diagnostic: tot limităm
    assert "ckd_limit_potassium" in r2.rule_ids


def test_hemochromatosis_never_targets_iron():
    r = _rank(_user(medical_conditions="hemocromatoza"), _lab(ferritin=5, vitamin_d=15))
    assert all(n.nutrient != "iron" for n in r.targeted)
    assert not {"beef_liver", "chicken_liver", "oysters_raw"} & {s.food.food_key for s in r.eligible}


def test_hypertension_excludes_high_sodium():
    r = _rank(_user(medical_conditions="hipertensiune"), _lab(vitamin_d=15))
    assert all((s.food.sodium or 0) <= 600 for s in r.eligible)


def test_diabetes_penalises_high_glycemic_load():
    r = _rank(_user(medical_conditions="diabet"), _lab(magnesium=1.4))
    pasta = next(s for s in r.eligible if s.food.food_key == "wholewheat_pasta")
    assert ("diabetes_low_glycemic_load", 0.6) in pasta.penalties


def test_feedback_dislike_lowers_score():
    base = rank_foods(FOODS, detect_needs(_user(), _lab(magnesium=1.4)))
    top = base.items[0].food
    disliked = rank_foods(FOODS, detect_needs(_user(), _lab(magnesium=1.4)), feedback={top.id: "dislike"})
    assert next(s.score for s in disliked.eligible if s.food.id == top.id) < base.items[0].score


def test_unvalidated_legacy_foods_are_never_recommended():
    from domain.models import FoodItem
    legacy = FoodItem(id=1, name="Bagel Simplu", category="Cereale", magnesium=57, calories=270)
    r = _rank(_user(), _lab(magnesium=1.4), foods=FOODS + [legacy])
    assert 1 not in {s.food.id for s in r.eligible}


# ---------- biodisponibilitate și variante ----------

def test_heme_iron_sources_beat_spinach_for_iron_deficiency():
    r = _rank(_user(sex="F", age=30, weight=60, height=165), _lab(ferritin=8))
    keys = _keys(r)
    assert keys.index("chicken_liver") < keys.index("spinach_cooked")
    assert keys.index("mussels") < keys.index("spinach_cooked")
    bio = {s.food.food_key: s.primary.bioavailability for s in r.eligible if s.primary}
    assert bio["beef_lean"] == 1.0 and bio["lentils"] == 0.5 and bio["spinach_cooked"] == 0.25


def test_one_form_of_the_same_food_per_list():
    from services.recommendations.scoring import base_food

    for user, lab in ((_user(), None), (_user(), _lab(magnesium=1.4)), (_user(), _lab(vitamin_d=12))):
        bases = [base_food(s.food) for s in _rank(user, lab).items]
        assert len(bases) == len(set(bases)), bases


def test_replacement_respects_category_caps_and_variants_of_kept_foods():
    user, lab = _user(), _lab(magnesium=1.4)
    full = _rank(user, lab).items
    kept = [s.food for s in full if s.food.category_key == "leafy_greens"][:MAX_PER_CATEGORY]
    assert len(kept) == MAX_PER_CATEGORY
    r = RecommenderService().rank(user, FOODS, lab, exclude_food_ids={f.id for f in kept}, taken=kept)
    assert all(s.food.category_key != "leafy_greens" for s in r.items)
    assert "spinach_raw" not in _keys(r) and "spinach_cooked" not in _keys(r)
