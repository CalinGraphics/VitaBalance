"""
Food catalog data access – Supabase only.
"""
from __future__ import annotations

import threading
import time
from typing import List, Optional, Tuple

from supabase import Client

from supabase_client import get_supabase_client
from domain.models import FoodItem, row_to_food


class FoodRepository:
    TABLE = "foods"
    _cache_lock = threading.Lock()
    _foods_cache: Optional[Tuple[float, List[FoodItem]]] = None
    _CACHE_TTL_SEC = 180.0

    def __init__(self, client: Optional[Client] = None):
        self._client = client or get_supabase_client()

    def get_all(self) -> List[FoodItem]:
        now = time.monotonic()
        with self._cache_lock:
            cached = self._foods_cache
            if cached is not None:
                ts, items = cached
                if now - ts < self._CACHE_TTL_SEC:
                    return items

        resp = self._client.table(self.TABLE).select("*").execute()
        if not resp.data:
            items: List[FoodItem] = []
        else:
            items = [row_to_food(r) for r in resp.data]

        with self._cache_lock:
            self._foods_cache = (time.monotonic(), items)
        return items
