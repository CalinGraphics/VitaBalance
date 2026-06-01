"""
Materializare recomandări (motor + persistare) — apelabil din HTTP sau BackgroundTasks.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import HTTPException

from domain.models import UserProfile
from repositories import (
    UserRepository,
    FoodRepository,
    LabResultRepository,
    RecommendationRepository,
    FeedbackRepository,
)
from domain.models import FoodItem, RecommendationItem
from services.deficit_calculator import DeficitCalculator
from services.explanation_generator import ExplanationGenerator
from services.explanation_storage import explanation_from_db_row, explanation_to_db_fields
from services.portion_calculator import suggest_portion
from services.recommender import RecommenderService
from services.recommendation_fast_context import enter_fast_bulk_mode, exit_fast_bulk_mode

ACTIVE_REC_LIMIT = 20
FEEDBACK_REC_LOOKUP_LIMIT = 25


def _build_explanation_for_insert(
    food: FoodItem,
    user: UserProfile,
    rec_dict: dict,
    has_lab_data: bool,
    *,
    fast: bool,
) -> dict:
    ps = suggest_portion(food, user)
    if fast:
        texts = rec_dict.get("explanations") or []
        main = ""
        if texts:
            main = str(texts[0]).strip()
            if len(texts) > 1:
                main = ". ".join(str(t).strip() for t in texts[:2] if str(t).strip())
        if not main:
            main = f"Recomandat pentru profilul tău: {food.name}."
        reasons = (
            ["Adaptat profilului și analizelor tale."]
            if has_lab_data
            else ["Adaptat profilului tău."]
        )
        return {
            "text": main[:1200],
            "portion": ps.amount,
            "portion_unit": ps.unit,
            "reasons": reasons,
            "tips": ["Folosește porția sugerată în mesele zilnice."],
            "alternatives": None,
        }
    explanation_gen = ExplanationGenerator()
    explanation = explanation_gen.generate_explanation(
        food=food,
        user=user,
        deficits={},
        score=rec_dict["score"],
        coverage=rec_dict["coverage"],
        explanations=rec_dict.get("explanations"),
        matched_rules=rec_dict.get("matched_rules"),
        has_lab_data=has_lab_data,
        nutrients_covered=rec_dict.get("nutrients_covered"),
        portion_grams=ps.grams_equivalent,
    )
    explanation["portion"] = ps.amount
    explanation["portion_unit"] = ps.unit
    return explanation


def _has_lab_data(lab_results) -> bool:
    if lab_results is None:
        return False
    for key in [
        "hemoglobin", "ferritin", "calcium", "vitamin_d", "vitamin_b12", "magnesium",
        "protein", "zinc", "folate", "vitamin_a", "vitamin_c", "iodine", "vitamin_k", "potassium",
    ]:
        if getattr(lab_results, key, None) is not None:
            return True
    return False


def _build_feedback_by_food(
    user_feedbacks,
    active_recs: List[RecommendationItem],
    feedback_food_by_rec_id: Dict[int, int],
) -> dict:
    feedback_by_food: dict = {}
    rec_by_id = {r.id: r for r in active_recs}
    for fb in user_feedbacks:
        if fb.recommendation_id is None:
            continue
        fid = getattr(fb, "food_id", None)
        if fid is None:
            rec = rec_by_id.get(fb.recommendation_id)
            fid = rec.food_id if rec else feedback_food_by_rec_id.get(fb.recommendation_id)
        if fid is None:
            continue
        if fid not in feedback_by_food:
            feedback_by_food[fid] = []
        feedback_by_food[fid].append(fb)
    return feedback_by_food


def _api_item_from_rec(
    rec: RecommendationItem,
    food: FoodItem,
    expl: dict,
    feedback_counts: Dict[int, Dict[str, int]],
    user_feedback_by_rec: Dict[int, int],
) -> dict:
    counts = feedback_counts.get(rec.food_id, {"likes": 0, "dislikes": 0})
    return {
        "food_id": food.id,
        "food": {"id": food.id, "name": food.name, "category": food.category},
        "score": rec.score,
        "coverage": rec.coverage_percentage or 0,
        "explanation": expl,
        "recommendation_id": rec.id,
        "feedback": counts,
        "my_rating": user_feedback_by_rec.get(rec.id),
    }


def _insert_row_from_explanation(user_id: int, food_id: int, rec_dict: dict, expl: dict) -> dict:
    row = {
        "user_id": user_id,
        "food_id": food_id,
        "score": rec_dict["score"],
        "coverage_percentage": rec_dict["coverage"],
    }
    row.update(explanation_to_db_fields(expl))
    return row


def list_stored_recommendations_fast(user_id: int, _user_verified: bool = False) -> List[dict]:
    """
    Citire rapidă din DB — fără ExplanationGenerator (țintă < 800ms).

    Parametru _user_verified=True: sare verificarea existenței utilizatorului
    (apelat din endpoint-uri cu autentificare deja validată).
    """
    rec_repo = RecommendationRepository()
    feedback_repo = FeedbackRepository()
    food_repo = FoodRepository()

    if not _user_verified:
        user_repo = UserRepository()
        if not user_repo.get_by_id(user_id):
            return []

    # Paralelizare: recomandările și feedback-ul sunt independente
    with ThreadPoolExecutor(max_workers=2) as pool:
        fut_recs = pool.submit(rec_repo.get_by_user_id, user_id, ACTIVE_REC_LIMIT)
        fut_feedbacks = pool.submit(feedback_repo.get_by_user_id, user_id)
        existing_recs = fut_recs.result()
        user_feedbacks = fut_feedbacks.result()

    if not existing_recs:
        return []

    foods = food_repo.get_all()
    food_by_id = {f.id: f for f in foods}
    user_feedback_by_rec = {
        fb.recommendation_id: fb.rating
        for fb in user_feedbacks
        if fb.recommendation_id is not None
    }

    recommendations: List[dict] = []
    for rec in existing_recs[:ACTIVE_REC_LIMIT]:
        food = food_by_id.get(rec.food_id)
        if not food:
            continue
        row = {
            "explanation": rec.explanation,
            "portion_suggested": rec.portion_suggested,
            "explanation_json": rec.explanation_json,
            "reasons": rec.reasons,
            "tips": rec.tips,
        }
        expl = explanation_from_db_row(
            row,
            fallback_text=rec.explanation or "",
            fallback_portion=float(rec.portion_suggested or 0),
        )
        recommendations.append(
            _api_item_from_rec(rec, food, expl, {}, user_feedback_by_rec)
        )

    response_food_ids = [int(r["food_id"]) for r in recommendations if r.get("food_id") is not None]
    if response_food_ids:
        counts = feedback_repo.get_counts_by_food_ids(response_food_ids, user_id=user_id)
        for r in recommendations:
            fid = r.get("food_id")
            if fid is not None:
                r["feedback"] = counts.get(int(fid), {"likes": 0, "dislikes": 0})
    return recommendations


def _ensure_owner(owner_email: str, user_id: int) -> UserProfile:
    repo = UserRepository()
    profile = repo.get_by_email(owner_email)
    if not profile:
        raise HTTPException(status_code=404, detail="Profilul nu a fost găsit")
    if profile.id != user_id:
        raise HTTPException(status_code=403, detail="Nu ai acces la această resursă")
    return profile


def materialize_recommendations(
    user_id: int,
    owner_email: str,
    force_regenerate: bool = False,
    replace_recommendation_id: Optional[int] = None,
    exclude_food_ids: Optional[List[int]] = None,
) -> List[dict]:
    # _ensure_owner returnează UserProfile deja — nu mai re-cerem prin get_by_id
    user = _ensure_owner(owner_email, user_id)

    food_repo = FoodRepository()
    lab_repo = LabResultRepository()
    rec_repo = RecommendationRepository()
    feedback_repo = FeedbackRepository()

    foods = food_repo.get_all()
    if not foods:
        return []
    food_by_id = {f.id: f for f in foods}

    # Paralelizare: lab_results, feedbacks și recomandările curente sunt independente
    with ThreadPoolExecutor(max_workers=3) as pool:
        fut_labs = pool.submit(lab_repo.get_latest_by_user_id, user_id)
        fut_feedbacks = pool.submit(feedback_repo.get_by_user_id, user_id)
        fut_recs = pool.submit(rec_repo.get_by_user_id, user_id, FEEDBACK_REC_LOOKUP_LIMIT)
        lab_results = fut_labs.result()
        user_feedbacks = fut_feedbacks.result()
        all_user_recommendation_rows = fut_recs.result()

    feedback_counts_by_food: Dict[int, Dict[str, int]] = {}
    user_feedback_by_rec = {
        fb.recommendation_id: fb.rating for fb in user_feedbacks if fb.recommendation_id is not None
    }

    feedback_food_by_rec_id: Dict[int, int] = {}
    existing_recs_for_user = all_user_recommendation_rows[:ACTIVE_REC_LIMIT]

    # Cel mai recent rec după created_at — înlocuiește apelul redundant get_first_by_user_id
    existing = (
        max(
            all_user_recommendation_rows,
            key=lambda r: str(getattr(r, "created_at", None) or ""),
        )
        if all_user_recommendation_rows
        else None
    )
    should_generate = force_regenerate or (existing is None)

    def _to_dt(v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            s = v.replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(s)
            except Exception:
                return None
        return None

    if not force_regenerate and existing is not None:
        rec_dt = _to_dt(getattr(existing, "created_at", None))
        if lab_results is not None:
            lab_ca = _to_dt(getattr(lab_results, "created_at", None))
            lab_ua = _to_dt(getattr(lab_results, "updated_at", None))
            lab_dt = lab_ca
            if lab_ca is not None and lab_ua is not None:
                lab_dt = max(lab_ca, lab_ua)
            elif lab_ua is not None:
                lab_dt = lab_ua
            if lab_dt and (rec_dt is None or lab_dt > rec_dt):
                should_generate = True
        user_dt = _to_dt(getattr(user, "updated_at", None))
        if user_dt and (rec_dt is None or user_dt > rec_dt):
            should_generate = True

    exclude_ids = set(exclude_food_ids or [])
    is_replace_only = False
    if replace_recommendation_id:
        rec_to_replace = next(
            (r for r in existing_recs_for_user if r.id == replace_recommendation_id),
            None,
        )
        if rec_to_replace:
            feedback_food_by_rec_id[replace_recommendation_id] = rec_to_replace.food_id
            exclude_ids.add(rec_to_replace.food_id)
            rec_repo.delete_by_id(replace_recommendation_id)
            is_replace_only = True

    feedback_by_food = _build_feedback_by_food(
        user_feedbacks, existing_recs_for_user, feedback_food_by_rec_id
    )

    if is_replace_only:
        for r in existing_recs_for_user:
            exclude_ids.add(r.food_id)

    foods_filtered = [f for f in foods if f.id not in exclude_ids] if exclude_ids else foods

    calculator = DeficitCalculator()
    deficits = calculator.calculate_deficits(user, lab_results)
    has_lab_data = _has_lab_data(lab_results)

    recommendations: List[dict] = []
    if is_replace_only:
        recommender = RecommenderService()
        rec_list = recommender.generate_single_recommendation(
            user=user,
            deficits=deficits,
            foods=foods_filtered,
            lab_results=lab_results,
            user_feedbacks=user_feedbacks,
            feedback_by_food=feedback_by_food,
        )
        inserted_row_ids: Dict[int, dict] = {}
        inserted_recs: List = []
        if rec_list:
            food = next((f for f in foods_filtered if f.id == rec_list[0]["food_id"]), None)
            if food:
                # Cale rapidă — fără ExplanationGenerator complet (identică cu generate principal)
                expl = _build_explanation_for_insert(food, user, rec_list[0], has_lab_data, fast=True)
                inserted_recs = rec_repo.insert_many(
                    [_insert_row_from_explanation(user.id, food.id, rec_list[0], expl)]
                )
                for ins in inserted_recs:
                    inserted_row_ids[ins.id] = expl

        # Reconstruiește lista din memorie — elimină query extra get_by_user_id
        updated_recs = [r for r in existing_recs_for_user if r.id != replace_recommendation_id]
        updated_recs.extend(inserted_recs)
        updated_recs.sort(
            key=lambda r: (float(r.coverage_percentage or 0), float(r.score or 0)),
            reverse=True,
        )
        updated_recs = updated_recs[:ACTIVE_REC_LIMIT]

        fids_replace = [r.food_id for r in updated_recs]
        if fids_replace:
            feedback_counts_by_food = feedback_repo.get_counts_by_food_ids(
                fids_replace, user_id=user_id
            )
        for rec in updated_recs:
            food = food_by_id.get(rec.food_id)
            if not food:
                continue
            if rec.id in inserted_row_ids:
                expl = inserted_row_ids[rec.id]
            else:
                expl = explanation_from_db_row(
                    {
                        "explanation": rec.explanation,
                        "portion_suggested": rec.portion_suggested,
                        "explanation_json": rec.explanation_json,
                        "reasons": rec.reasons,
                        "tips": rec.tips,
                    },
                    fallback_text=rec.explanation or "",
                    fallback_portion=float(rec.portion_suggested or 0),
                )
            recommendations.append(
                _api_item_from_rec(rec, food, expl, feedback_counts_by_food, user_feedback_by_rec)
            )
    elif should_generate:
        fast_token = enter_fast_bulk_mode()
        try:
            recommender = RecommenderService()
            rec_list = recommender.generate_recommendations(
                user=user,
                deficits=deficits,
                foods=foods_filtered,
                lab_results=lab_results,
                user_feedbacks=user_feedbacks,
                feedback_by_food=feedback_by_food,
            )
            to_insert = []
            explanation_by_food_id: Dict[int, dict] = {}
            for rec in rec_list[:20]:
                food = food_by_id.get(rec["food_id"])
                if not food:
                    continue
                explanation = _build_explanation_for_insert(
                    food, user, rec, has_lab_data, fast=True
                )
                to_insert.append(_insert_row_from_explanation(user.id, food.id, rec, explanation))
                explanation_by_food_id[food.id] = explanation
            if to_insert:
                if existing is not None and not is_replace_only:
                    rec_repo.delete_by_user_id(user_id)
                inserted = rec_repo.insert_many(to_insert)
                for i, rec in enumerate(inserted):
                    if i >= len(rec_list):
                        break
                    food = food_by_id.get(rec.food_id)
                    if not food:
                        continue
                    expl = explanation_by_food_id.get(food.id)
                    if not expl:
                        continue
                    recommendations.append(
                        _api_item_from_rec(
                            rec, food, expl, feedback_counts_by_food, user_feedback_by_rec
                        )
                    )
        finally:
            exit_fast_bulk_mode(fast_token)
    else:
        existing_recs = existing_recs_for_user[:ACTIVE_REC_LIMIT]
        food_by_id = {f.id: f for f in foods}
        for rec in existing_recs:
            food = food_by_id.get(rec.food_id)
            if not food:
                continue
            expl = explanation_from_db_row(
                {
                    "explanation": rec.explanation,
                    "portion_suggested": rec.portion_suggested,
                    "explanation_json": rec.explanation_json,
                    "reasons": rec.reasons,
                    "tips": rec.tips,
                },
                fallback_text=rec.explanation or "",
                fallback_portion=float(rec.portion_suggested or 0),
            )
            recommendations.append(
                _api_item_from_rec(rec, food, expl, feedback_counts_by_food, user_feedback_by_rec)
            )

    if not recommendations and should_generate:
        fast_token = enter_fast_bulk_mode()
        try:
            recommender = RecommenderService()
            rec_list = recommender.generate_recommendations(
                user=user,
                deficits={},
                foods=foods,
                lab_results=lab_results,
                user_feedbacks=user_feedbacks,
                feedback_by_food=feedback_by_food,
            )
            if not rec_list:
                return []
            to_insert = []
            explanation_by_food_id: Dict[int, dict] = {}
            for rec in rec_list[:20]:
                food = food_by_id.get(rec["food_id"])
                if not food:
                    continue
                explanation = _build_explanation_for_insert(
                    food, user, rec, has_lab_data, fast=True
                )
                to_insert.append(_insert_row_from_explanation(user.id, food.id, rec, explanation))
                explanation_by_food_id[food.id] = explanation
            inserted = rec_repo.insert_many(to_insert)
            for i, rec in enumerate(inserted):
                if i >= len(rec_list):
                    break
                food = food_by_id.get(rec.food_id)
                if not food:
                    continue
                expl = explanation_by_food_id.get(food.id)
                if not expl:
                    continue
                recommendations.append(
                    _api_item_from_rec(
                        rec, food, expl, feedback_counts_by_food, user_feedback_by_rec
                    )
                )
        finally:
            exit_fast_bulk_mode(fast_token)

    unique_recommendations: List[dict] = []
    seen_food_ids: set[int] = set()
    for rec in recommendations:
        fid = rec.get("food_id")
        if fid is None:
            unique_recommendations.append(rec)
            continue
        if fid in seen_food_ids:
            continue
        seen_food_ids.add(fid)
        unique_recommendations.append(rec)

    response_food_ids = [int(rec["food_id"]) for rec in unique_recommendations if rec.get("food_id") is not None]
    if response_food_ids:
        feedback_counts_by_food = feedback_repo.get_counts_by_food_ids(
            response_food_ids, user_id=user_id
        )
        for rec in unique_recommendations:
            fid = rec.get("food_id")
            if fid is None:
                continue
            rec["feedback"] = feedback_counts_by_food.get(int(fid), {"likes": 0, "dislikes": 0})

    return unique_recommendations


