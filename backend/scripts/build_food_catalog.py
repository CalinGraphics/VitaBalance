"""
Construiește catalogul validat de alimente din USDA FoodData Central (SR Legacy).

    python scripts/build_food_catalog.py --sr <dir cu food.csv, food_nutrient.csv>   # scrie data/foods_catalog.json
    python scripts/build_food_catalog.py --sql                                        # + migrations/011_seed_validated_foods.sql

Setul SR Legacy (aprilie 2018) se descarcă de la https://fdc.nal.usda.gov/download-datasets
(„SR Legacy”, CSV). Scriptul nu inventează nicio valoare: ce lipsește în USDA rămâne null.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from data.food_catalog_spec import CATEGORIES, FOODS  # noqa: E402
from data.iodine_values import IODINE_PER_100G, IODINE_SOURCE  # noqa: E402
from services.nutrition.food_validation import validate_per_100g  # noqa: E402

CATALOG_PATH = BACKEND / "data" / "foods_catalog.json"
SQL_PATH = BACKEND / "migrations" / "012_seed_validated_foods.sql"
IODINE_SQL_PATH = BACKEND / "migrations" / "014_iodine_values.sql"

# id nutrient USDA -> coloană în `foods` (unitatea USDA = unitatea coloanei)
USDA_NUTRIENTS = {
    1008: "calories",      # kcal
    1003: "protein",       # g
    1004: "fat",           # g
    1005: "carbs",         # g, carbohidrați totali „by difference” (includ fibrele)
    1079: "fiber",         # g
    2000: "sugars",        # g, zaharuri totale
    1018: "alcohol",       # g
    1253: "cholesterol",   # mg
    1087: "calcium",       # mg
    1089: "iron",          # mg
    1090: "magnesium",     # mg
    1091: "phosphorus",    # mg
    1092: "potassium",     # mg
    1093: "sodium",        # mg
    1095: "zinc",          # mg
    1100: "iodine",        # µg (SR Legacy nu are iod pentru aproape niciun aliment -> null)
    1106: "vitamin_a",     # µg RAE
    1114: "vitamin_d",     # µg (D2 + D3)
    1162: "vitamin_c",     # mg
    1178: "vitamin_b12",   # µg
    1185: "vitamin_k",     # µg filochinonă
    1190: "folate",        # µg DFE
}
# Fortificarea obligatorie din SUA (fier, acid folic) nu se aplică produselor românești: nu folosim aceste valori.
US_ENRICHMENT_NUTRIENTS = ("iron", "folate")


def load_usda(sr_dir: Path, fdc_ids: set[int]) -> tuple[dict[int, str], dict[int, dict[str, float]]]:
    descriptions: dict[int, str] = {}
    with open(sr_dir / "food.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fid = int(row["fdc_id"])
            if fid in fdc_ids:
                descriptions[fid] = row["description"]
    values: dict[int, dict[str, float]] = {fid: {} for fid in fdc_ids}
    with open(sr_dir / "food_nutrient.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fid = int(row["fdc_id"])
            nid = int(row["nutrient_id"])
            if fid in fdc_ids and nid in USDA_NUTRIENTS and row["amount"] != "":
                values[fid][USDA_NUTRIENTS[nid]] = float(row["amount"])
    return descriptions, values


def build(sr_dir: Path) -> list[dict]:
    ids = {spec.fdc_id for spec in FOODS}
    descriptions, values = load_usda(sr_dir, ids)
    missing = sorted(ids - set(descriptions))
    if missing:
        raise SystemExit(f"FDC ID inexistente în SR Legacy: {missing}")
    keys = [spec.key for spec in FOODS]
    if len(keys) != len(set(keys)):
        raise SystemExit("Chei duplicate în food_catalog_spec.FOODS")

    catalog = []
    for spec in FOODS:
        if spec.category not in CATEGORIES:
            raise SystemExit(f"{spec.key}: categorie necunoscută {spec.category}")
        per100 = {col: values[spec.fdc_id].get(col) for col in USDA_NUTRIENTS.values()}
        notes = []
        if "us_enriched" in spec.flags:
            for col in US_ENRICHMENT_NUTRIENTS:
                per100[col] = None
            notes.append("iron/folate omise: fortificare obligatorie SUA")
        if spec.key in IODINE_PER_100G:
            db_id, description, value, n = IODINE_PER_100G[spec.key]
            per100["iodine"] = value
            notes.append(f"iodine: {IODINE_SOURCE} DB_ID {db_id} ({description}, n={n})")
        check = validate_per_100g(per100)
        catalog.append({
            "key": spec.key,
            "fdc_id": spec.fdc_id,
            "usda_description": descriptions[spec.fdc_id],
            "name_ro": spec.name_ro,
            "name_en": spec.name_en,
            "category": spec.category,
            "portion_g": spec.portion_g,
            "portion_ro": spec.portion_ro,
            "portion_en": spec.portion_en,
            "animal": spec.animal,
            "allergens": list(spec.allergens),
            "flags": list(spec.flags),
            "per100g": {k: (round(v, 3) if v is not None else None) for k, v in per100.items()},
            "validation": {"ok": check.ok, "issues": check.issues,
                           "atwater_kcal": round(check.atwater_kcal, 1) if check.atwater_kcal is not None else None},
            "notes": notes,
        })
    return catalog


def _sql_literal(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, list):
        return "array[" + ",".join(_sql_literal(v) for v in value) + "]::text[]" if value else "'{}'::text[]"
    return "'" + str(value).replace("'", "''") + "'"


def to_sql(catalog: list[dict]) -> str:
    cols = ["food_key", "fdc_id", "data_source", "validated", "name", "name_en", "category", "category_key",
            "portion_g", "portion_label_ro", "portion_label_en", "animal_source", "allergen_codes", "flags",
            *USDA_NUTRIENTS.values()]
    lines = [
        "-- 012: catalogul validat de alimente (generat de scripts/build_food_catalog.py din USDA FoodData Central SR Legacy).",
        "-- NU edita de mână: modifică data/food_catalog_spec.py și regenerează. Idempotent (upsert pe food_key).",
        "begin;",
        f"insert into public.foods ({', '.join(cols)}) values",
    ]
    rows = []
    for item in catalog:
        cat_ro = CATEGORIES[item["category"]][0]
        vals = [item["key"], item["fdc_id"], "usda_sr_legacy_2018", item["validation"]["ok"], item["name_ro"], item["name_en"],
                cat_ro, item["category"], item["portion_g"], item["portion_ro"], item["portion_en"], item["animal"],
                item["allergens"], item["flags"], *[item["per100g"][c] for c in USDA_NUTRIENTS.values()]]
        rows.append("  (" + ", ".join(_sql_literal(v) for v in vals) + ")")
    lines.append(",\n".join(rows))
    update_cols = [c for c in cols if c != "food_key"]
    lines.append("on conflict (food_key) where food_key is not null do update set " + ", ".join(f"{c} = excluded.{c}" for c in update_cols) + ";")
    lines.append("commit;")
    return "\n".join(lines) + "\n"


def iodine_sql() -> str:
    """Migrarea 014: doar valorile de iod (catalogul 012 era deja aplicat). Idempotentă."""
    lines = [
        "-- 014: iodul din alimentele catalogului validat (generat de scripts/build_food_catalog.py --sql-iodine).",
        "-- Sursa: USDA, FDA and ODS-NIH Database for the Iodine Content of Common Foods, Release 4.0 (2024),",
        "-- µg / 100 g; maparea și motivele sunt în data/iodine_values.py. Alimentele nemapate rămân cu iod NULL.",
        "begin;",
    ]
    for key, (db_id, description, value, n) in IODINE_PER_100G.items():
        lines.append(f"update public.foods set iodine = {value!r} where food_key = '{key}';  -- DB_ID {db_id}, n={n}")
    lines.append("commit;")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sr", type=Path, help="directorul SR Legacy dezarhivat")
    ap.add_argument("--sql", action="store_true", help="scrie și migrarea de seed din catalogul JSON existent")
    ap.add_argument("--sql-iodine", action="store_true", help="scrie migrarea 014 cu valorile de iod")
    args = ap.parse_args()
    if args.sr:
        catalog = build(args.sr)
        CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        bad = [c for c in catalog if not c["validation"]["ok"]]
        print(f"{len(catalog)} alimente scrise în {CATALOG_PATH.name}; {len(bad)} cu probleme de validare:")
        for c in bad:
            print(f"  {c['key']}: {c['validation']['issues']}")
    if args.sql:
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        SQL_PATH.write_text(to_sql(catalog), encoding="utf-8")
        print(f"scris {SQL_PATH}")
    if args.sql_iodine:
        IODINE_SQL_PATH.write_text(iodine_sql(), encoding="utf-8")
        print(f"scris {IODINE_SQL_PATH}")


if __name__ == "__main__":
    main()
