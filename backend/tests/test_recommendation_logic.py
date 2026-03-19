import sys
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from domain.models import FoodItem, LabResultItem, UserProfile
from services.deficit_calculator import DeficitCalculator
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


if __name__ == "__main__":
    unittest.main()
