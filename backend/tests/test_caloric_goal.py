"""Obiectivul caloric este opțional, validat și doar informativ (nu intră în UserProfile-ul folosit la scorare)."""
import pytest
from pydantic import ValidationError

from domain.models import row_to_user
from schemas import UserCreate

BASE = {
    "email": "a@test.com",
    "name": "A",
    "age": 30,
    "sex": "F",
    "weight": 60,
    "height": 165,
    "activity_level": "moderate",
    "diet_type": "omnivore",
}


def test_caloric_goal_is_optional():
    assert UserCreate(**BASE).caloric_goal is None


@pytest.mark.parametrize("value", [500, 2000, 10000])
def test_caloric_goal_accepts_valid_range(value):
    assert UserCreate(**BASE, caloric_goal=value).caloric_goal == value


@pytest.mark.parametrize("value", [0, 499, 10001, -5])
def test_caloric_goal_rejects_out_of_range(value):
    with pytest.raises(ValidationError):
        UserCreate(**BASE, caloric_goal=value)


def test_row_to_user_maps_caloric_goal():
    row = {"id": 1, **BASE, "caloric_goal": "2100"}
    assert row_to_user(row).caloric_goal == 2100.0


@pytest.mark.parametrize("raw", [None, 0, "", "abc"])
def test_row_to_user_treats_missing_goal_as_none(raw):
    row = {"id": 1, **BASE, "caloric_goal": raw}
    assert row_to_user(row).caloric_goal is None
    row.pop("caloric_goal")
    assert row_to_user(row).caloric_goal is None
