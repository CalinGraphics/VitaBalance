import sys
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from fastapi.testclient import TestClient
    HAS_FASTAPI = True
except ModuleNotFoundError:
    HAS_FASTAPI = False


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

if HAS_FASTAPI:
    import main as main_module
from domain.models import FoodItem, LabResultItem, RecommendationItem, UserProfile


def make_user_profile(**overrides) -> UserProfile:
    data = {
        "id": 1,
        "email": "tester@example.com",
        "name": "Tester",
        "age": 24,
        "sex": "M",
        "weight": 72.0,
        "height": 182.0,
        "activity_level": "moderate",
        "diet_type": "omnivore",
        "allergies": "",
        "medical_conditions": "",
    }
    data.update(overrides)
    return UserProfile(**data)


@unittest.skipUnless(HAS_FASTAPI, "fastapi nu este instalat în environment-ul curent")
class RecommendationsEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(main_module.app)
        main_module.app.dependency_overrides[main_module.get_current_user] = (
            lambda: {"email": "tester@example.com"}
        )

    def tearDown(self) -> None:
        main_module.app.dependency_overrides = {}

    def _make_repo_patches(self, user: UserProfile, foods, lab_result):
        class FakeUserRepo:
            def get_by_email(self, email):
                return user if email.lower() == user.email.lower() else None

            def get_by_id(self, user_id):
                return user if user_id == user.id else None

        class FakeFoodRepo:
            def get_all(self):
                return foods

        class FakeLabRepo:
            def get_latest_by_user_id(self, user_id):
                return lab_result if user_id == user.id else None

        class FakeFeedbackRepo:
            def get_by_user_id(self, user_id):
                return []

            def get_counts_by_food_id(self):
                return {}

        class FakeRecRepo:
            def __init__(self):
                self._rows = []
                self._seq = 1

            def get_first_by_user_id(self, user_id):
                return None

            def get_by_user_id(self, user_id, limit=10):
                return self._rows[:limit]

            def insert_many(self, rows):
                out = []
                for r in rows:
                    rec = RecommendationItem(
                        id=self._seq,
                        user_id=r["user_id"],
                        food_id=r["food_id"],
                        score=float(r["score"]),
                        explanation=r.get("explanation") or "",
                        portion_suggested=float(r.get("portion_suggested") or 150),
                        coverage_percentage=float(r.get("coverage_percentage") or 0),
                    )
                    self._seq += 1
                    self._rows.append(rec)
                    out.append(rec)
                return out

            def delete_by_user_id(self, user_id):
                self._rows = [x for x in self._rows if x.user_id != user_id]

            def delete_by_id(self, recommendation_id):
                self._rows = [x for x in self._rows if x.id != recommendation_id]

        return [
            patch.object(main_module, "UserRepository", FakeUserRepo),
            patch.object(main_module, "FoodRepository", FakeFoodRepo),
            patch.object(main_module, "LabResultRepository", FakeLabRepo),
            patch.object(main_module, "FeedbackRepository", FakeFeedbackRepo),
            patch.object(main_module, "RecommendationRepository", FakeRecRepo),
        ]

    def test_excludes_chicken_when_medical_condition_says_no_chicken(self):
        user = make_user_profile(medical_conditions="nu mananc pui")
        foods = [
            FoodItem(id=10, name="Pui la rotisor", category="carne", protein=30, iron=1.2),
            FoodItem(id=11, name="Somon la cuptor", category="pește & fructe de mare", protein=25, vitamin_d=8),
            FoodItem(id=12, name="Linte fiartă", category="leguminoase", protein=9, iron=3.3, folate=180),
        ]
        labs = LabResultItem(id=1, user_id=1)  # fără biomarkeri completați

        ctx = self._make_repo_patches(user, foods, labs)
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            resp = self.client.post("/api/recommendations", json={"user_id": 1})

        self.assertEqual(resp.status_code, 200, resp.text)
        payload = resp.json()
        names = [r["food"]["name"].lower() for r in payload]
        self.assertFalse(any("pui" in n for n in names), payload)

    def test_no_lab_data_uses_profile_wording_not_medical_analyses(self):
        user = make_user_profile()
        foods = [
            FoodItem(id=21, name="Năut fiert", category="leguminoase", protein=8.5, folate=170, iron=2.7),
            FoodItem(id=22, name="Macrou", category="pește & fructe de mare", vitamin_d=10, vitamin_b12=9),
        ]
        labs = LabResultItem(id=2, user_id=1)  # toate None

        ctx = self._make_repo_patches(user, foods, labs)
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            resp = self.client.post("/api/recommendations", json={"user_id": 1})

        self.assertEqual(resp.status_code, 200, resp.text)
        payload = resp.json()
        self.assertGreater(len(payload), 0)
        reasons_text = " ".join(
            " ".join(rec.get("explanation", {}).get("reasons", [])) for rec in payload
        ).lower()
        self.assertNotIn("analizele medicale", reasons_text)

    def test_low_hemoglobin_without_ferritin_triggers_iron_context(self):
        user = make_user_profile()
        foods = [
            FoodItem(id=30, name="Ficat de pui", category="carne", iron=8.5, vitamin_b12=16),
            FoodItem(id=31, name="Castravete", category="legume", iron=0.3, vitamin_c=5),
        ]
        labs = LabResultItem(id=3, user_id=1, hemoglobin=11.0, ferritin=None)

        ctx = self._make_repo_patches(user, foods, labs)
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            resp = self.client.post("/api/recommendations", json={"user_id": 1})

        self.assertEqual(resp.status_code, 200, resp.text)
        payload = resp.json()
        text_blob = " ".join(rec.get("explanation", {}).get("text", "") for rec in payload).lower()
        self.assertIn("fier", text_blob)


if __name__ == "__main__":
    unittest.main()
