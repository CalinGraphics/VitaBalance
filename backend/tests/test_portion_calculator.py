"""Porții sugerate — sex, categorie, greutate."""
import unittest

from domain.models import FoodItem, UserProfile
from services.portion_calculator import suggest_portion_grams, normalized_sex


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
