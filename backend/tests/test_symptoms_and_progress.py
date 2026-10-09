"""Jurnalul de stare: simptomele ajustează confortul, sugerează analize, recomandă consult — nu creează deficite."""
from datetime import date, timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient

import main as main_module
from domain.models import CheckIn, LabResultItem, UserProfile
from rules.symptoms import SYMPTOM_CODES, SYMPTOM_RULES, analyse, symptom_factors
from services.nutrition.needs import detect_needs
from services.progress import build_progress
from services.recommendations.recommender import RecommenderService, recommendation_inputs_hash
from tests.catalog_fixture import all_foods, food
from tests.conftest import FakeCheckinRepository

FOODS = all_foods()
TODAY = date.today()
USER = UserProfile(id=1, email="s@s.ro", name="S", age=30, sex="F", weight=60, height=165,
                   activity_level="moderate", diet_type="omnivore", allergies="", medical_conditions="")


def _c(days_ago, symptoms, severity=1, **kw):
    return CheckIn(id=days_ago + 1, user_id=1, checked_on=(TODAY - timedelta(days=days_ago)).isoformat(),
                   symptoms=tuple(symptoms), severity=severity, **kw)


# ---------- reguli ----------

def test_every_symptom_rule_has_a_source_and_known_code():
    assert all(r.source and r.symptom in SYMPTOM_CODES for r in SYMPTOM_RULES)
    assert len({r.id for r in SYMPTOM_RULES}) == len(SYMPTOM_RULES)


def test_nausea_prefers_lighter_foods():
    assert ("nausea_lighter_foods", 0.6) in symptom_factors(food("salmon_farmed"), frozenset({"greata"}))  # ~16 g grăsime
    assert symptom_factors(food("spinach_cooked"), frozenset({"greata"})) == []


def test_constipation_prefers_fibre_and_bloating_avoids_gassy_foods():
    assert ("constipation_more_fibre", 1.2) in symptom_factors(food("lentils"), frozenset({"constipatie"}))
    assert ("bloating_fewer_gassy_foods", 0.8) in symptom_factors(food("black_beans"), frozenset({"balonare"}))
    assert symptom_factors(food("carrots"), frozenset({"balonare"})) == []


def test_symptoms_never_create_deficits():
    needs = detect_needs(UserProfile(**{**USER.__dict__, "medical_conditions": ""}), None)
    assert needs.needs == []
    r = RecommenderService().rank(USER, FOODS, None, symptoms={"oboseala", "ameteli", "crampe_musculare"})
    assert r.targeted == [] and r.needs == []


# ---------- interpretare ----------

def test_lab_hints_only_for_missing_labs():
    ins = analyse([_c(0, ["oboseala"])], {"hemoglobin": 13.0, "ferritin": None, "vitamin_b12": None, "vitamin_d": 35})
    assert ins.lab_suggestions == ("ferritin", "vitamin_b12")
    cramps = analyse([_c(1, ["crampe_musculare"])], {})
    assert cramps.lab_suggestions == ("magnesium", "potassium", "calcium")


def test_see_doctor_when_severe_persistent_or_vomiting_two_days():
    assert analyse([_c(0, ["ameteli"], severity=3)], {}).see_doctor_reasons == ("severe",)
    assert "persistent" in analyse([_c(d, ["greata"]) for d in range(4)], {}).see_doctor_reasons
    assert "vomiting_2_days" in analyse([_c(0, ["varsaturi"]), _c(2, ["varsaturi"])], {}).see_doctor_reasons
    assert not analyse([_c(0, ["dureri_cap"])], {}).see_doctor


def test_old_checkins_are_ignored():
    assert analyse([_c(20, ["greata"], severity=3)], {}).recent == frozenset()


# ---------- recomandări ----------

def test_symptoms_change_ranking_hash_and_facts():
    from services.explanations.facts import build_facts

    labs = LabResultItem(id=1, user_id=1, vitamin_d=15)
    base = RecommenderService().rank(USER, FOODS, labs)
    nausea = RecommenderService().rank(USER, FOODS, labs, symptoms={"greata"})
    assert recommendation_inputs_hash(USER, FOODS, labs) != recommendation_inputs_hash(USER, FOODS, labs, {"greata"})
    salmon = lambda r: next(s for s in r.eligible if s.food.food_key == "salmon_farmed")  # noqa: E731
    assert salmon(nausea).score < salmon(base).score
    facts = build_facts(salmon(nausea), nausea, has_lab_data=True)
    assert facts["symptoms"] == ["greata"] and facts["symptom_adjustments"] == ["nausea_lighter_foods"]


# ---------- progres ----------

def test_progress_series_and_insights():
    history = [LabResultItem(id=2, user_id=1, ferritin=20, updated_at="2026-09-01T00:00:00Z"),
               LabResultItem(id=1, user_id=1, ferritin=9, hemoglobin=11.0, updated_at="2026-06-01T00:00:00Z")]
    p = build_progress(USER, [_c(0, ["oboseala"], energy=2, weight=59.5)], history)
    ferr = p["series"]["labs"]["ferritin"]
    assert [pt["value"] for pt in ferr["points"]] == [9.0, 20.0] and ferr["low"] == 15.0 and ferr["unit"] == "ng/mL"
    assert p["series"]["labs"]["hemoglobin"]["low"] == 12.0  # limita pentru femei
    assert p["series"]["weight"] == [{"date": TODAY.isoformat(), "value": 59.5}]
    assert p["insights"]["recent_symptoms"] == ["oboseala"]
    assert p["insights"]["lab_suggestions"] == ["vitamin_b12", "vitamin_d"]  # feritina și hemoglobina există


# ---------- API ----------

class _FakeUsers:
    def get_by_email(self, email):
        return USER

    def get_by_id(self, user_id):
        return USER


class _FakeLabs:
    def get_all_by_user_id(self, user_id):
        return []


class _SavingCheckins(FakeCheckinRepository):
    def upsert_for_day(self, user_id, day, data):
        return CheckIn(id=7, user_id=user_id, checked_on=day.isoformat(), symptoms=tuple(data["symptoms"]),
                       severity=data["severity"], energy=data["energy"], weight=data["weight"], notes=data["notes"])


def _client():
    main_module.app.dependency_overrides[main_module.get_current_user] = lambda: {"email": USER.email}
    return TestClient(main_module.app)


def test_checkin_api_validates_and_saves():
    with patch.object(main_module, "UserRepository", _FakeUsers), patch.object(main_module, "CheckinRepository", _SavingCheckins):
        c = _client()
        ok = c.post("/api/checkins", json={"user_id": 1, "symptoms": ["greata", "ameteli"], "severity": 2, "energy": 3})
        assert ok.status_code == 200, ok.text
        assert ok.json()["symptoms"] == ["ameteli", "greata"]
        assert c.post("/api/checkins", json={"user_id": 1, "symptoms": ["febra"]}).status_code == 400
        assert c.post("/api/checkins", json={"user_id": 1}).status_code == 400
        future = (TODAY + timedelta(days=2)).isoformat()
        assert c.post("/api/checkins", json={"user_id": 1, "energy": 3, "checked_on": future}).status_code == 400
        assert c.post("/api/checkins", json={"user_id": 1, "energy": 9}).status_code == 422
    main_module.app.dependency_overrides = {}


def test_checkin_api_reports_missing_table():
    from repositories.checkin_repository import CheckinStoreUnavailable

    class _Missing(FakeCheckinRepository):
        def upsert_for_day(self, *a, **k):
            raise CheckinStoreUnavailable()

    with patch.object(main_module, "UserRepository", _FakeUsers), patch.object(main_module, "CheckinRepository", _Missing):
        resp = _client().post("/api/checkins", json={"user_id": 1, "energy": 3})
        assert resp.status_code == 503
    main_module.app.dependency_overrides = {}


def test_progress_api():
    with patch.object(main_module, "UserRepository", _FakeUsers), patch.object(main_module, "LabResultRepository", _FakeLabs):
        resp = _client().get("/api/progress/1")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["storage_available"] is True and body["symptom_codes"] == list(SYMPTOM_CODES)
    main_module.app.dependency_overrides = {}


def test_same_comfort_advice_applies_once_for_several_symptoms():
    factors = symptom_factors(food("salmon_farmed"), frozenset({"greata", "varsaturi", "diaree", "lipsa_poftei"}))
    assert [f for _, f in factors] == [0.6]
