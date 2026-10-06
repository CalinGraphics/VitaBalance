"""
Cache pe recomandări, cu cheia = hash(profil + analize + catalog + versiunea scorului), independentă de limbă.

- `inputs_hash` (fără voturi) se salvează în faptele fiecărei recomandări: dacă la următoarea cerere hash-ul e același,
  recomandările din DB sunt încă valabile, oricât s-ar fi mișcat `updated_at` (ex. schimbarea pozei sau a numelui).
  Invalidarea e automată: orice schimbare de profil sau analize schimbă hash-ul.
- `RankingCache` ține în memorie clasamentele calculate recent (cheia include și voturile și excluderile).
"""
from __future__ import annotations

import hashlib
import json
import threading
from collections import OrderedDict
from typing import Any, Dict, Iterable, Optional, Sequence

from domain.models import FoodItem, LabResultItem, UserProfile

_PROFILE_FIELDS = ("age", "sex", "weight", "height", "activity_level", "diet_type", "allergies", "medical_conditions")
_LAB_FIELDS = ("hemoglobin", "ferritin", "vitamin_d", "vitamin_b12", "calcium", "magnesium", "zinc", "protein", "folate",
               "vitamin_a", "vitamin_c", "iodine", "vitamin_k", "potassium", "notes")


def catalog_signature(foods: Sequence[FoodItem]) -> str:
    """Se schimbă când se schimbă catalogul validat (alimente adăugate/scoase sau valori modificate)."""
    h = hashlib.sha256()
    for f in foods:
        if f.validated:
            h.update(f"{f.id}:{f.food_key}:{f.calories}:{f.portion_g}:{f.magnesium}:{f.iron}:{f.vitamin_d};".encode())
    return h.hexdigest()[:16]


def inputs_hash(user: UserProfile, lab_results: Optional[LabResultItem], catalog: str, versions: str) -> str:
    payload: Dict[str, Any] = {
        "user": {k: getattr(user, k, None) for k in _PROFILE_FIELDS},
        "labs": {k: getattr(lab_results, k, None) for k in _LAB_FIELDS} if lab_results is not None else None,
        "catalog": catalog,
        "versions": versions,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:24]


class RankingCache:
    def __init__(self, max_items: int = 256):
        self._items: "OrderedDict[str, Any]" = OrderedDict()
        self._max = max_items
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    @staticmethod
    def key(inputs: str, feedback: Dict[int, str], exclude: Iterable[int]) -> str:
        return f"{inputs}|{sorted(feedback.items())}|{sorted(set(exclude))}"

    def get(self, key: str):
        with self._lock:
            value = self._items.get(key)
            if value is None:
                self.misses += 1
                return None
            self._items.move_to_end(key)
            self.hits += 1
            return value

    def put(self, key: str, value) -> None:
        with self._lock:
            self._items[key] = value
            self._items.move_to_end(key)
            while len(self._items) > self._max:
                self._items.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


RANKING_CACHE = RankingCache()
