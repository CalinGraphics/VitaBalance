#!/usr/bin/env python3
"""
Populează explanation_json, reasons și tips pentru recomandări existente (one-shot).

Utilizare (din rădăcina repo):
  python scripts/backfill_recommendations.py
  python scripts/backfill_recommendations.py --limit 100
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from repositories import (  # noqa: E402
    UserRepository,
    FoodRepository,
    LabResultRepository,
    RecommendationRepository,
)
from services.deficit_calculator import DeficitCalculator  # noqa: E402
from services.explanation_generator import ExplanationGenerator  # noqa: E402
from services.explanation_storage import explanation_to_db_fields  # noqa: E402
from services.recommendation_materialize import _has_lab_data  # noqa: E402


def backfill(limit: int) -> int:
    rec_repo = RecommendationRepository()
    user_repo = UserRepository()
    food_repo = FoodRepository()
    lab_repo = LabResultRepository()

    foods = food_repo.get_all()
    food_by_id = {f.id: f for f in foods}
    pending = rec_repo.list_needing_explanation_backfill(limit=limit)
    if not pending:
        print("Nicio recomandare de backfill (explanation_json deja populat).")
        return 0

    gen = ExplanationGenerator()
    updated = 0
    for rec in pending:
        user = user_repo.get_by_id(rec.user_id)
        food = food_by_id.get(rec.food_id)
        if not user or not food:
            continue
        lab_results = lab_repo.get_latest_by_user_id(rec.user_id)
        deficits = DeficitCalculator().calculate_deficits(user, lab_results)
        expl = gen.generate_explanation(
            food=food,
            user=user,
            deficits=deficits,
            score=rec.score,
            coverage=rec.coverage_percentage or 0,
            explanations=[rec.explanation] if rec.explanation else None,
            matched_rules=[],
            has_lab_data=_has_lab_data(lab_results),
        )
        fields = explanation_to_db_fields(expl)
        rec_repo.update_explanation_fields(rec.id, fields)
        updated += 1
        print(f"  OK rec_id={rec.id} user_id={rec.user_id} food_id={rec.food_id}")

    print(f"Backfill finalizat: {updated}/{len(pending)} rânduri actualizate.")
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill explanation_json pe recommendations")
    parser.add_argument("--limit", type=int, default=500, help="Max rânduri per rulare")
    args = parser.parse_args()
    backfill(limit=args.limit)


if __name__ == "__main__":
    main()
