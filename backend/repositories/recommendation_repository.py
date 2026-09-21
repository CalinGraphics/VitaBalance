"""
Recommendations data access – Supabase only.
"""
from typing import List, Optional
from supabase import Client

from supabase_client import get_supabase_client
from domain.models import RecommendationItem, row_to_recommendation


class RecommendationRepository:
    TABLE = "recommendations"

    def __init__(self, client: Optional[Client] = None):
        self._client = client or get_supabase_client()

    def get_by_user_id(
        self, user_id: int, limit: int = 10
    ) -> List[RecommendationItem]:
        resp = (
            self._client.table(self.TABLE)
            .select("*")
            .eq("user_id", user_id)
            .order("coverage_percentage", desc=True)
            .order("score", desc=True)
            .limit(limit)
            .execute()
        )
        if not resp.data:
            return []
        return [row_to_recommendation(r) for r in resp.data]

    def delete_by_user_id(self, user_id: int) -> None:
        self._client.table(self.TABLE).delete().eq("user_id", user_id).execute()

    def delete_by_id(self, recommendation_id: int) -> None:
        self._client.table(self.TABLE).delete().eq("id", recommendation_id).execute()

    def insert_many(self, rows: List[dict]) -> List[RecommendationItem]:
        if not rows:
            return []
        resp = self._client.table(self.TABLE).insert(rows).execute()
        if not resp.data:
            raise ValueError("Insert recommendations returned no data")
        return [row_to_recommendation(r) for r in resp.data]

    def get_first_by_user_id(self, user_id: int) -> Optional[RecommendationItem]:
        resp = (
            self._client.table(self.TABLE)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if not resp.data or len(resp.data) == 0:
            return None
        return row_to_recommendation(resp.data[0])
