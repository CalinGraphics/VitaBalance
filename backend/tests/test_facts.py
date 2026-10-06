"""Faptele salvate cu fiecare recomandare: independente de limbă, cu sursa deficitului și urma scorului."""
from domain.models import LabResultItem, UserProfile
from services.explanations.facts import has_facts
from services.explanations.storage import explanation_to_db_fields, facts_from_row, legacy_explanation
from services.explanations.facts import build_facts
from services.nutrition.needs import detect_needs
from services.recommendations.scoring import rank_foods
from tests.catalog_fixture import food


def _user(**kw) -> UserProfile:
    base = dict(id=1, email="a@b.ro", name="A", age=30, sex="F", weight=60, height=165,
                activity_level="moderate", diet_type="omnivore", allergies="", medical_conditions="")
    base.update(kw)
    return UserProfile(**base)


def _lab(**kw) -> LabResultItem:
    return LabResultItem(id=1, user_id=1, **kw)


def _facts(user, lab, key="spinach_cooked"):
    ranking = rank_foods([food(key)], detect_needs(user, lab))
    assert ranking.items, f"{key} nu a fost recomandat"
    return build_facts(ranking.items[0], ranking, has_lab_data=lab is not None)


def test_lab_need_carries_value_threshold_unit_and_severity():
    iron = _facts(_user(), _lab(ferritin=12.0))["nutrients"][0]
    assert iron["key"] == "iron"
    assert iron["need"] == {"nutrient": "iron", "source": "lab", "severity": "moderate", "daily_reference": 16.0,
                            "marker": "ferritin", "value": 12.0, "threshold": 15.0, "unit": "ng/mL"}


def test_hemoglobin_fallback_with_sex_specific_threshold():
    assert _facts(_user(), _lab(hemoglobin=10.5))["nutrients"][0]["need"]["threshold"] == 12.0
    assert _facts(_user(sex="M"), _lab(hemoglobin=12.5))["nutrients"][0]["need"]["threshold"] == 13.0


def test_notes_source_only_without_a_lab_value():
    notes = _facts(_user(medical_conditions="deficiență de magneziu"), None)
    assert notes["nutrients"][0]["need"]["source"] == "notes"
    lab = _facts(_user(medical_conditions="deficiență de magneziu"), _lab(magnesium=1.4))
    assert next(n for n in lab["nutrients"] if n["key"] == "magnesium")["need"]["source"] == "lab"


def test_only_deficit_nutrients_are_listed():
    facts = _facts(_user(), _lab(ferritin=12.0, calcium=9.5, magnesium=2.0, potassium=4.2))
    assert [n["key"] for n in facts["nutrients"]] == ["iron"]


def test_without_deficits_contributions_are_general():
    facts = _facts(_user(), None)
    assert facts["nutrients"] and all(n["need"]["source"] == "general" for n in facts["nutrients"])
    assert facts["has_lab_data"] is False


def test_profile_rules_portion_and_trace_are_stored():
    facts = _facts(_user(sex="F", diet_type="vegan", allergies="lactoza, nuci", medical_conditions="hipertensiune"),
                   _lab(vitamin_b12=165.0), key="soy_milk_fortified")
    assert facts["profile"] == {"diet": "vegan", "allergies": ["lactoza", "nuci"], "conditions": ["hypertension"]}
    assert "hypertension_limit_sodium" in facts["safety_rules"]
    assert facts["portion"] == {"amount": 250, "unit": "ml", "label_ro": "un pahar (250 ml)", "label_en": "a glass (250 ml)"}
    assert facts["kcal_portion"] == 82 and facts["primary"] == "vitamin_b12" and facts["category"] == "plant_milks"
    assert facts["trace"]["components"] and facts["trace"]["score"] > 0


def test_facts_roundtrip_through_db_fields():
    facts = _facts(_user(), _lab(ferritin=12.0))
    fields = explanation_to_db_fields(facts)
    assert has_facts(fields["explanation_json"]) and fields["explanation"] == "" and fields["portion_suggested"] == 80
    assert facts_from_row(fields["explanation_json"]) == facts


def test_legacy_rows_without_facts_keep_their_stored_text():
    legacy = {"explanation_json": {"text": "Text vechi", "portion": 100, "reasons": ["r"], "tips": None},
              "explanation": "Text vechi"}
    assert facts_from_row(legacy["explanation_json"]) is None
    assert legacy_explanation(legacy) == {"text": "Text vechi", "reasons": ["r"], "tips": []}
