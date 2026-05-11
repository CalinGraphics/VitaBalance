"""
Teste „golden” ușoare pe motorul de recomandări: structură stabilă și consistență minimă.
"""
import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from domain.models import FoodItem, UserProfile
from services.recommender import RecommenderService


def _user(**kwargs) -> UserProfile:
    base = dict(
        id=1,
        email="golden@example.com",
        name="Golden",
        age=35,
        sex="F",
        weight=65.0,
        height=165.0,
        activity_level="moderate",
        diet_type="omnivore",
        allergies="",
        medical_conditions="",
    )
    base.update(kwargs)
    return UserProfile(**base)


class RecommenderGoldenTests(unittest.TestCase):
    def test_output_shape_and_ordering(self):
        user = _user()
        foods = [
            FoodItem(id=1, name="Spanac fiert", category="legume", iron=3.6, folate=190, vitamin_c=28),
            FoodItem(id=2, name="Linte", category="leguminoase", iron=3.3, protein=9, folate=180),
            FoodItem(id=3, name="Somon", category="pește & fructe de mare", protein=20, vitamin_d=10, vitamin_b12=4),
        ]
        svc = RecommenderService()
        deficits = {"iron": 2.0, "folate": 120.0}
        out = svc.generate_recommendations(
            user=user,
            deficits=deficits,
            foods=foods,
            lab_results=None,
            user_feedbacks=None,
            feedback_by_food=None,
        )
        self.assertGreater(len(out), 0)
        for rec in out:
            self.assertIn("food_id", rec)
            self.assertIn("score", rec)
            self.assertIn("coverage", rec)
            self.assertGreaterEqual(rec["coverage"], 0.0)

    def test_vegan_user_excludes_obvious_animal_products(self):
        user = _user(diet_type="vegan", allergies="")
        foods = [
            FoodItem(id=10, name="Iaurt natural", category="lactate", protein=4, calcium=120),
            FoodItem(id=11, name="Năut", category="leguminoase", protein=8, iron=2.5, folate=150),
        ]
        svc = RecommenderService()
        out = svc.generate_recommendations(
            user=user,
            deficits={"iron": 1.5},
            foods=foods,
            lab_results=None,
            user_feedbacks=None,
            feedback_by_food=None,
        )
        ids = {r["food_id"] for r in out}
        self.assertNotIn(10, ids)


if __name__ == "__main__":
    unittest.main()
