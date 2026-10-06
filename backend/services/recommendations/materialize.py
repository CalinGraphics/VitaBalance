"""
Materializare recomandări (motor + persistare) — apelabil din HTTP sau BackgroundTasks.

Explicațiile se salvează ca FAPTE structurate (explanation_json.facts, inclusiv urma scorului). Răspunsul API e
independent de limbă: fapte, numele în ambele limbi și id-uri; frontend-ul construiește textul, deci schimbarea
limbii nu cere nicio cerere la server.

Ordinea e una singură peste tot: scorul descrescător (motorul produce o listă descrescătoare, iar citirea din DB
sortează tot după scor), deci graficul și cardurile primesc exact aceeași listă.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import HTTPException

from domain.models import FoodItem, RecommendationItem, UserProfile
from repositories import (
    UserRepository,
    FoodRepository,
    LabResultRepository,
    RecommendationRepository,
    FeedbackRepository,
)
from services.explanations.facts import build_facts, has_facts
from services.explanations.storage import explanation_to_db_fields, facts_from_row, legacy_explanation
from services.recommendations.recommender import RecommenderService
from services.recommendations.scoring import MAX_RECOMMENDATIONS, Ranking, ScoredFood

ACTIVE_REC_LIMIT = MAX_RECOMMENDATIONS
LAB_KEYS = (
    "hemoglobin", "ferritin", "calcium", "vitamin_d", "vitamin_b12", "magnesium",
    "protein", "zinc", "folate", "vitamin_a", "vitamin_c", "iodine", "vitamin_k", "potassium",
)


def _has_lab_data(lab_results) -> bool:
    return lab_results is not None and any(getattr(lab_results, k, None) is not None for k in LAB_KEYS)


def _rating_by_food(user_feedbacks) -> Dict[int, int]:
    return {fb.food_id: fb.rating for fb in user_feedbacks}


def kcal_per_100g_for_display(food: FoodItem) -> Optional[float]:
    """
    kcal / 100 g pentru estimarea caloriilor porției. Doar pentru catalogul validat: valorile vechi amestecau
    porții cu 100 g (vezi docs/audit.md), deci pentru ele nu afișăm o estimare greșită.
    """
    if not food.validated or food.calories is None or food.calories < 0:
        return None
    return float(food.calories)


def _food_payload(food: FoodItem) -> dict:
    return {
        "id": food.id,
        "name_ro": food.name,
        "name_en": food.name_en or food.name,
        "category": food.category,
        "category_key": food.category_key,
        # kcal / 100 g — caloriile porției = calories × porție / 100 (vezi utils/calories.ts)
        "calories": kcal_per_100g_for_display(food),
    }


def _api_item_from_rec(
    rec: RecommendationItem,
    food: FoodItem,
    food_by_id: Dict[int, FoodItem],
    feedback_counts: Dict[int, Dict[str, int]],
    user_rating_by_food: Dict[int, int],
) -> dict:
    """Element de listă independent de limbă."""
    facts = facts_from_row(rec.explanation_json)
    alternatives = []
    for fid in (facts or {}).get("alternatives") or []:
        other = food_by_id.get(int(fid))
        if other is not None:
            alternatives.append({"id": other.id, "name_ro": other.name, "name_en": other.name_en or other.name})
    return {
        "food_id": food.id,
        "recommendation_id": rec.id,
        "food": _food_payload(food),
        "score": rec.score,
        # % din necesarul zilnic al nutrientului principal acoperit de porție — aceeași cifră în grafic și pe card
        "coverage": rec.coverage_percentage or 0,
        "facts": facts,
        "alternatives": alternatives,
        "legacy": None if facts else legacy_explanation(
            {"explanation": rec.explanation, "explanation_json": rec.explanation_json,
             "reasons": rec.reasons, "tips": rec.tips}),
        "feedback": feedback_counts.get(rec.food_id, {"likes": 0, "dislikes": 0}),
        "my_rating": user_rating_by_food.get(rec.food_id),
    }


def _insert_rows(user: UserProfile, ranking: Ranking, items: List[ScoredFood], has_lab_data: bool) -> List[dict]:
    """Rânduri pentru `recommendations`: doar fapte (textul se construiește în frontend)."""
    rows: List[dict] = []
    for item in items:
        row = {
            "user_id": user.id,
            "food_id": item.food.id,
            "score": round(item.score, 6),
            "coverage_percentage": item.coverage_pct,
        }
        row.update(explanation_to_db_fields(build_facts(item, ranking, has_lab_data=has_lab_data)))
        rows.append(row)
    return rows


def _sorted_recs(recs: List[RecommendationItem]) -> List[RecommendationItem]:
    return sorted(recs, key=lambda r: (-float(r.score or 0), r.id or 0))


def _api_list(recs, food_by_id, feedback_repo, user_id, user_rating_by_food) -> List[dict]:
    out: List[dict] = []
    seen: set[int] = set()
    for rec in _sorted_recs(recs)[:ACTIVE_REC_LIMIT]:
        food = food_by_id.get(rec.food_id)
        if not food or food.id in seen:
            continue
        seen.add(food.id)
        out.append(_api_item_from_rec(rec, food, food_by_id, {}, user_rating_by_food))
    ids = [r["food_id"] for r in out]
    if ids:
        counts = feedback_repo.get_counts_by_food_ids(ids, user_id=user_id)
        for r in out:
            r["feedback"] = counts.get(int(r["food_id"]), {"likes": 0, "dislikes": 0})
    return out


def list_stored_recommendations_fast(user_id: int, _user_verified: bool = False) -> List[dict]:
    """
    Citire rapidă din DB — fără recalcularea recomandărilor. `_user_verified=True` sare verificarea existenței
    utilizatorului (endpoint-uri deja autentificate).
    """
    rec_repo = RecommendationRepository()
    feedback_repo = FeedbackRepository()

    if not _user_verified and not UserRepository().get_by_id(user_id):
        return []

    with ThreadPoolExecutor(max_workers=2) as pool:
        fut_recs = pool.submit(rec_repo.get_by_user_id, user_id, ACTIVE_REC_LIMIT)
        fut_feedbacks = pool.submit(feedback_repo.get_by_user_id, user_id)
        existing_recs = fut_recs.result()
        user_feedbacks = fut_feedbacks.result()
    if not existing_recs:
        return []

    food_by_id = {f.id: f for f in FoodRepository().get_all()}
    return _api_list(existing_recs, food_by_id, feedback_repo, user_id, _rating_by_food(user_feedbacks))


def _ensure_owner(owner_email: str, user_id: int) -> UserProfile:
    profile = UserRepository().get_by_email(owner_email)
    if not profile:
        raise HTTPException(status_code=404, detail="Profilul nu a fost găsit")
    if profile.id != user_id:
        raise HTTPException(status_code=403, detail="Nu ai acces la această resursă")
    return profile


def _to_dt(v):
    if v is None or isinstance(v, datetime):
        return v
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _needs_regeneration(existing: List[RecommendationItem], user: UserProfile, lab_results) -> bool:
    """Recomandări lipsă, mai vechi decât profilul/analizele sau salvate într-un format de fapte vechi."""
    if not existing:
        return True
    if any(not has_facts(r.explanation_json) for r in existing):
        return True
    newest = max((_to_dt(r.created_at) for r in existing if _to_dt(r.created_at)), default=None)
    if newest is None:
        return True
    stamps = [_to_dt(getattr(user, "updated_at", None))]
    if lab_results is not None:
        stamps += [_to_dt(getattr(lab_results, "created_at", None)), _to_dt(getattr(lab_results, "updated_at", None))]
    return any(t is not None and t > newest for t in stamps)


def materialize_recommendations(
    user_id: int,
    owner_email: str,
    force_regenerate: bool = False,
    replace_recommendation_id: Optional[int] = None,
    exclude_food_ids: Optional[List[int]] = None,
) -> List[dict]:
    user = _ensure_owner(owner_email, user_id)

    rec_repo = RecommendationRepository()
    feedback_repo = FeedbackRepository()
    foods = FoodRepository().get_all()
    if not foods:
        return []
    food_by_id = {f.id: f for f in foods}

    with ThreadPoolExecutor(max_workers=3) as pool:
        fut_labs = pool.submit(LabResultRepository().get_latest_by_user_id, user_id)
        fut_feedbacks = pool.submit(feedback_repo.get_by_user_id, user_id)
        fut_recs = pool.submit(rec_repo.get_by_user_id, user_id, ACTIVE_REC_LIMIT)
        lab_results = fut_labs.result()
        user_feedbacks = fut_feedbacks.result()
        existing = fut_recs.result()

    has_lab_data = _has_lab_data(lab_results)
    rating_by_food = _rating_by_food(user_feedbacks)
    recommender = RecommenderService()
    exclude = set(exclude_food_ids or [])

    to_replace = next((r for r in existing if r.id == replace_recommendation_id), None) if replace_recommendation_id else None
    if to_replace is not None:
        # Înlocuire: următorul aliment din clasament care nu e deja în listă.
        remaining = [r for r in existing if r.id != to_replace.id]
        exclude |= {r.food_id for r in existing}
        ranking = recommender.rank(user, foods, lab_results, user_feedbacks, exclude_food_ids=exclude)
        rec_repo.delete_by_id(to_replace.id)
        inserted = rec_repo.insert_many(_insert_rows(user, ranking, ranking.items[:1], has_lab_data)) \
            if ranking.items else []
        return _api_list(remaining + inserted, food_by_id, feedback_repo, user_id, rating_by_food)

    if force_regenerate or exclude or _needs_regeneration(existing, user, lab_results):
        ranking = recommender.rank(user, foods, lab_results, user_feedbacks, exclude_food_ids=exclude)
        rows = _insert_rows(user, ranking, ranking.items, has_lab_data)
        if rows:
            if existing:
                rec_repo.delete_by_user_id(user_id)
            existing = rec_repo.insert_many(rows)
    return _api_list(existing, food_by_id, feedback_repo, user_id, rating_by_food)
