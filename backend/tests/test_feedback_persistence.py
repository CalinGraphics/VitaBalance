"""Feedback persistent per (user, aliment): supraviețuiește regenerării/înlocuirii recomandărilor."""
import pytest

from domain.models import FoodItem, RecommendationItem
from repositories.feedback_repository import FeedbackRepository
from services.recommendation_materialize import (
    _api_item_from_rec,
    _build_feedback_by_food,
    _rating_by_food,
)


class _Resp:
    def __init__(self, data):
        self.data = data


class _Query:
    """Imită lanțul supabase-py (select/eq/limit/upsert/execute) peste tabele în memorie."""

    def __init__(self, tables, name):
        self._tables = tables
        self._name = name
        self._filters = []
        self._upsert_row = None
        self._on_conflict = None
        self._limit = None

    def select(self, *_args):
        return self

    def eq(self, col, val):
        self._filters.append((col, val))
        return self

    def limit(self, n):
        self._limit = n
        return self

    def upsert(self, row, on_conflict=None):
        self._upsert_row = row
        self._on_conflict = on_conflict
        return self

    def execute(self):
        rows = self._tables[self._name]
        if self._upsert_row is not None:
            keys = [k.strip() for k in (self._on_conflict or "id").split(",")]
            for r in rows:
                if all(r.get(k) == self._upsert_row.get(k) for k in keys):
                    r.update(self._upsert_row)
                    return _Resp([dict(r)])
            new = {"id": len(rows) + 1, **self._upsert_row}
            rows.append(new)
            return _Resp([dict(new)])
        out = [dict(r) for r in rows if all(r.get(c) == v for c, v in self._filters)]
        return _Resp(out[: self._limit] if self._limit else out)


class _FakeClient:
    def __init__(self, recommendations=None):
        self.tables = {"feedback": [], "recommendations": list(recommendations or [])}

    def table(self, name):
        return _Query(self.tables, name)


def _repo(recommendations):
    client = _FakeClient(recommendations)
    return FeedbackRepository(client=client), client


def test_feedback_takes_food_from_owned_recommendation():
    repo, client = _repo([{"id": 10, "user_id": 1, "food_id": 5}])
    fb = repo.upsert(1, 10, -1)
    assert (fb.food_id, fb.recommendation_id, fb.rating) == (5, 10, -1)
    assert len(client.tables["feedback"]) == 1


def test_same_food_new_recommendation_updates_the_single_row():
    # După regenerare, alimentul revine cu alt recommendation_id: rămâne UN singur vot pentru aliment.
    repo, client = _repo([{"id": 10, "user_id": 1, "food_id": 5}, {"id": 11, "user_id": 1, "food_id": 5}])
    repo.upsert(1, 10, -1)
    fb = repo.upsert(1, 11, 5)
    assert len(client.tables["feedback"]) == 1
    assert (fb.food_id, fb.recommendation_id, fb.rating) == (5, 11, 5)


def test_feedback_without_recommendation_link_is_kept_by_food():
    # Recomandarea a fost ștearsă (înlocuire): DB face recommendation_id NULL, votul rămâne valabil pe aliment.
    repo, client = _repo([{"id": 10, "user_id": 1, "food_id": 5}])
    repo.upsert(1, 10, -1)
    client.tables["recommendations"].clear()
    client.tables["feedback"][0]["recommendation_id"] = None  # ON DELETE SET NULL

    feedbacks = repo.get_by_user_id(1)
    assert len(feedbacks) == 1 and feedbacks[0].recommendation_id is None
    assert _rating_by_food(feedbacks) == {5: -1}
    assert set(_build_feedback_by_food(feedbacks)) == {5}


def test_deleted_recommendation_falls_back_to_given_food_id():
    repo, _ = _repo([])
    fb = repo.upsert(1, 999, 1, food_id=7)
    assert (fb.food_id, fb.recommendation_id) == (7, None)


def test_deleted_recommendation_without_food_id_is_rejected():
    repo, client = _repo([])
    with pytest.raises(ValueError):
        repo.upsert(1, 999, 1)
    assert client.tables["feedback"] == []


def test_other_users_recommendation_is_not_linked():
    repo, _ = _repo([{"id": 10, "user_id": 2, "food_id": 5}])
    fb = repo.upsert(1, 10, 4, food_id=8)
    assert (fb.food_id, fb.recommendation_id) == (8, None)


def test_my_rating_follows_the_food_not_the_recommendation_id():
    # Aceeași aliment cu recommendation_id nou (după regenerare) își păstrează votul.
    food = FoodItem(id=5, name="Spanac", category="Legume")
    new_rec = RecommendationItem(id=99, user_id=1, food_id=5, score=1.0, explanation="", portion_suggested=100)
    item = _api_item_from_rec(new_rec, food, {}, {}, {5: -1})
    assert item["my_rating"] == -1
    assert item["recommendation_id"] == 99
