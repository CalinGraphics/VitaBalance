import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from domain.models import UserProfile, LabResultItem
from services.deficit_calculator import DeficitCalculator


def make_user(**overrides) -> UserProfile:
    base = {
        "id": 1,
        "email": "t@example.com",
        "name": "T",
        "age": 30,
        "sex": "M",
        "weight": 70.0,
        "height": 175.0,
        "activity_level": "moderate",
        "diet_type": "omnivore",
        "allergies": "",
        "medical_conditions": "",
    }
    base.update(overrides)
    return UserProfile(**base)


class DeficitCalculatorProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calc = DeficitCalculator()

    def test_iron_rdi_female_higher_than_male_same_age(self):
        m = make_user(sex="m", age=28)
        f = make_user(sex="F", age=28)
        self.assertEqual(self.calc.get_rdi("iron", m), 8)
        self.assertEqual(self.calc.get_rdi("iron", f), 18)

    def test_sex_romanian_and_lowercase_maps_to_rdi_table(self):
        b = make_user(sex="bărbat", age=40)
        fem = make_user(sex="femeie", age=40)
        self.assertEqual(self.calc.get_rdi("zinc", b), 11)
        self.assertEqual(self.calc.get_rdi("zinc", fem), 8)

    def test_vitamin_d_senior_uses_70_plus_bucket(self):
        young = make_user(age=45, sex="F")
        senior = make_user(age=72, sex="F")
        self.assertEqual(self.calc.get_rdi("vitamin_d", young), 600)
        self.assertEqual(self.calc.get_rdi("vitamin_d", senior), 800)

    def test_hemoglobin_sex_specific_low_normal_cutoffs(self):
        # 12,5 g/dL: sub pragul uzual bărbați (13,5), peste pragul femei (12,0)
        labs = LabResultItem(id=1, user_id=1, hemoglobin=12.5, ferritin=None)
        male = make_user(sex="male")
        female = make_user(sex="f")
        dm = self.calc.calculate_deficits(male, labs)
        df = self.calc.calculate_deficits(female, labs)
        self.assertGreater(dm.get("iron", 0), 0)
        self.assertEqual(df.get("iron", 0), 0)

    def test_pregnancy_bumps_iron_and_folate_for_women(self):
        u = make_user(
            sex="F",
            age=28,
            medical_conditions="sarcina trimestrul 2",
        )
        self.assertEqual(self.calc.get_rdi("iron", u), 27.0)
        self.assertEqual(self.calc.get_rdi("folate", u), 600.0)

    def test_activity_level_case_insensitive(self):
        u = make_user(activity_level="Moderate", sex="M", weight=80.0)
        rdi = self.calc.get_rdi("protein", u)
        self.assertAlmostEqual(rdi, 80.0, places=5)

    def test_with_labs_small_non_lab_estimated_deficit_is_suppressed(self):
        user = make_user(sex="M", diet_type="omnivore")
        labs = LabResultItem(
            id=11,
            user_id=1,
            calcium=9.2,
            vitamin_d=34.0,
            vitamin_b12=430.0,
            protein=6.4,
            zinc=96.0,
            magnesium=2.0,
            ferritin=52.0,
        )
        deficits = self.calc.calculate_deficits(user, labs)
        self.assertEqual(deficits.get("vitamin_c", 0), 0)

    def test_with_labs_explicit_vitamin_c_need_keeps_priority(self):
        user = make_user(
            sex="M",
            diet_type="omnivore",
            medical_conditions="deficienta de vitamina C",
        )
        labs = LabResultItem(
            id=12,
            user_id=1,
            calcium=9.2,
            vitamin_d=34.0,
            vitamin_b12=430.0,
            protein=6.4,
            zinc=96.0,
            magnesium=2.0,
            ferritin=52.0,
        )
        deficits = self.calc.calculate_deficits(user, labs)
        self.assertGreater(deficits.get("vitamin_c", 0), 0)


if __name__ == "__main__":
    unittest.main()
