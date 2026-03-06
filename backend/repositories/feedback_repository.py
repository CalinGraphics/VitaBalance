"""
Feedback data access – Supabase only.
"""
from typing import List, Optional
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
