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

    def get_counts_by_food(self, user_id: Optional[int] = None) -> Dict[int, Dict[str, int]]:
        """
        Returnează pentru fiecare food_id:
        {
          food_id: { 'likes': x, 'dislikes': y }
        }
        Opțional, se poate filtra doar pe un anumit user_id (pentru debugging).
        """
        query = self._client.table(self.TABLE).select("food_id, rating").neq("food_id", None)
        if user_id is not None:
            query = query.eq("user_id", user_id)
        resp = query.execute()
        counts: Dict[int, Dict[str, int]] = {}
        if not resp.data:
            return counts
        for row in resp.data:
            food_id = row.get("food_id")
            rating = row.get("rating", 0)
            if food_id is None:
                continue
            if food_id not in counts:
                counts[food_id] = {"likes": 0, "dislikes": 0}
            if isinstance(rating, (int, float)) and rating >= 4:
                counts[food_id]["likes"] += 1
            elif isinstance(rating, (int, float)) and rating <= 2:
                counts[food_id]["dislikes"] += 1
        return counts

    def create(
        self,
        user_id: int,
        rating: int,
        *,
        recommendation_id: Optional[int] = None,
        comment: Optional[str] = None,
        tried: bool = False,
        worked: Optional[bool] = None,
    ) -> FeedbackItem:
        row = {
            "user_id": user_id,
            "rating": rating,
            "recommendation_id": recommendation_id,
            "comment": comment,
            "tried": tried,
            "worked": worked,
        }
        row = {k: v for k, v in row.items() if v is not None}
        resp = self._client.table(self.TABLE).insert(row).execute()
        if not resp.data or len(resp.data) == 0:
            raise ValueError("Insert feedback returned no data")
        return row_to_feedback(resp.data[0])
