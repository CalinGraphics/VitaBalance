"""Necesarul de referință EFSA, pragurile de laborator pe sexe, severitatea și sursa deficitului."""
import pytest

from data.lab_ranges import LAB_RANGES, MILD, MODERATE, SEVERE, severity_for
from data.reference_values import SOURCES, UNITS, reference_intake
from domain.models import LabResultItem, UserProfile
from services.nutrition.needs import NUTRIENTS, detect_needs


def _user(**kw):
    base = dict(id=1, email="a@b.c", name="A", age=34, sex="M", weight=79, height=182,
                activity_level="moderate", diet_type="omnivore", allergies="", medical_conditions="")
    base.update(kw)
    return UserProfile(**base)


def _lab(**kw):
    return LabResultItem(id=1, user_id=1, **kw)


# ---------- EFSA ----------

def test_every_nutrient_has_unit_source_and_value():
    for n in NUTRIENTS:
        assert n in UNITS and n in SOURCES
        assert reference_intake(n, sex="F", age=30, weight_kg=60) > 0


@pytest.mark.parametrize("nutrient, sex, age, expected", [
    ("iron", "M", 30, 11.0), ("iron", "F", 30, 16.0), ("iron", "F", 60, 11.0),
    ("calcium", "F", 20, 1000.0), ("calcium", "M", 40, 950.0),
    ("vitamin_d", "M", 40, 15.0),                    # µg, nu UI
    ("vitamin_b12", "F", 30, 4.0),
    ("magnesium", "M", 40, 350.0), ("magnesium", "F", 40, 300.0),
    ("folate", "M", 40, 330.0),
    ("vitamin_a", "M", 40, 750.0), ("vitamin_a", "F", 40, 650.0),
    ("vitamin_c", "M", 40, 110.0), ("vitamin_c", "F", 40, 95.0),
    ("iodine", "F", 40, 150.0), ("vitamin_k", "M", 40, 70.0), ("potassium", "M", 40, 3500.0),
])
def test_efsa_values(nutrient, sex, age, expected):
    assert reference_intake(nutrient, sex=sex, age=age, weight_kg=70) == expected


def test_life_stage_values():
    assert reference_intake("folate", sex="F", age=30, pregnant=True) == 600.0
    assert reference_intake("vitamin_b12", sex="F", age=30, lactating=True) == 5.0
    assert reference_intake("iodine", sex="F", age=30, pregnant=True) == 200.0
    assert reference_intake("protein", sex="M", age=30, weight_kg=80) == pytest.approx(66.4)
    assert reference_intake("protein", sex="F", age=30, weight_kg=60, pregnant=True) == pytest.approx(58.8)
    assert reference_intake("folate", sex="M", age=30, pregnant=True) == 330.0  # sarcina nu se aplică la „M”


# ---------- praguri și severitate ----------

def test_sex_specific_hemoglobin_threshold():
    hb = LAB_RANGES["hemoglobin"]
    assert hb.low("M") == 13.0 and hb.low("F") == 12.0 and hb.low("F", pregnant=True) == 11.0
    assert severity_for(hb, 12.5, "F") is None
    assert severity_for(hb, 12.5, "M") == MILD
    assert severity_for(hb, 9.0, "M") == MODERATE
    assert severity_for(hb, 7.5, "F") == SEVERE


def test_vitamin_d_bands():
    vd = LAB_RANGES["vitamin_d"]
    assert severity_for(vd, 30, "M") is None
    assert severity_for(vd, 25, "M") == MILD
    assert severity_for(vd, 18, "M") == MODERATE
    assert severity_for(vd, 8, "M") == SEVERE


def test_generic_severity_by_distance_below_minimum():
    mg = LAB_RANGES["magnesium"]  # limita 1,7 mg/dL
    assert severity_for(mg, 1.6, "M") == MILD       # 6% sub
    assert severity_for(mg, 1.45, "M") == MODERATE  # 15% sub
    assert severity_for(mg, 1.2, "M") == SEVERE     # 29% sub


# ---------- sursa deficitului ----------

def test_deficit_only_from_labs_or_explicit_statement():
    assert detect_needs(_user(), None).needs == []                             # fără analize, fără text
    assert detect_needs(_user(medical_conditions="iau vitamina D zilnic"), None).needs == []
    assert detect_needs(_user(medical_conditions="nu am deficit de fier"), None).needs == []
    notes = detect_needs(_user(medical_conditions="Deficiență de magneziu"), None).needs
    assert [(n.nutrient, n.source) for n in notes] == [("magnesium", "notes")]


def test_profile_codes_are_explicit_statements():
    needs = detect_needs(_user(medical_conditions="deficienta_vitamin_d, deficienta_b12"), None).needs
    assert {(n.nutrient, n.source) for n in needs} == {("vitamin_d", "notes"), ("vitamin_b12", "notes")}


def test_lab_source_wins_and_normal_lab_overrides_notes():
    res = detect_needs(_user(medical_conditions="Deficiență de magneziu"), _lab(magnesium=1.5, vitamin_d=40))
    mg = res.by_nutrient()["magnesium"]
    assert (mg.source, mg.marker, mg.value, mg.threshold, mg.unit) == ("lab", "magnesium", 1.5, 1.7, "mg/dL")
    normal = detect_needs(_user(medical_conditions="Deficiență de magneziu"), _lab(magnesium=2.0))
    assert normal.needs == []


def test_golden_patient_1_needs():
    res = detect_needs(_user(), _lab(vitamin_d=18, magnesium=1.6))
    assert [(n.nutrient, n.severity) for n in res.needs] == [("vitamin_d", MODERATE), ("magnesium", MILD)]
    assert res.by_nutrient()["vitamin_d"].daily_reference == 15.0


def test_ferritin_preferred_over_hemoglobin():
    res = detect_needs(_user(sex="F", age=28), _lab(ferritin=9, hemoglobin=13.5))
    assert res.by_nutrient()["iron"].marker == "ferritin"
    ok = detect_needs(_user(sex="F", age=28), _lab(ferritin=40, hemoglobin=11.0))
    assert "iron" not in ok.by_nutrient()  # feritina normală decide


def test_hemochromatosis_cancels_iron_need_and_high_potassium_becomes_a_limit():
    res = detect_needs(_user(medical_conditions="hemocromatoza"), _lab(ferritin=5))
    assert "iron" not in res.by_nutrient()
    k = detect_needs(_user(), _lab(potassium=5.8))
    assert k.limits == {"potassium": "lab_high"} and k.context.hyperkalemia
