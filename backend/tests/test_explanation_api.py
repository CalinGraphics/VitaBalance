"""API independent de limbă: fapte + nume RO/EN, endpoint-ul de explicație, explanations_outdated (repo-uri false)."""
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import main as main_module
from domain.models import FoodItem, LabResultItem, RecommendationItem, UserProfile
from services.recommendations import materialize as materialize_module
from tests.catalog_fixture import food


USER = UserProfile(id=1, email="tester@example.com", name="Tester", age=30, sex="F", weight=60, height=165,
                   activity_level="moderate", diet_type="omnivore", allergies="", medical_conditions="")
# Alimente reale din catalogul validat; id-uri fixe ca testele să fie ușor de citit. Ficatul nu are nume EN,
# ca să verificăm revenirea la numele românesc.
FOODS = [
    food("spinach_cooked", id=10),
    food("lentils", id=11),
    food("chicken_liver", id=12, name_en=None),
]
LABS = LabResultItem(id=1, user_id=1, ferritin=12.0)


class _Store:
    rows: list = []
    seq = 1


class FakeUserRepo:
    def get_by_email(self, email):
        return USER if email.lower() == USER.email.lower() else None

    def get_by_id(self, user_id):
        return USER if user_id == USER.id else None


class FakeFoodRepo:
    def get_all(self):
        return FOODS


class FakeLabRepo:
    def get_latest_by_user_id(self, user_id):
        return LABS


class FakeFeedbackRepo:
    def get_by_user_id(self, user_id):
        return []

    def get_counts_by_food_ids(self, food_ids, user_id=None):
        return {int(f): {"likes": 0, "dislikes": 0} for f in food_ids}


class FakeRecRepo:
    """Stare comună între instanțe (ca baza de date): păstrează și explanation_json."""

    def get_by_user_id(self, user_id, limit=10):
        return _Store.rows[:limit]

    def get_first_by_user_id(self, user_id):
        return _Store.rows[-1] if _Store.rows else None

    def insert_many(self, rows):
        out = []
        for r in rows:
            rec = RecommendationItem(
                id=_Store.seq, user_id=r["user_id"], food_id=r["food_id"], score=float(r["score"]),
                explanation=r["explanation"], portion_suggested=float(r["portion_suggested"]),
                coverage_percentage=float(r["coverage_percentage"]), explanation_json=r["explanation_json"],
                reasons=r["reasons"], tips=r["tips"], created_at="2099-01-01T00:00:00+00:00",
            )
            _Store.seq += 1
            _Store.rows.append(rec)
            out.append(rec)
        return out

    def delete_by_user_id(self, user_id):
        _Store.rows = []

    def delete_by_id(self, recommendation_id):
        _Store.rows = [r for r in _Store.rows if r.id != recommendation_id]


class ExplanationApiTests(unittest.TestCase):
    def setUp(self):
        _Store.rows, _Store.seq = [], 1
        self.client = TestClient(main_module.app)
        main_module.app.dependency_overrides[main_module.get_current_user] = lambda: {"email": USER.email}
        self.patches = []
        for module in (main_module, materialize_module):
            for name, fake in (("UserRepository", FakeUserRepo), ("FoodRepository", FakeFoodRepo),
                               ("LabResultRepository", FakeLabRepo), ("FeedbackRepository", FakeFeedbackRepo),
                               ("RecommendationRepository", FakeRecRepo)):
                p = patch.object(module, name, fake)
                p.start()
                self.patches.append(p)

    def tearDown(self):
        for p in self.patches:
            p.stop()
        main_module.app.dependency_overrides = {}

    def _generate(self):
        resp = self.client.post("/api/recommendations?force_regenerate=true", json={"user_id": 1})
        self.assertEqual(resp.status_code, 200, resp.text)
        return resp.json()

    def test_generation_returns_language_independent_items(self):
        items = self._generate()
        self.assertTrue(items)
        by_id = {i["food_id"]: i for i in items}
        self.assertEqual((by_id[10]["food"]["name_ro"], by_id[10]["food"]["name_en"]), ("Spanac fiert", "Cooked spinach"))
        for item in items:
            need = item["facts"]["nutrients"][0]["need"]
            self.assertEqual((need["source"], need["marker"], need["value"], need["threshold"]), ("lab", "ferritin", 12.0, 15.0))
            self.assertIsNone(item["legacy"])
            # niciun text în răspuns: doar chei, cifre și nume
            self.assertNotIn("text", item)

    def test_lang_query_does_not_change_the_response(self):
        self._generate()
        ro = self.client.get("/api/recommendations/stored/1?lang=ro").json()
        en = self.client.get("/api/recommendations/stored/1?lang=en").json()
        self.assertEqual(ro, en)

    def test_food_without_translation_falls_back_to_romanian_name(self):
        self._generate()
        by_id = {i["food_id"]: i for i in self.client.get("/api/recommendations/stored/1").json()}
        self.assertEqual(by_id[12]["food"]["name_en"], "Ficat de pui gătit")

    def test_alternatives_come_with_both_names(self):
        items = self._generate()
        for item in items:
            for alt in item["alternatives"]:
                self.assertEqual(set(alt), {"id", "name_ro", "name_en"})

    def test_explanation_endpoint_returns_one_recommendation(self):
        self._generate()
        rec_id = _Store.rows[0].id
        resp = self.client.get(f"/api/recommendations/1/{rec_id}/explanation")
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertEqual(body["recommendation_id"], rec_id)
        self.assertIn("trace", body["facts"])
        self.assertEqual(self.client.get("/api/recommendations/1/99999/explanation").status_code, 404)

    def test_sync_meta_flags_recommendations_created_before_facts(self):
        _Store.rows = [RecommendationItem(id=1, user_id=1, food_id=10, score=1.0, explanation="Text vechi",
                                          portion_suggested=100, created_at="2099-01-01T00:00:00+00:00")]
        self.assertTrue(self.client.get("/api/recommendations/sync-meta/1").json()["explanations_outdated"])

    def test_legacy_recommendations_are_regenerated_once_then_no_longer_outdated(self):
        _Store.rows = [RecommendationItem(id=1, user_id=1, food_id=10, score=1.0, explanation="Text vechi",
                                          portion_suggested=100, created_at="2099-01-01T00:00:00+00:00")]
        _Store.seq = 2
        # fără force_regenerate: rândurile vechi (fără fapte) declanșează singure regenerarea
        resp = self.client.post("/api/recommendations", json={"user_id": 1})
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertNotIn("Text vechi", resp.text)
        self.assertFalse(self.client.get("/api/recommendations/sync-meta/1").json()["explanations_outdated"])


if __name__ == "__main__":
    unittest.main()
