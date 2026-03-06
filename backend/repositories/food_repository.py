"""
Food catalog data access – Supabase only.
"""
from typing import List, Optional
from supabase import Client

from supabase_client import get_supabase_client
from domain.models import FoodItem, row_to_food


class FoodRepository:
    TABLE = "foods"

    def __init__(self, client: Optional[Client] = None):
        self._client = client or get_supabase_client()

    def get_all(self) -> List[FoodItem]:
        resp = self._client.table(self.TABLE).select("*").execute()
        if not resp.data:
            return []
        return [row_to_food(r) for r in resp.data]
