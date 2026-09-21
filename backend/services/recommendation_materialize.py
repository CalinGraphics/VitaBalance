"""
Materializare recomandări (motor + persistare) — apelabil din HTTP sau BackgroundTasks.

Explicațiile se salvează ca FAPTE structurate (explanation_json.facts) și se randează la citire în limba cerută
(RO/EN) — vezi explanation_facts.py / explanation_renderer.py.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, Iterable, List, Optional

from fastapi import HTTPException

from domain.models import UserProfile, food_display_name
from repositories import (
    UserRepository,
    FoodRepository,
    LabResultRepository,
    RecommendationRepository,
    FeedbackRepository,
)
from domain.models import FoodItem, RecommendationItem
from services.deficit_calculator import DeficitCalculator
from services.explanation_facts import alternatives_for, build_facts, has_facts, parse_explanation_json
from services.explanation_i18n import DEFAULT_LANG, normalize_lang
from services.explanation_renderer import render_explanation
from services.explanation_storage import explanation_from_db_row, explanation_to_db_fields
from services.portion_calculator import suggest_portion
from services.recommender import RecommenderService
from services.recommendation_fast_context import enter_fast_bulk_mode, exit_fast_bulk_mode

ACTIVE_REC_LIMIT = 20
FEEDBACK_REC_LOOKUP_LIMIT = 25


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


def _build_feedback_by_food(user_feedbacks) -> dict:
    """Feedback-ul e legat direct de aliment, deci rămâne valabil după regenerarea/înlocuirea recomandărilor."""
    feedback_by_food: dict = {}
    for fb in user_feedbacks:
        feedback_by_food.setdefault(fb.food_id, []).append(fb)
    return feedback_by_food


def _rating_by_food(user_feedbacks) -> Dict[int, int]:
    return {fb.food_id: fb.rating for fb in user_feedbacks}


def kcal_per_100g_for_display(food: FoodItem) -> Optional[float]:
    """
    kcal / 100 g pentru afișarea informativă a obiectivului caloric (NU intră în scorare).

    Catalogul conține și preparate ("Mese/...": ex. Gyros, Burrito) cu valori per porție, nu per 100 g:
    macronutrienții lor însumează > 100 g la 100 g, ceea ce e imposibil. Pentru ele returnăm None,
    ca estimarea porției să nu fie umflată artificial.
    """
    kcal = float(getattr(food, "calories", 0) or 0)
    if kcal <= 0:
        return None
    macros = (
        float(getattr(food, "protein", 0) or 0)
        + float(getattr(food, "fat", 0) or 0)
        + float(getattr(food, "carbs", 0) or 0)
    )
    if macros > 100.5:
        return None
    return kcal


def _explanation_for_api(
    rec: RecommendationItem, food: FoodItem, food_by_id: Dict[int, FoodItem], lang: str
) -> dict:
    """Explicația în limba cerută: randată din fapte; rândurile vechi (fără fapte) rămân în textul salvat (RO)."""

    def name_of(fid: int) -> Optional[str]:
        other = food_by_id.get(fid)
        return food_display_name(other, lang) if other else None

    return explanation_from_db_row(
        {
            "explanation": rec.explanation,
            "portion_suggested": rec.portion_suggested,
            "explanation_json": rec.explanation_json,
            "reasons": rec.reasons,
            "tips": rec.tips,
        },
        fallback_text=rec.explanation or "",
        fallback_portion=float(rec.portion_suggested or 0),
        lang=lang,
        food_name=food_display_name(food, lang),
        name_of=name_of,
    )


def _api_item_from_rec(
    rec: RecommendationItem,
    food: FoodItem,
    food_by_id: Dict[int, FoodItem],
    feedback_counts: Dict[int, Dict[str, int]],
    user_rating_by_food: Dict[int, int],
    lang: str = DEFAULT_LANG,
) -> dict:
    counts = feedback_counts.get(rec.food_id, {"likes": 0, "dislikes": 0})
    return {
        "food_id": food.id,
        "food": {
            "id": food.id,
            "name": food_display_name(food, lang),
            "category": food.category,
            # kcal / 100 g — folosit doar pentru afișarea informativă față de obiectivul caloric
            "calories": kcal_per_100g_for_display(food),
        },
        "score": rec.score,
        "coverage": rec.coverage_percentage or 0,
        "explanation": _explanation_for_api(rec, food, food_by_id, lang),
        "recommendation_id": rec.id,
        "feedback": counts,
        "my_rating": user_rating_by_food.get(rec.food_id),
    }


def _facts_nutrient_keys(explanation_json) -> List[str]:
    facts = (parse_explanation_json(explanation_json) or {}).get("facts") or {}
    return [n["key"] for n in facts.get("nutrients") or [] if n.get("key")]


def _prepare_insert_rows(
    *,
    user: UserProfile,
    lab_results,
    deficits: Dict[str, float],
    has_lab_data: bool,
    rec_list: List[dict],
    food_by_id: Dict[int, FoodItem],
    context_recs: Iterable[RecommendationItem] = (),
) -> List[dict]:
    """
    Rânduri pentru `recommendations`: fapte structurate + explicația RO derivată din ele (compatibilitate cu
    coloanele explanation/reasons/tips). `context_recs` = recomandări deja existente, folosite doar pentru alternative.
    """
    entries = []
    for rec in rec_list[:ACTIVE_REC_LIMIT]:
        food = food_by_id.get(rec["food_id"])
        if not food:
            continue
        facts = build_facts(
            food=food,
            user=user,
            lab_results=lab_results,
            deficits=deficits,
            rec=rec,
            portion=suggest_portion(food, user),
            has_lab_data=has_lab_data,
        )
        entries.append((food, rec, facts))

    nutrients_by_food = {c.food_id: _facts_nutrient_keys(c.explanation_json) for c in context_recs}
    nutrients_by_food.update({f.id: [n["key"] for n in facts["nutrients"]] for f, _, facts in entries})
    pool = [{"food_id": f.id} for f, _, _ in entries] + [{"food_id": fid} for fid in nutrients_by_food if fid not in {f.id for f, _, _ in entries}]
    alts = alternatives_for(pool, nutrients_by_food)

    rows: List[dict] = []
    for food, rec, facts in entries:
        facts["alternatives"] = alts.get(food.id, [])
        expl = render_explanation(
            facts,
            food_name=food.name,
            lang=DEFAULT_LANG,
            name_of=lambda fid: food_by_id[fid].name if fid in food_by_id else None,
        )
        expl["facts"] = facts
        row = {
            "user_id": user.id,
            "food_id": food.id,
            "score": rec["score"],
            "coverage_percentage": rec["coverage"],
        }
        row.update(explanation_to_db_fields(expl))
        rows.append(row)
    return rows


def list_stored_recommendations_fast(
    user_id: int, _user_verified: bool = False, lang: str = DEFAULT_LANG
) -> List[dict]:
    """
    Citire rapidă din DB — fără recalcularea recomandărilor (țintă < 800ms); explicația se randează din faptele
    salvate, în limba cerută.

    Parametru _user_verified=True: sare verificarea existenței utilizatorului
    (apelat din endpoint-uri cu autentificare deja validată).
    """
    lang = normalize_lang(lang)
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
    user_rating_by_food = _rating_by_food(user_feedbacks)

    recommendations: List[dict] = []
    for rec in existing_recs[:ACTIVE_REC_LIMIT]:
        food = food_by_id.get(rec.food_id)
        if not food:
            continue
        recommendations.append(_api_item_from_rec(rec, food, food_by_id, {}, user_rating_by_food, lang))

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
    lang: str = DEFAULT_LANG,
) -> List[dict]:
    lang = normalize_lang(lang)
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
    user_rating_by_food = _rating_by_food(user_feedbacks)

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
        # Recomandările create înainte de explicațiile pe bază de fapte se regenerează o singură dată,
        # ca să poată fi randate specific pacientului și în ambele limbi.
        if any(not has_facts(r.explanation_json) for r in existing_recs_for_user):
            should_generate = True

    exclude_ids = set(exclude_food_ids or [])
    is_replace_only = False
    if replace_recommendation_id:
        rec_to_replace = next(
            (r for r in existing_recs_for_user if r.id == replace_recommendation_id),
            None,
        )
        if rec_to_replace:
            exclude_ids.add(rec_to_replace.food_id)
            rec_repo.delete_by_id(replace_recommendation_id)
            is_replace_only = True

    feedback_by_food = _build_feedback_by_food(user_feedbacks)

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
        inserted_recs: List = []
        remaining_recs = [r for r in existing_recs_for_user if r.id != replace_recommendation_id]
        if rec_list:
            rows = _prepare_insert_rows(
                user=user,
                lab_results=lab_results,
                deficits=deficits,
                has_lab_data=has_lab_data,
                rec_list=rec_list[:1],
                food_by_id=food_by_id,
                context_recs=remaining_recs,
            )
            if rows:
                inserted_recs = rec_repo.insert_many(rows)

        # Reconstruiește lista din memorie — elimină query extra get_by_user_id
        updated_recs = list(remaining_recs)
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
            recommendations.append(
                _api_item_from_rec(rec, food, food_by_id, feedback_counts_by_food, user_rating_by_food, lang)
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
            to_insert = _prepare_insert_rows(
                user=user,
                lab_results=lab_results,
                deficits=deficits,
                has_lab_data=has_lab_data,
                rec_list=rec_list,
                food_by_id=food_by_id,
            )
            if to_insert:
                if existing is not None and not is_replace_only:
                    rec_repo.delete_by_user_id(user_id)
                inserted = rec_repo.insert_many(to_insert)
                for rec in inserted:
                    food = food_by_id.get(rec.food_id)
                    if not food:
                        continue
                    recommendations.append(
                        _api_item_from_rec(
                            rec, food, food_by_id, feedback_counts_by_food, user_rating_by_food, lang
                        )
                    )
        finally:
            exit_fast_bulk_mode(fast_token)
    else:
        for rec in existing_recs_for_user[:ACTIVE_REC_LIMIT]:
            food = food_by_id.get(rec.food_id)
            if not food:
                continue
            recommendations.append(
                _api_item_from_rec(rec, food, food_by_id, feedback_counts_by_food, user_rating_by_food, lang)
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
            to_insert = _prepare_insert_rows(
                user=user,
                lab_results=lab_results,
                deficits={},
                has_lab_data=has_lab_data,
                rec_list=rec_list,
                food_by_id=food_by_id,
            )
            inserted = rec_repo.insert_many(to_insert)
            for rec in inserted:
                food = food_by_id.get(rec.food_id)
                if not food:
                    continue
                recommendations.append(
                    _api_item_from_rec(
                        rec, food, food_by_id, feedback_counts_by_food, user_rating_by_food, lang
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
