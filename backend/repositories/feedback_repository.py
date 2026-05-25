"""
Feedback data access – Supabase only.
"""
from typing import Dict, List, Optional
from supabase import Client

from supabase_client import get_supabase_client
from domain.models import FeedbackItem, row_to_feedback


class FeedbackRepository:
    TABLE = "feedback"

    def __init__(self, client: Optional[Client] = None):
        self._client = client or get_supabase_client()

    def get_by_user_id(self, user_id: int) -> List[FeedbackItem]:
        resp = (
            self._client.table(self.TABLE)
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        if not resp.data:
            return []
        return [row_to_feedback(r) for r in resp.data]

    def get_by_user_and_recommendation(self, user_id: int, recommendation_id: int) -> Optional[FeedbackItem]:
        resp = (
            self._client.table(self.TABLE)
            .select("*")
            .eq("user_id", user_id)
            .eq("recommendation_id", recommendation_id)
            .limit(1)
            .execute()
        )
        if not resp.data or len(resp.data) == 0:
            return None
        return row_to_feedback(resp.data[0])

    def _resolve_food_id(self, recommendation_id: int, food_id: Optional[int]) -> Optional[int]:
        if food_id is not None:
            return int(food_id)
        resp = (
            self._client.table("recommendations")
            .select("food_id")
            .eq("id", recommendation_id)
            .limit(1)
            .execute()
        )
        if resp.data and len(resp.data) > 0 and resp.data[0].get("food_id") is not None:
            return int(resp.data[0]["food_id"])
        return None

    def upsert(
        self,
        user_id: int,
        recommendation_id: int,
        rating: int,
        food_id: Optional[int] = None,
    ) -> FeedbackItem:
        """Creează sau actualizează feedback-ul. Un singur vote per (user_id, recommendation_id)."""
        resolved_food_id = self._resolve_food_id(recommendation_id, food_id)
        existing = self.get_by_user_and_recommendation(user_id, recommendation_id)
        payload = {"rating": rating}
        if resolved_food_id is not None:
            payload["food_id"] = resolved_food_id
        if existing:
            resp = (
                self._client.table(self.TABLE)
                .update(payload)
                .eq("id", existing.id)
                .execute()
            )
            if not resp.data or len(resp.data) == 0:
                raise ValueError("Update feedback returned no data")
            return row_to_feedback(resp.data[0])
        row = {
            "user_id": user_id,
            "recommendation_id": recommendation_id,
            "rating": rating,
        }
        if resolved_food_id is not None:
            row["food_id"] = resolved_food_id
        resp = self._client.table(self.TABLE).insert(row).execute()
        if not resp.data or len(resp.data) == 0:
            raise ValueError("Insert feedback returned no data")
        return row_to_feedback(resp.data[0])

    def get_counts_by_food_ids(self, food_ids: List[int], user_id: Optional[int] = None) -> Dict[int, Dict[str, int]]:
        """
        Agregă likes/dislikes per food_id folosind coloana food_id (fără join recommendations).
        """
        wanted = {int(x) for x in (food_ids or []) if x is not None}
        if not wanted:
            return {}

        query = (
            self._client.table(self.TABLE)
            .select("food_id, rating")
            .in_("food_id", list(wanted))
        )
        if user_id is not None:
            query = query.eq("user_id", user_id)
        resp = query.execute()

        counts: Dict[int, Dict[str, int]] = {fid: {"likes": 0, "dislikes": 0} for fid in wanted}
        if not resp.data:
            return counts

        for row in resp.data:
            fid = row.get("food_id")
            if fid is None:
                continue
            fid = int(fid)
            if fid not in counts:
                counts[fid] = {"likes": 0, "dislikes": 0}
            rating = row.get("rating", 0)
            if isinstance(rating, (int, float)) and rating >= 4:
                counts[fid]["likes"] += 1
            elif isinstance(rating, (int, float)) and rating <= 2:
                counts[fid]["dislikes"] += 1
        return counts

    def create(
        self,
        user_id: int,
        rating: int,
        *,
        recommendation_id: int,
        food_id: Optional[int] = None,
    ) -> FeedbackItem:
        return self.upsert(user_id, recommendation_id, rating, food_id=food_id)
