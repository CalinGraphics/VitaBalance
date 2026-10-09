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
    from services.recommendations import materialize as materialize_module
from domain.models import FeedbackItem, FoodItem, LabResultItem, RecommendationItem, UserProfile
from tests.catalog_fixture import food


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

            def get_counts_by_food_ids(self, food_ids, user_id=None):
                return {int(fid): {"likes": 0, "dislikes": 0} for fid in food_ids}

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
                        explanation_json=r.get("explanation_json"),
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
            # `/api/recommendations` delega la materialize_recommendations(), care își
            # importă propriile referințe la repo-uri (nu pe cele din `main`) — fără aceste
            # patch-uri, testele loveau baza de date reală și primeau 404/liste goale.
            patch.object(materialize_module, "UserRepository", FakeUserRepo),
            patch.object(materialize_module, "FoodRepository", FakeFoodRepo),
            patch.object(materialize_module, "LabResultRepository", FakeLabRepo),
            patch.object(materialize_module, "FeedbackRepository", FakeFeedbackRepo),
            patch.object(materialize_module, "RecommendationRepository", FakeRecRepo),
        ]

    def test_excludes_chicken_when_medical_condition_says_no_chicken(self):
        user = make_user_profile(medical_conditions="nu mananc pui")
        foods = [food("chicken_breast", id=10), food("salmon_farmed", id=11), food("lentils", id=12)]
        labs = LabResultItem(id=1, user_id=1)  # fără biomarkeri completați

        ctx = self._make_repo_patches(user, foods, labs)
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4], ctx[5], ctx[6], ctx[7], ctx[8], ctx[9]:
            resp = self.client.post("/api/recommendations", json={"user_id": 1})

        self.assertEqual(resp.status_code, 200, resp.text)
        payload = resp.json()
        names = [r["food"]["name_ro"].lower() for r in payload]
        self.assertFalse(any("pui" in n for n in names), payload)

    def test_no_lab_data_uses_profile_wording_not_medical_analyses(self):
        user = make_user_profile()
        foods = [food("chickpeas", id=21), food("mackerel", id=22)]
        labs = LabResultItem(id=2, user_id=1)  # toate None

        ctx = self._make_repo_patches(user, foods, labs)
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4], ctx[5], ctx[6], ctx[7], ctx[8], ctx[9]:
            resp = self.client.post("/api/recommendations", json={"user_id": 1})

        self.assertEqual(resp.status_code, 200, resp.text)
        payload = resp.json()
        self.assertGreater(len(payload), 0)
        # fără analize: nicio nevoie „din analize”, doar contribuții generale
        sources = {n["need"]["source"] for rec in payload for n in rec["facts"]["nutrients"]}
        self.assertEqual(sources, {"general"})

    def test_low_hemoglobin_without_ferritin_triggers_iron_context(self):
        user = make_user_profile()
        foods = [food("chicken_liver", id=30), food("cucumber", id=31)]
        labs = LabResultItem(id=3, user_id=1, hemoglobin=11.0, ferritin=None)

        ctx = self._make_repo_patches(user, foods, labs)
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4], ctx[5], ctx[6], ctx[7], ctx[8], ctx[9]:
            resp = self.client.post("/api/recommendations", json={"user_id": 1})

        self.assertEqual(resp.status_code, 200, resp.text)
        payload = resp.json()
        needs = [n["need"] for rec in payload for n in rec["facts"]["nutrients"]]
        self.assertTrue(any(n.get("marker") == "hemoglobin" and n["nutrient"] == "iron" for n in needs))

    def test_list_stored_recommendations_returns_db_rows(self):
        user = make_user_profile()
        foods = [food("oats", id=40)]
        labs = LabResultItem(id=4, user_id=1)

        class FakeRecRepoWithRows:
            def get_by_user_id(self, user_id, limit=10):
                return [
                    RecommendationItem(
                        id=99,
                        user_id=1,
                        food_id=40,
                        score=4.2,
                        explanation="Test explicație",
                        portion_suggested=150.0,
                        coverage_percentage=12.5,
                    )
                ]

            def get_first_by_user_id(self, user_id):
                return None

            def insert_many(self, rows):
                return []

            def delete_by_user_id(self, user_id):
                pass

            def delete_by_id(self, recommendation_id):
                pass

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
                return labs if user_id == user.id else None

        class FakeFeedbackRepo:
            def get_by_user_id(self, user_id):
                # votul utilizatorului; contorul vine din această listă (fără o a doua interogare)
                return [FeedbackItem(id=1, user_id=1, food_id=40, rating=5)]

        with (
            patch.object(main_module, "UserRepository", FakeUserRepo),
            patch.object(main_module, "FoodRepository", FakeFoodRepo),
            patch.object(main_module, "LabResultRepository", FakeLabRepo),
            patch.object(main_module, "FeedbackRepository", FakeFeedbackRepo),
            patch.object(main_module, "RecommendationRepository", FakeRecRepoWithRows),
            # `/api/recommendations/stored/{id}` delegă la list_stored_recommendations_fast(),
            # care își importă propriile referințe la repo-uri (nu pe cele din `main`).
            patch.object(materialize_module, "UserRepository", FakeUserRepo),
            patch.object(materialize_module, "FoodRepository", FakeFoodRepo),
            patch.object(materialize_module, "LabResultRepository", FakeLabRepo),
            patch.object(materialize_module, "FeedbackRepository", FakeFeedbackRepo),
            patch.object(materialize_module, "RecommendationRepository", FakeRecRepoWithRows),
        ):
            resp = self.client.get("/api/recommendations/stored/1")

        self.assertEqual(resp.status_code, 200, resp.text)
        payload = resp.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["food_id"], 40)
        self.assertEqual(payload[0]["legacy"]["text"], "Test explicație")
        self.assertEqual(payload[0]["feedback"]["likes"], 1)
        self.assertEqual(payload[0]["my_rating"], 5)


if __name__ == "__main__":
    unittest.main()


def test_stale_pending_refresh_does_not_block_new_jobs():
    from datetime import datetime, timedelta, timezone
    from main import _refresh_pending_is_stale

    now = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
    assert not _refresh_pending_is_stale((now - timedelta(seconds=30)).isoformat(), now)
    assert _refresh_pending_is_stale((now - timedelta(minutes=10)).isoformat(), now)
    assert _refresh_pending_is_stale("2026-10-10T11:00:00Z", now)
    assert _refresh_pending_is_stale(None, now)
