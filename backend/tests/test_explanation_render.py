"""Explicații specifice pacientului, randate din fapte în RO/EN."""
import re

from domain.models import FoodItem, LabResultItem, UserProfile, food_display_name
from services import explanation_i18n as i18n
from services.deficit_calculator import DeficitCalculator
from services.explanation_facts import CONDITION_PATTERNS, NUTRIENT_KEYS, alternatives_for, build_facts, has_facts
from services.explanation_renderer import SECTION_SEP, render_explanation
from services.explanation_storage import explanation_from_db_row, explanation_to_db_fields
from services.portion_calculator import PortionSuggestion

PORTION = PortionSuggestion(amount=150, unit="g", grams_equivalent=150)
ROMANIAN_LETTERS = re.compile(r"[ăâîșțĂÂÎȘȚ]")


def _user(**kw) -> UserProfile:
    base = dict(id=1, email="a@b.ro", name="A", age=30, sex="F", weight=60, height=165,
                activity_level="moderate", diet_type="omnivore", allergies="", medical_conditions="")
    base.update(kw)
    return UserProfile(**base)


def _lab(**kw) -> LabResultItem:
    return LabResultItem(id=1, user_id=1, **kw)


def _food(**kw) -> FoodItem:
    base = dict(id=1, name="Spanac", name_en="Spinach", category="Legume",
                iron=2.7, calcium=99, vitamin_c=28, magnesium=79, potassium=558, vitamin_b12=1.2)
    base.update(kw)
    return FoodItem(**base)


def _facts(user, lab, food=None, covered=None, has_lab=True):
    food = food or _food()
    deficits = DeficitCalculator().calculate_deficits(user, lab)
    rec = {"nutrients_covered": covered or [], "coverage": 30.0, "score": 5.0, "matched_rules": []}
    return build_facts(food=food, user=user, lab_results=lab, deficits=deficits, rec=rec,
                       portion=PORTION, has_lab_data=has_lab)


def _all_text(expl) -> str:
    return " ".join([expl["text"], *expl["reasons"], *(expl["tips"] or []), *(expl["alternatives"] or [])])


# ---------- specific pacientului ----------

def test_lab_value_and_threshold_are_quoted_in_both_languages():
    facts = _facts(_user(), _lab(ferritin=12.0), covered=["iron"])
    iron = facts["nutrients"][0]
    assert iron["key"] == "iron"
    assert iron["need"] == {"source": "lab", "marker": "ferritin", "value": 12.0, "threshold": 30.0, "unit": "ng/mL"}

    ro = render_explanation(facts, food_name="Spanac", lang="ro")
    en = render_explanation(facts, food_name="Spinach", lang="en")
    assert "Feritină: 12 ng/mL (prag: 30 ng/mL)" in ro["reasons"][0]
    assert "Ferritin: 12 ng/mL (threshold: 30 ng/mL)" in en["reasons"][0]
    assert "valori sub pragul clinic pentru: fier" in ro["text"]
    assert "below the clinical threshold for: iron" in en["text"]


def test_hemoglobin_is_used_when_ferritin_is_missing():
    facts = _facts(_user(), _lab(hemoglobin=10.5), covered=["iron"])
    need = facts["nutrients"][0]["need"]
    assert (need["marker"], need["value"], need["threshold"], need["unit"]) == ("hemoglobin", 10.5, 12.0, "g/dL")


def test_decimal_separator_follows_language():
    facts = _facts(_user(), _lab(hemoglobin=10.5), covered=["iron"])
    assert "10,5 g/dL" in render_explanation(facts, food_name="x", lang="ro")["reasons"][0]
    assert "10.5 g/dL" in render_explanation(facts, food_name="x", lang="en")["reasons"][0]


def test_diet_allergies_and_conditions_appear_with_their_restriction():
    user = _user(diet_type="vegan", allergies="lactoza, nuci", medical_conditions="hipertensiune")
    facts = _facts(user, _lab(vitamin_b12=165.0), covered=["vitamin_b12"])
    assert facts["profile"] == {"diet": "vegan", "allergies": ["lactoza", "nuci"], "conditions": ["hypertension"]}

    ro = render_explanation(facts, food_name="Spanac", lang="ro")
    en = render_explanation(facts, food_name="Spinach", lang="en")
    ro_reasons, en_reasons = " ".join(ro["reasons"]), " ".join(en["reasons"])
    assert "dieta vegană" in ro_reasons and "lactoză și nuci" in ro_reasons and "hipertensiune" in ro_reasons
    assert "fără sare adăugată" in ro_reasons
    assert "a vegan diet" in en_reasons and "lactose and tree nuts" in en_reasons and "hypertension" in en_reasons
    assert "no added salt" in en_reasons
    assert any("dieta vegană" in t and "medicul" in t for t in ro["tips"])
    assert any("vegan diet" in t and "doctor" in t for t in en["tips"])


def test_need_mentioned_in_notes_is_worded_as_patient_reported():
    user = _user(medical_conditions="deficiență de magneziu")
    facts = _facts(user, None, food=_food(), has_lab=False)
    assert facts["nutrients"][0]["key"] == "magnesium"
    assert facts["nutrients"][0]["need"] == {"source": "notes"}
    ro = render_explanation(facts, food_name="Spanac", lang="ro")
    assert "ai menționat nevoia de: magneziu" in ro["text"]
    assert "nu ai încă analize" in " ".join(ro["reasons"])


# ---------- strict: doar ce ține de pacient ----------

def test_only_nutrients_with_a_modelled_deficit_are_mentioned():
    # Spanacul e bogat și în calciu/magneziu/potasiu, dar analizele arată deficit doar la fier.
    facts = _facts(_user(), _lab(ferritin=12.0, calcium=9.5, magnesium=2.0, potassium=4.2), covered=["iron", "calcium"])
    assert [n["key"] for n in facts["nutrients"]] == ["iron"]
    ro = render_explanation(facts, food_name="Spanac", lang="ro")
    assert "calciu" not in _all_text(ro) and "magneziu" not in _all_text(ro)


def test_without_deficits_only_general_contribution_is_stated_no_deficit_claim():
    facts = _facts(_user(), None, has_lab=False)
    assert facts["nutrients"] and all(n["need"]["source"] == "general" for n in facts["nutrients"])
    ro = render_explanation(facts, food_name="Spanac", lang="ro")
    assert "compatibil cu profilul tău" in ro["text"]
    assert "sub pragul" not in _all_text(ro) and "deficit" not in _all_text(ro).lower()


def test_kidney_condition_never_gets_a_generic_advice_to_increase_potassium():
    facts = _facts(_user(medical_conditions="insuficiență renală"), _lab(potassium=3.0), covered=["potassium"])
    ro = render_explanation(facts, food_name="Spanac", lang="ro")
    en = render_explanation(facts, food_name="Spinach", lang="en")
    assert any("discută cu medicul înainte de a crește aportul de potasiu" in t for t in ro["tips"])
    assert any("talk to your doctor before increasing your potassium" in t for t in en["tips"])
    assert i18n.TIPS["ro"]["potassium"] not in ro["tips"]


# ---------- traducere ----------

def test_english_output_has_no_romanian_text_and_matches_romanian_structure():
    user = _user(diet_type="vegan", allergies="oua", medical_conditions="hipertensiune, deficiență de magneziu")
    facts = _facts(user, _lab(ferritin=12.0, vitamin_b12=150.0), covered=["iron", "vitamin_b12"])
    facts["alternatives"] = [2, 3]
    names_en = {2: "Lentils", 3: "Tofu"}
    names_ro = {2: "Linte", 3: "Tofu"}
    ro = render_explanation(facts, food_name="Spanac", lang="ro", name_of=names_ro.get)
    en = render_explanation(facts, food_name="Spinach", lang="en", name_of=names_en.get)

    assert not ROMANIAN_LETTERS.search(_all_text(en)), _all_text(en)
    assert en["alternatives"] == ["Lentils", "Tofu"] and ro["alternatives"] == ["Linte", "Tofu"]
    assert len(en["reasons"]) == len(ro["reasons"])
    assert len(en["tips"]) == len(ro["tips"])
    assert len(en["text"].split(SECTION_SEP)) == len(ro["text"].split(SECTION_SEP))


def test_unknown_language_falls_back_to_romanian():
    facts = _facts(_user(), _lab(ferritin=12.0), covered=["iron"])
    assert render_explanation(facts, food_name="Spanac", lang="fr")["text"] == \
        render_explanation(facts, food_name="Spanac", lang="ro")["text"]
    assert [i18n.normalize_lang(x) for x in ("EN", "en-GB", "en_US", None, "de")] == ["en", "en", "en", "ro", "ro"]


def test_catalogs_are_complete_in_both_languages():
    for catalog in (i18n.SENTENCES, i18n.TIPS, i18n.NUTRIENT_LABELS, i18n.ALLERGY_LABELS,
                    i18n.CONDITION_LABELS, i18n.DIET_LABELS, i18n.MARKER_LABELS):
        assert set(catalog["ro"]) == set(catalog["en"])
    assert set(NUTRIENT_KEYS) == set(i18n.NUTRIENT_LABELS["ro"]) == set(i18n.NUTRIENT_UNITS)
    assert set(CONDITION_PATTERNS) == set(i18n.CONDITION_LABELS["ro"])


def test_food_display_name_uses_english_name_with_fallback():
    assert food_display_name(_food(), "en") == "Spinach"
    assert food_display_name(_food(name_en=None), "en") == "Spanac"
    assert food_display_name(_food(), "ro") == "Spanac"


# ---------- alternative ----------

def test_alternatives_share_the_primary_nutrient():
    recs = [{"food_id": 1}, {"food_id": 2}, {"food_id": 3}]
    keys = {1: ["iron", "calcium"], 2: ["calcium", "iron"], 3: ["magnesium"]}
    # 1 (fier) -> 2 conține fier; 2 (calciu) -> 1 conține calciu; 3 (magneziu) nu are alte surse în listă
    assert alternatives_for(recs, keys) == {1: [2], 2: [1], 3: []}


# ---------- persistență ----------

def test_facts_roundtrip_through_db_fields_and_render_in_requested_language():
    facts = _facts(_user(), _lab(ferritin=12.0), covered=["iron"])
    expl = render_explanation(facts, food_name="Spanac", lang="ro")
    expl["facts"] = facts
    fields = explanation_to_db_fields(expl)
    assert has_facts(fields["explanation_json"])
    assert fields["explanation"] == expl["text"]  # coloanele vechi rămân populate (RO)

    row = {"explanation_json": fields["explanation_json"], "explanation": fields["explanation"]}
    en = explanation_from_db_row(row, lang="en", food_name="Spinach")
    assert "below the clinical threshold" in en["text"]


def test_legacy_rows_without_facts_keep_their_stored_text():
    legacy = {"explanation_json": {"text": "Text vechi", "portion": 100, "reasons": ["r"], "tips": None},
              "explanation": "Text vechi"}
    assert not has_facts(legacy["explanation_json"])
    out = explanation_from_db_row(legacy, lang="en", food_name="Spinach")
    assert out["text"] == "Text vechi"
