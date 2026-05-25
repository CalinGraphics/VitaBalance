"""Porții sugerate — sex, categorie, greutate."""
import unittest

from domain.models import FoodItem, UserProfile
from services.portion_calculator import (
    suggest_portion,
    suggest_portion_grams,
    normalized_sex,
    format_portion_label,
)


def _food(category: str) -> FoodItem:
    return FoodItem(
        id=1,
        name="Test",
        category=category,
        iron=1,
        calcium=1,
        vitamin_d=0,
        vitamin_b12=0,
        magnesium=1,
        protein=5,
        zinc=0,
        vitamin_c=1,
        fiber=1,
        calories=100,
    )


class TestPortionCalculator(unittest.TestCase):
    def test_male_larger_than_female_same_profile(self):
        base = {
            "age": 30,
            "weight": 70,
            "height": 170,
            "activity_level": "moderate",
            "diet_type": "omnivore",
        }
        male = UserProfile(id=1, email="m@test.com", name="M", sex="masculin", **base)
        female = UserProfile(id=2, email="f@test.com", name="F", sex="feminin", **base)
        food = _food("carne")
        m_portion = suggest_portion_grams(food, male)
        f_portion = suggest_portion_grams(food, female)
        self.assertGreater(m_portion, f_portion)
        self.assertEqual(normalized_sex(male), "M")
        self.assertEqual(normalized_sex(female), "F")

    def test_heavier_user_gets_larger_portion(self):
        light = UserProfile(
            id=1,
            email="a@test.com",
            name="A",
            sex="F",
            age=25,
            weight=55,
            height=165,
            activity_level="moderate",
            diet_type="omnivore",
        )
        heavy = UserProfile(
            id=2,
            email="b@test.com",
            name="B",
            sex="F",
            age=25,
            weight=90,
            height=175,
            activity_level="moderate",
            diet_type="omnivore",
        )
        food = _food("legume")
        self.assertGreater(suggest_portion_grams(food, heavy), suggest_portion_grams(food, light))

    def test_bauturi_in_ml(self):
        user = UserProfile(
            id=1,
            email="u@test.com",
            name="U",
            sex="F",
            age=30,
            weight=65,
            height=165,
            activity_level="moderate",
            diet_type="omnivore",
        )
        coffee = FoodItem(
            id=2,
            name="Cafea Neagră",
            category="Băuturi",
            iron=0.3,
            calcium=5,
            vitamin_d=0,
            vitamin_b12=0,
            magnesium=8,
            protein=0.3,
            zinc=0.2,
            vitamin_c=0,
            fiber=0,
            calories=5,
        )
        cola = FoodItem(
            id=3,
            name="Suc Cola (1 doză)",
            category="Băuturi",
            iron=0,
            calcium=59,
            vitamin_d=0,
            vitamin_b12=0,
            magnesium=24,
            protein=0,
            zinc=1,
            vitamin_c=0,
            fiber=0,
            calories=140,
        )
        ps_coffee = suggest_portion(coffee, user)
        ps_cola = suggest_portion(cola, user)
        self.assertEqual(ps_coffee.unit, "ml")
        self.assertEqual(ps_cola.unit, "ml")
        self.assertGreaterEqual(ps_cola.amount, 270)
        self.assertLessEqual(ps_cola.amount, 360)
        self.assertIn("ml", format_portion_label(ps_coffee.amount, ps_coffee.unit))

    def test_deserturi_in_grams(self):
        user = UserProfile(
            id=1,
            email="u@test.com",
            name="U",
            sex="M",
            age=25,
            weight=80,
            height=180,
            activity_level="moderate",
            diet_type="omnivore",
        )
        cake = FoodItem(
            id=4,
            name="Cheesecake (1 felie)",
            category="Deserturi",
            iron=1,
            calcium=27,
            vitamin_d=0.6,
            vitamin_b12=0,
            magnesium=33,
            protein=5,
            zinc=0.5,
            vitamin_c=1.9,
            fiber=1,
            calories=320,
        )
        ps = suggest_portion(cake, user)
        self.assertEqual(ps.unit, "g")
        self.assertGreaterEqual(ps.amount, 90)

    def test_nuts_smaller_than_vegetables(self):
        user = UserProfile(
            id=1,
            email="u@test.com",
            name="U",
            sex="M",
            age=30,
            weight=75,
            height=178,
            activity_level="moderate",
            diet_type="omnivore",
        )
        nuts = suggest_portion_grams(_food("nuci & seminte"), user)
        veg = suggest_portion_grams(_food("legume"), user)
        self.assertLess(nuts, veg)


if __name__ == "__main__":
    unittest.main()
