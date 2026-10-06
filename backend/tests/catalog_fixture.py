"""Catalogul validat real (data/foods_catalog.json) ca FoodItem-uri, pentru teste fără baza de date."""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from domain.models import FoodItem, food_from_catalog_entry  # noqa: E402

CATALOG_PATH = BACKEND_ROOT / "data" / "foods_catalog.json"
ID_OFFSET = 1000


@lru_cache(maxsize=1)
def catalog_entries() -> tuple:
    return tuple(json.loads(CATALOG_PATH.read_text(encoding="utf-8")))


def all_foods() -> List[FoodItem]:
    return [food_from_catalog_entry(e, ID_OFFSET + i) for i, e in enumerate(catalog_entries())]


def foods_by_key() -> Dict[str, FoodItem]:
    return {f.food_key: f for f in all_foods()}


def food(key: str, **overrides) -> FoodItem:
    f = foods_by_key()[key]
    return replace(f, **overrides) if overrides else f
