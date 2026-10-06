"""Mifflin-St Jeor, consumul zilnic și avertismentul pentru obiectivul caloric (care nu blochează salvarea)."""
import pytest

from domain.models import UserProfile
from services.nutrition.energy import caloric_goal_warning, energy_estimate, mifflin_st_jeor


def _user(**kw):
    base = dict(id=1, email="a@b.c", name="A", age=34, sex="M", weight=79, height=182,
                activity_level="moderate", diet_type="omnivore")
    base.update(kw)
    return UserProfile(**base)


def test_mifflin_st_jeor():
    assert mifflin_st_jeor("M", 79, 182, 34) == pytest.approx(1762.5)
    assert mifflin_st_jeor("F", 60, 165, 28) == pytest.approx(1330.25)


def test_energy_estimate_uses_activity_factor():
    est = energy_estimate(_user())
    assert est == {"bmr": 1762, "tdee": 2732, "activity_factor": 1.55}
    assert energy_estimate(_user(weight=0)) is None


def test_1200_kcal_for_79kg_man_is_below_bmr():
    w = caloric_goal_warning(_user(caloric_goal=1200))
    assert w["code"] == "below_bmr" and w["bmr"] == 1762 and w["tdee"] == 2732 and w["deviation_pct"] == -56


def test_athlete_goal_far_below_tdee():
    # foarte activ: TDEE ~ 3350; 1900 kcal e peste BMR, dar cu peste 40% sub consum
    w = caloric_goal_warning(_user(activity_level="very_active", caloric_goal=1900))
    assert w["code"] == "far_from_tdee" and w["deviation_pct"] < -40


def test_reasonable_or_missing_goal_has_no_warning():
    assert caloric_goal_warning(_user(caloric_goal=2500)) is None
    assert caloric_goal_warning(_user(caloric_goal=None)) is None


def test_warning_does_not_block_profile_save():
    from domain.schemas import UserCreate
    UserCreate(email="a@b.co", name="A", age=34, sex="M", weight=79, height=182, activity_level="moderate",
               diet_type="omnivore", caloric_goal=1200)
