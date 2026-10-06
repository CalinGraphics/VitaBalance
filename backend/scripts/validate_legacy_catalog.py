"""
Raport de validare pentru catalogul vechi (`foods` cu validated = false). Doar citire.

    python scripts/validate_legacy_catalog.py > ../docs/catalog-validation.md

Verifică energia declarată față de macronutrienți (services/nutrition/food_validation.py) și marchează numele care
conțin o cantitate („(1 bucată)”), semn că valorile sunt per porție, nu la 100 g.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from repositories.supabase_client import get_supabase_client  # noqa: E402
from services.nutrition.food_validation import validate_per_100g  # noqa: E402

QTY = re.compile(r"\(\s*\d")


def main() -> None:
    rows = get_supabase_client().table("foods").select("*").execute().data or []
    legacy = [r for r in rows if not r.get("validated")]
    failing, per_portion = [], []
    for r in legacy:
        res = validate_per_100g(r)
        if not res.ok:
            failing.append((r, res))
        if QTY.search(r.get("name") or ""):
            per_portion.append(r)

    print("# Validarea catalogului vechi de alimente\n")
    print(f"Generat de `backend/scripts/validate_legacy_catalog.py`. Rânduri vechi: **{len(legacy)}**. "
          "Niciunul nu mai e recomandat (motorul folosește doar catalogul validat din USDA).\n")
    print(f"- În afara toleranței energetice (±15%) sau cu date lipsă: **{len(failing)}**")
    print(f"- Cu o cantitate în nume (valori probabil per porție, nu la 100 g): **{len(per_portion)}**\n")
    print("Verificarea energiei nu prinde valorile per porție: ele sunt consistente intern (vezi docs/audit.md §4.0).\n")
    print("## Rânduri în afara toleranței\n")
    print("| id | aliment | kcal declarat | kcal din macronutrienți | probleme |")
    print("|---|---|---|---|---|")
    for r, res in sorted(failing, key=lambda x: x[0]["id"]):
        calc = f"{res.atwater_kcal:.0f}" if res.atwater_kcal is not None else "—"
        print(f"| {r['id']} | {r.get('name')} | {r.get('calories')} | {calc} | {', '.join(res.issues)} |")


if __name__ == "__main__":
    main()
