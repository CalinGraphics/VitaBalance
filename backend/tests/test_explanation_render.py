"""Explicații specifice pacientului, randate din fapte în RO/EN (fapte produse de motorul real, pe catalogul real)."""
import re

from domain.models import LabResultItem, UserProfile, food_display_name
from services.explanations import i18n
from services.explanations.facts import NUTRIENT_KEYS, build_facts, has_facts
from services.explanations.renderer import SECTION_SEP, render_explanation
from services.explanations.storage import explanation_from_db_row, explanation_to_db_fields
from services.nutrition.needs import detect_needs
from services.nutrition.profile_context import CONDITION_CODES, TEXT_PATTERNS
from services.recommendations.scoring import rank_foods
from tests.catalog_fixture import food

ROMANIAN_LETTERS = re.compile(r"[ăâîșțĂÂÎȘȚ]")


def _user(**kw) -> UserProfile:
    base = dict(id=1, email="a@b.ro", name="A", age=30, sex="F", weight=60, height=165,
                activity_level="moderate", diet_type="omnivore", allergies="", medical_conditions="")
    base.update(kw)
    return UserProfile(**base)


def _lab(**kw) -> LabResultItem:
    return LabResultItem(id=1, user_id=1, **kw)


def _facts(user, lab, key="spinach_cooked"):
    f = food(key)
    ranking = rank_foods([f], detect_needs(user, lab))
    assert ranking.items, f"{key} nu a fost recomandat"
    return build_facts(ranking.items[0], ranking, has_lab_data=lab is not None)


def _all_text(expl) -> str:
    return " ".join([expl["text"], *expl["reasons"], *(expl["tips"] or []), *(expl["alternatives"] or [])])


# ---------- specific pacientului ----------

def test_lab_value_and_threshold_are_quoted_in_both_languages():
    facts = _facts(_user(), _lab(ferritin=12.0))
    iron = facts["nutrients"][0]
    assert iron["key"] == "iron"
    assert iron["need"] == {"nutrient": "iron", "source": "lab", "severity": "moderate", "daily_reference": 16.0,
                            "marker": "ferritin", "value": 12.0, "threshold": 15.0, "unit": "ng/mL"}

    ro = render_explanation(facts, food_name="Spanac fiert", lang="ro")
    en = render_explanation(facts, food_name="Cooked spinach", lang="en")
    assert "Feritină: 12 ng/mL (prag: 15 ng/mL)" in ro["reasons"][0]
    assert "Ferritin: 12 ng/mL (threshold: 15 ng/mL)" in en["reasons"][0]
    assert "valori sub pragul clinic pentru: fier" in ro["text"]
    assert "below the clinical threshold for: iron" in en["text"]


def test_hemoglobin_is_used_when_ferritin_is_missing_with_sex_specific_threshold():
    need = _facts(_user(), _lab(hemoglobin=10.5))["nutrients"][0]["need"]
    assert (need["marker"], need["value"], need["threshold"], need["unit"]) == ("hemoglobin", 10.5, 12.0, "g/dL")
    need_m = _facts(_user(sex="M"), _lab(hemoglobin=12.5))["nutrients"][0]["need"]
    assert need_m["threshold"] == 13.0


def test_decimal_separator_follows_language():
    facts = _facts(_user(), _lab(hemoglobin=10.5))
    assert "10,5 g/dL" in render_explanation(facts, food_name="x", lang="ro")["reasons"][0]
    assert "10.5 g/dL" in render_explanation(facts, food_name="x", lang="en")["reasons"][0]


def test_diet_allergies_and_conditions_appear_with_their_restriction():
    user = _user(diet_type="vegan", allergies="lactoza, nuci", medical_conditions="hipertensiune")
    facts = _facts(user, _lab(vitamin_b12=165.0), key="soy_milk_fortified")
    assert facts["profile"] == {"diet": "vegan", "allergies": ["lactoza", "nuci"], "conditions": ["hypertension"]}

    ro = render_explanation(facts, food_name="Lapte de soia", lang="ro")
    en = render_explanation(facts, food_name="Soy milk", lang="en")
    ro_reasons, en_reasons = " ".join(ro["reasons"]), " ".join(en["reasons"])
    assert "dieta vegană" in ro_reasons and "lactoză și nuci" in ro_reasons and "hipertensiune" in ro_reasons
    assert "fără alimente bogate în sare" in ro_reasons
    assert "a vegan diet" in en_reasons and "lactose and tree nuts" in en_reasons and "high blood pressure" in en_reasons
    assert "no high-salt foods" in en_reasons
    assert any("dieta vegană" in t and "medicul" in t for t in ro["tips"])
    assert any("vegan diet" in t and "doctor" in t for t in en["tips"])


def test_need_stated_in_notes_is_worded_as_user_reported_and_lab_need_never_is():
    facts = _facts(_user(medical_conditions="deficiență de magneziu"), None)
    assert facts["nutrients"][0]["key"] == "magnesium"
    assert facts["nutrients"][0]["need"]["source"] == "notes"
    ro = render_explanation(facts, food_name="Spanac", lang="ro")
    assert "ai menționat nevoia de: magneziu" in ro["text"]
    assert "nu ai încă analize" in " ".join(ro["reasons"])

    # Același text în observații, dar analiza arată deficit: sursa e analiza, nu „ai menționat”.
    lab_facts = _facts(_user(medical_conditions="deficiență de magneziu"), _lab(magnesium=1.4))
    mg = next(n for n in lab_facts["nutrients"] if n["key"] == "magnesium")
    assert mg["need"]["source"] == "lab"
    assert "menționat" not in render_explanation(lab_facts, food_name="Spanac", lang="ro")["text"]


# ---------- strict: doar ce ține de pacient ----------

def test_only_nutrients_with_a_deficit_are_mentioned():
    # Spanacul aduce și calciu/magneziu/potasiu, dar analizele arată deficit doar la fier.
    facts = _facts(_user(), _lab(ferritin=12.0, calcium=9.5, magnesium=2.0, potassium=4.2))
    assert [n["key"] for n in facts["nutrients"]] == ["iron"]
    ro = render_explanation(facts, food_name="Spanac", lang="ro")
    assert "calciu" not in _all_text(ro) and "magneziu" not in _all_text(ro)


def test_without_deficits_only_general_contribution_is_stated_no_deficit_claim():
    facts = _facts(_user(), None)
    assert facts["nutrients"] and all(n["need"]["source"] == "general" for n in facts["nutrients"])
    ro = render_explanation(facts, food_name="Spanac", lang="ro")
    assert "compatibil cu profilul tău" in ro["text"]
    assert "sub pragul" not in _all_text(ro) and "deficit" not in _all_text(ro).lower()


def test_every_tip_has_a_source():
    assert set(i18n.TIPS["ro"]) == set(i18n.TIPS["en"]) == set(i18n.TIP_SOURCES)
    assert all(i18n.TIP_SOURCES.values())


def test_vitamin_c_iron_tip_only_for_plant_iron():
    plant = render_explanation(_facts(_user(), _lab(ferritin=8.0), key="lentils"), food_name="x", lang="en")
    animal = render_explanation(_facts(_user(), _lab(ferritin=8.0), key="beef_lean"), food_name="x", lang="en")
    assert any("vitamin C" in t for t in plant["tips"] or [])
    assert not any("vitamin C" in t for t in animal["tips"] or [])


# ---------- traducere ----------

def test_english_output_has_no_romanian_text_and_matches_romanian_structure():
    user = _user(diet_type="vegan", allergies="oua", medical_conditions="hipertensiune, deficiență de magneziu")
    facts = _facts(user, _lab(ferritin=12.0, vitamin_b12=150.0))
    facts["alternatives"] = [2, 3]
    names_en = {2: "Lentils", 3: "Tofu"}
    names_ro = {2: "Linte", 3: "Tofu"}
    ro = render_explanation(facts, food_name="Spanac", lang="ro", name_of=names_ro.get)
    en = render_explanation(facts, food_name="Spinach", lang="en", name_of=names_en.get)

    assert not ROMANIAN_LETTERS.search(_all_text(en)), _all_text(en)
    assert en["alternatives"] == ["Lentils", "Tofu"] and ro["alternatives"] == ["Linte", "Tofu"]
    assert len(en["reasons"]) == len(ro["reasons"])
    assert len(en["tips"] or []) == len(ro["tips"] or [])
    assert len(en["text"].split(SECTION_SEP)) == len(ro["text"].split(SECTION_SEP))


def test_unknown_language_falls_back_to_romanian():
    facts = _facts(_user(), _lab(ferritin=12.0))
    assert render_explanation(facts, food_name="Spanac", lang="fr")["text"] == \
        render_explanation(facts, food_name="Spanac", lang="ro")["text"]
    assert [i18n.normalize_lang(x) for x in ("EN", "en-GB", "en_US", None, "de")] == ["en", "en", "en", "ro", "ro"]


def test_catalogs_are_complete_in_both_languages():
    for catalog in (i18n.SENTENCES, i18n.TIPS, i18n.NUTRIENT_LABELS, i18n.ALLERGY_LABELS,
                    i18n.CONDITION_LABELS, i18n.DIET_LABELS, i18n.MARKER_LABELS):
        assert set(catalog["ro"]) == set(catalog["en"])
    assert set(NUTRIENT_KEYS) == set(i18n.NUTRIENT_LABELS["ro"]) == set(i18n.NUTRIENT_UNITS)
    assert set(CONDITION_CODES.values()) | set(TEXT_PATTERNS) == set(i18n.CONDITION_LABELS["ro"])


def test_food_display_name_uses_english_name_with_fallback():
    f = food("spinach_raw")
    assert food_display_name(f, "en") == "Raw spinach"
    assert food_display_name(food("spinach_raw", name_en=None), "en") == "Spanac crud"
    assert food_display_name(f, "ro") == "Spanac crud"


# ---------- persistență ----------

def test_facts_roundtrip_through_db_fields_and_render_in_requested_language():
    facts = _facts(_user(), _lab(ferritin=12.0))
    assert facts["trace"]["components"] and facts["trace"]["score"] > 0  # scorul e urmăribil până la cifre
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
