"""API: parametrul lang, endpoint-ul de explicație și semnalul explanations_outdated (Supabase înlocuit cu repo-uri false)."""
import re
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import main as main_module
from domain.models import FoodItem, LabResultItem, RecommendationItem, UserProfile
from services import recommendation_materialize as materialize_module

ROMANIAN_LETTERS = re.compile(r"[ăâîșțĂÂÎȘȚ]")

USER = UserProfile(id=1, email="tester@example.com", name="Tester", age=30, sex="F", weight=60, height=165,
                   activity_level="moderate", diet_type="omnivore", allergies="", medical_conditions="")
FOODS = [
    FoodItem(id=10, name="Spanac fiert", name_en="Boiled Spinach", category="legume", iron=3.6, vitamin_c=9, protein=3),
    FoodItem(id=11, name="Linte fiartă", name_en="Boiled Lentils", category="leguminoase", iron=3.3, folate=180, protein=9),
    FoodItem(id=12, name="Ficat de pui", name_en=None, category="carne", iron=9.0, vitamin_b12=16, protein=17),
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

    def _generate(self, lang):
        resp = self.client.post(f"/api/recommendations?force_regenerate=true&lang={lang}", json={"user_id": 1})
        self.assertEqual(resp.status_code, 200, resp.text)
        return resp.json()

    def test_generation_returns_english_names_and_explanations_for_lang_en(self):
        items = self._generate("en")
        self.assertTrue(items)
        by_id = {i["food_id"]: i for i in items}
        self.assertEqual(by_id[10]["food"]["name"], "Boiled Spinach")
        for item in items:
            text = " ".join([item["explanation"]["text"], *item["explanation"]["reasons"], *(item["explanation"]["tips"] or [])])
            self.assertIn("below the clinical threshold for: iron", item["explanation"]["text"])
            self.assertIn("Ferritin: 12 ng/mL (threshold: 30 ng/mL)", " ".join(item["explanation"]["reasons"]))
            self.assertFalse(ROMANIAN_LETTERS.search(text), text)

    def test_same_stored_recommendations_render_in_romanian_without_regenerating(self):
        self._generate("en")
        stored_ids = [r.id for r in _Store.rows]
        items = self.client.get("/api/recommendations/stored/1?lang=ro").json()
        self.assertEqual([r.id for r in _Store.rows], stored_ids)  # nimic regenerat
        by_id = {i["food_id"]: i for i in items}
        self.assertEqual(by_id[10]["food"]["name"], "Spanac fiert")
        self.assertIn("valori sub pragul clinic pentru: fier", by_id[10]["explanation"]["text"])
        self.assertIn("Feritină: 12 ng/mL (prag: 30 ng/mL)", " ".join(by_id[10]["explanation"]["reasons"]))

    def test_food_without_translation_falls_back_to_romanian_name_in_english(self):
        self._generate("ro")
        by_id = {i["food_id"]: i for i in self.client.get("/api/recommendations/stored/1?lang=en").json()}
        self.assertEqual(by_id[12]["food"]["name"], "Ficat de pui")

    def test_explanation_endpoint_returns_one_recommendation_in_requested_language(self):
        self._generate("ro")
        rec_id = _Store.rows[0].id
        resp = self.client.get(f"/api/recommendations/1/{rec_id}/explanation?lang=en")
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertEqual((body["recommendation_id"], body["lang"]), (rec_id, "en"))
        self.assertIn("recommended because your lab results", body["explanation"]["text"])
        self.assertEqual(self.client.get("/api/recommendations/1/99999/explanation").status_code, 404)

    def test_unknown_language_defaults_to_romanian(self):
        self._generate("ro")
        body = self.client.get(f"/api/recommendations/1/{_Store.rows[0].id}/explanation?lang=xx").json()
        self.assertEqual(body["lang"], "ro")

    def test_sync_meta_flags_recommendations_created_before_facts(self):
        _Store.rows = [RecommendationItem(id=1, user_id=1, food_id=10, score=1.0, explanation="Text vechi",
                                          portion_suggested=100, created_at="2099-01-01T00:00:00+00:00")]
        self.assertTrue(self.client.get("/api/recommendations/sync-meta/1").json()["explanations_outdated"])

    def test_legacy_recommendations_are_regenerated_once_then_no_longer_outdated(self):
        _Store.rows = [RecommendationItem(id=1, user_id=1, food_id=10, score=1.0, explanation="Text vechi",
                                          portion_suggested=100, created_at="2099-01-01T00:00:00+00:00")]
        _Store.seq = 2
        # fără force_regenerate: rândurile vechi (fără fapte) declanșează singure regenerarea
        resp = self.client.post("/api/recommendations?lang=en", json={"user_id": 1})
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertNotIn("Text vechi", resp.text)
        self.assertFalse(self.client.get("/api/recommendations/sync-meta/1").json()["explanations_outdated"])


if __name__ == "__main__":
    unittest.main()
