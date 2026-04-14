import sys
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from domain.models import FoodItem, LabResultItem, UserProfile
from services.deficit_calculator import DeficitCalculator
from services.explanation_generator import ExplanationGenerator
from services.recommender import RecommenderService
from services.rule_engine import NutritionalRuleEngine


def make_user(**overrides) -> UserProfile:
    base = {
        "id": 1,
        "email": "test@example.com",
        "name": "Tester",
        "age": 24,
        "sex": "M",
        "weight": 72.0,
        "height": 180.0,
        "activity_level": "moderate",
        "diet_type": "omnivore",
        "allergies": "",
        "medical_conditions": "",
    }
    base.update(overrides)
    return UserProfile(**base)


def make_food(**overrides) -> FoodItem:
    base = {
        "id": 1,
        "name": "Aliment test",
        "category": "legume",
        "iron": 2.0,
        "calcium": 120.0,
        "magnesium": 80.0,
        "vitamin_d": 0.0,
        "vitamin_b12": 0.0,
        "protein": 6.0,
        "zinc": 1.5,
        "vitamin_c": 20.0,
        "folate": 80.0,
        "vitamin_a": 30.0,
        "iodine": 15.0,
        "vitamin_k": 20.0,
        "potassium": 250.0,
    }
    base.update(overrides)
    return FoodItem(**base)


class RecommendationLogicTests(unittest.TestCase):
    def setUp(self) -> None:
        self.deficit_calc = DeficitCalculator()
        self.rule_engine = NutritionalRuleEngine()
        self.recommender = RecommenderService()

    def test_no_lab_values_results_in_no_medical_deficits(self):
        user = make_user()
        labs = LabResultItem(id=1, user_id=1)  # toate valorile None
        deficits = self.deficit_calc.calculate_deficits(user, labs)
        self.assertEqual(deficits, {})

    def test_iron_uses_hemoglobin_when_ferritin_missing(self):
        user = make_user(sex="M")
        labs_normal_hb = LabResultItem(id=1, user_id=1, hemoglobin=14.0, ferritin=None)
        deficits_normal = self.deficit_calc.calculate_deficits(user, labs_normal_hb)
        self.assertEqual(deficits_normal.get("iron", 0), 0)

        labs_low_hb = LabResultItem(id=2, user_id=1, hemoglobin=11.5, ferritin=None)
        deficits_low = self.deficit_calc.calculate_deficits(user, labs_low_hb)
        self.assertGreater(deficits_low.get("iron", 0), 0)

    def test_forbidden_chicken_is_filtered_from_recommendations(self):
        user = make_user(medical_conditions="nu mananc pui")
        chicken = make_food(id=10, name="Pui la rotisor", category="carne")
        fish = make_food(id=11, name="Somon la cuptor", category="pește & fructe de mare")

        self.assertFalse(self.rule_engine._is_compatible(chicken, user))
        self.assertTrue(self.rule_engine._is_compatible(fish, user))

        recs = self.recommender.generate_recommendations(
            user=user,
            deficits={},
            foods=[chicken, fish],
            lab_results=None,
            user_feedbacks=[],
            feedback_by_food={},
        )
        ids = [r["food_id"] for r in recs]
        self.assertNotIn(chicken.id, ids)
        self.assertIn(fish.id, ids)

    def test_medical_conditions_normalization_with_underscores(self):
        user = make_user(medical_conditions="nu_mananc_pui")
        chicken = make_food(id=20, name="Piept de pui", category="carne")
        self.assertFalse(self.rule_engine._is_compatible(chicken, user))

    def test_compound_observation_blocks_all_listed_foods(self):
        user = make_user(medical_conditions="Nu mananc peste, pui")
        chicken = make_food(id=30, name="Pui la cuptor", category="carne")
        fish = make_food(id=31, name="Peste la gratar", category="peste & fructe de mare")
        legumes = make_food(id=32, name="Linte fiarta", category="leguminoase")

        self.assertFalse(self.rule_engine._is_compatible(chicken, user))
        self.assertFalse(self.rule_engine._is_compatible(fish, user))
        self.assertTrue(self.rule_engine._is_compatible(legumes, user))

    def test_long_observation_with_multiple_sentences(self):
        user = make_user(
            medical_conditions=(
                "Am hipertensiune arteriala si reflux gastric. "
                "Nu mananc peste, pui, porc si evit cafea. "
                "De asemenea, medicul mi-a recomandat sa reduc sarea."
            )
        )
        chicken = make_food(id=40, name="Pui la gratar", category="carne")
        fish = make_food(id=41, name="Peste la cuptor", category="peste & fructe de mare")
        pork = make_food(id=42, name="Cotlet de porc", category="carne")
        coffee = make_food(id=43, name="Cafea espresso", category="bauturi")
        lentils = make_food(id=44, name="Linte fiarta", category="leguminoase")

        self.assertFalse(self.rule_engine._is_compatible(chicken, user))
        self.assertFalse(self.rule_engine._is_compatible(fish, user))
        self.assertFalse(self.rule_engine._is_compatible(pork, user))
        self.assertFalse(self.rule_engine._is_compatible(coffee, user))
        self.assertTrue(self.rule_engine._is_compatible(lentils, user))

    def test_reflux_blocks_spicy_chutney(self):
        user = make_user(medical_conditions="am reflux gastroesofagian")
        spicy = make_food(id=50, name="Chutney picant", category="sosuri")
        neutral = make_food(id=51, name="Iaurt simplu", category="lactate")
        self.assertFalse(self.rule_engine._is_compatible(spicy, user))
        self.assertTrue(self.rule_engine._is_compatible(neutral, user))

    def test_high_cholesterol_blocks_fried_and_rich_cheese(self):
        user = make_user(medical_conditions="colesterol_ridicat")
        fries = make_food(id=60, name="Cartofi Prajiți garnitură", category="legume")
        brie = make_food(id=61, name="Brânză Brie", category="lactate")
        cucumber = make_food(id=62, name="Castravete proaspăt", category="legume")
        self.assertFalse(self.rule_engine._is_compatible(fries, user))
        self.assertFalse(self.rule_engine._is_compatible(brie, user))
        self.assertTrue(self.rule_engine._is_compatible(cucumber, user))

    def test_tree_nut_allergy_blocks_ambiguous_nut_dishes(self):
        user = make_user(allergies="nuci", medical_conditions="")
        kibbeh = make_food(id=70, name="Kibbeh prăjit", category="carne")
        pesto = make_food(id=71, name="Pesto verde", category="condimente & mirodenii")
        somon = make_food(id=72, name="Somon la grătar", category="pește & fructe de mare")
        self.assertFalse(self.rule_engine._is_compatible(kibbeh, user))
        self.assertFalse(self.rule_engine._is_compatible(pesto, user))
        self.assertTrue(self.rule_engine._is_compatible(somon, user))

    def test_vegan_blocks_fructe_de_mare_even_if_peste_not_in_category_string(self):
        user = make_user(diet_type="vegan")
        creveti = make_food(
            id=100,
            name="Creveți în sos",
            category="Mese/Fructe de mare",
            iron=1.0,
        )
        self.assertFalse(self.rule_engine._is_compatible(creveti, user))

    def test_soy_allergy_allows_lentils_blocks_tofu(self):
        user = make_user(allergies="soia")
        linte = make_food(id=103, name="Linte roșie fiartă", category="leguminoase", iron=3.0)
        tofu = make_food(id=104, name="Tofu natur", category="proteine vegetale", iron=2.0)
        self.assertTrue(self.rule_engine._is_compatible(linte, user))
        self.assertFalse(self.rule_engine._is_compatible(tofu, user))

    def test_soy_allergy_blocks_processed_conserve_risk(self):
        user = make_user(allergies="soia")
        supa = make_food(id=109, name="Supa de legume la conserva", category="mese/legume")
        self.assertFalse(self.rule_engine._is_compatible(supa, user))

    def test_soy_allergy_processed_item_allowed_when_api_marks_soy_free(self):
        user = make_user(allergies="soia")
        supa = make_food(id=111, name="Supa crema bio", category="mese/procesate")
        with patch("services.compatibility_core.assess_hidden_soy_risk_from_api", return_value=False):
            self.assertTrue(self.rule_engine._is_compatible(supa, user))

    def test_soy_allergy_processed_item_blocked_when_api_reports_soy(self):
        user = make_user(allergies="soia")
        supa = make_food(id=112, name="Supa crema instant", category="mese/procesate")
        with patch("services.compatibility_core.assess_hidden_soy_risk_from_api", return_value=True):
            self.assertFalse(self.rule_engine._is_compatible(supa, user))

    def test_egg_allergy_does_not_false_positive_on_noua(self):
        user = make_user(allergies="oua")
        salata = make_food(id=105, name="Salată verde nouă", category="salate", iron=0.5)
        oua = make_food(id=106, name="Ou fiert", category="oua", iron=1.0)
        self.assertTrue(self.rule_engine._is_compatible(salata, user))
        self.assertFalse(self.rule_engine._is_compatible(oua, user))

    def test_vegan_diet_type_case_insensitive(self):
        user = make_user(diet_type="Vegan")
        homar = make_food(id=101, name="Homar", category="Proteine/Fructe de mare")
        self.assertFalse(self.rule_engine._is_compatible(homar, user))

    def test_organic_vegetables_not_blocked_for_vegan(self):
        user = make_user(diet_type="vegan")
        leg = make_food(id=102, name="Salată verde", category="legume organice")
        self.assertTrue(self.rule_engine._is_compatible(leg, user))

    def test_vegan_blocks_caprese_by_name_even_if_category_is_legume(self):
        user = make_user(diet_type="vegan")
        caprese = make_food(id=107, name="Salata Caprese", category="Mese/Legume")
        self.assertFalse(self.rule_engine._is_compatible(caprese, user))

    def test_fish_allergy_blocks_shellfish_and_seafood_category(self):
        user = make_user(allergies="peste")
        homar = make_food(id=80, name="Homar fiert", category="Proteine/Fructe de mare")
        somon = make_food(id=81, name="Somon", category="pește & fructe de mare")
        pui = make_food(id=82, name="Pui la grătar", category="carne")
        self.assertFalse(self.rule_engine._is_compatible(homar, user))
        self.assertFalse(self.rule_engine._is_compatible(somon, user))
        self.assertTrue(self.rule_engine._is_compatible(pui, user))

    def test_fish_allergy_blocks_shrimp_name_with_diacritics(self):
        """Keyword „crevet” trebuie să se potrivească cu „Creveți” (text normalizat)."""
        user = make_user(allergies="peste")
        creveti = make_food(
            id=83,
            name="Creveți la tigaie",
            category="garnituri",
            iron=1.5,
        )
        self.assertFalse(self.rule_engine._is_compatible(creveti, user))

    def test_english_fish_allergy_alias_maps_to_seafood_rules(self):
        user = make_user(allergies="fish")
        creveti = make_food(id=84, name="Shrimp bowl", category="mese", iron=0.5)
        self.assertFalse(self.rule_engine._is_compatible(creveti, user))

    def test_egg_allergy_blocks_cobb_and_picatta_names(self):
        user = make_user(allergies="oua")
        cobb = make_food(id=90, name="Salată Cobb", category="mese/proteine")
        piccata = make_food(id=91, name="Pui Piccata", category="mese/carne")
        linte = make_food(id=92, name="Linte fiartă", category="leguminoase")
        self.assertFalse(self.rule_engine._is_compatible(cobb, user))
        self.assertFalse(self.rule_engine._is_compatible(piccata, user))
        self.assertTrue(self.rule_engine._is_compatible(linte, user))

    def test_iron_explanation_uses_hemoglobin_when_ferritin_missing(self):
        from services.scoped_rules import ScopedRulesEngine, ScopedRule, NutrientType, ScopeType

        eng = ScopedRulesEngine()
        rule = ScopedRule(
            nutrient=NutrientType.IRON,
            scope=ScopeType.DIET_OMNIVORE,
            weight=1.0,
            recommended_foods=["carne roșie", "ficat"],
            explanation_template="Pentru că ai dietă omnivoră și este indicat aport suplimentar de fier pe baza analizelor disponibile, recomandăm {foods}.",
            clinical_threshold=30.0,
        )
        labs = LabResultItem(id=1, user_id=1, hemoglobin=11.2, ferritin=None)
        user = make_user()
        food = make_food(name="Carne", category="carne", iron=3.0)
        text = eng._generate_explanation(rule, food, 3.0, 5.0, labs, user)
        self.assertIn("hemoglobin", text.lower())
        self.assertIn("feritin", text.lower())
        self.assertNotIn("feritină < 30", text.lower())

    def test_fallback_reason_with_lab_data_does_not_claim_no_deficits(self):
        gen = ExplanationGenerator()
        user = make_user(diet_type="vegan")
        food = make_food(id=108, name="Fasole neagră", category="leguminoase")
        out = gen.generate_explanation(
            food=food,
            user=user,
            deficits={"vitamin_b12": 2.0},
            score=3.2,
            coverage=24.0,
            explanations=["Recomandare de completare."],
            matched_rules=["fallback_profile_based"],
            has_lab_data=True,
        )
        reason_blob = " ".join(out.get("reasons") or []).lower()
        self.assertIn("deficitele identificate", reason_blob)
        self.assertNotIn("nu se evidențiază deficite active", reason_blob)

    def test_vegan_b12_generates_fortified_and_supplement_tip(self):
        gen = ExplanationGenerator()
        user = make_user(diet_type="vegan", medical_conditions="deficienta vitamina b12")
        food = make_food(id=110, name="Fasole", category="leguminoase")
        out = gen.generate_explanation(
            food=food,
            user=user,
            deficits={"vitamin_b12": 2.0},
            score=2.8,
            coverage=20.0,
            explanations=["Este indicat aport de vitamina B12."],
            matched_rules=["generic_vitamin_b12"],
            has_lab_data=True,
        )
        tips = " ".join(out.get("tips") or []).lower()
        self.assertIn("fortificate", tips)
        self.assertIn("supliment", tips)

    def test_fallback_targets_active_deficit_nutrients_when_provided(self):
        user = make_user(diet_type="vegan")
        b12_food = make_food(
            id=120,
            name="Cereale fortificate B12",
            category="cereale",
            vitamin_b12=3.0,
            vitamin_a=0.0,
            vitamin_c=0.0,
        )
        a_food = make_food(
            id=121,
            name="Morcovi cruzi",
            category="legume",
            vitamin_b12=0.0,
            vitamin_a=900.0,
            vitamin_c=0.0,
        )
        recs = self.recommender._generate_fallback_recommendations(
            user=user,
            foods=[a_food, b12_food],
            target_nutrients=["vitamin_b12"],
        )
        self.assertTrue(recs)
        self.assertEqual(recs[0]["food_id"], 120)


if __name__ == "__main__":
    unittest.main()
