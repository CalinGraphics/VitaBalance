"""
Exportă răspunsuri API reale (motorul real, catalogul real) pentru testele frontend ale mesajelor.

    python scripts/export_frontend_fixtures.py

Scrie frontend/src/features/recommendations/explanations/__fixtures__/patients.json: pentru fiecare pacient-tip
din tests/golden, primele recomandări exact în forma trimisă de GET /api/recommendations/stored.
Regenerează fișierul când se schimbă motorul sau catalogul (testele snapshot vor arăta diferența).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from domain.models import LabResultItem, RecommendationItem, UserProfile  # noqa: E402
from services.recommendations.materialize import _api_item_from_rec, _insert_rows  # noqa: E402
from services.recommendations.recommender import RecommenderService  # noqa: E402
from tests.catalog_fixture import all_foods  # noqa: E402
from tests.golden.patients import PATIENTS  # noqa: E402

OUT = BACKEND.parent / "frontend" / "src" / "features" / "recommendations" / "explanations" / "__fixtures__" / "patients.json"
TOP = 5


def export() -> dict:
    foods = all_foods()
    by_id = {f.id: f for f in foods}
    out = {}
    for p in PATIENTS:
        user = UserProfile(**p["user"])
        labs = LabResultItem(id=1, user_id=user.id, **p["labs"]) if p["labs"] is not None else None
        ranking = RecommenderService().rank(user, foods, labs)
        rows = _insert_rows(user, ranking, ranking.items[:TOP], has_lab_data=labs is not None)
        items = []
        for i, row in enumerate(rows, 1):
            rec = RecommendationItem(id=i, user_id=user.id, food_id=row["food_id"], score=row["score"],
                                     explanation="", portion_suggested=row["portion_suggested"],
                                     coverage_percentage=row["coverage_percentage"],
                                     explanation_json=row["explanation_json"])
            item = _api_item_from_rec(rec, by_id[row["food_id"]], by_id, {}, {})
            item["facts"].pop("trace", None)  # urma scorului nu e folosită de text și ar face fixture-ul uriaș
            items.append(item)
        out[p["id"]] = items
    return out


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(export(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"scris {OUT}")
