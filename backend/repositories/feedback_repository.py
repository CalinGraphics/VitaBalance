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

    def upsert(
        self,
        user_id: int,
        recommendation_id: int,
        rating: int,
        *,
        comment: Optional[str] = None,
        tried: bool = False,
        worked: Optional[bool] = None,
    ) -> FeedbackItem:
        """Creează sau actualizează feedback-ul. Un singur vote per (user_id, recommendation_id)."""
        existing = self.get_by_user_and_recommendation(user_id, recommendation_id)
        if existing:
            resp = (
                self._client.table(self.TABLE)
                .update({
                    "rating": rating,
                    "comment": comment,
                    "tried": tried,
                    "worked": worked,
                })
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
            "comment": comment,
            "tried": tried,
            "worked": worked,
        }
        row = {k: v for k, v in row.items() if v is not None}
        resp = self._client.table(self.TABLE).insert(row).execute()
        if not resp.data or len(resp.data) == 0:
            raise ValueError("Insert feedback returned no data")
        return row_to_feedback(resp.data[0])

    def get_counts_by_recommendation(self, user_id: Optional[int] = None) -> Dict[int, Dict[str, int]]:
        """
        Returnează pentru fiecare recommendation_id:
        {
          recommendation_id: { 'likes': x, 'dislikes': y }
        }
        Opțional, se poate filtra doar pe un anumit user_id (pentru debugging).
        """
        query = self._client.table(self.TABLE).select("recommendation_id, rating")
        if user_id is not None:
            query = query.eq("user_id", user_id)
        resp = query.execute()
        counts: Dict[int, Dict[str, int]] = {}
        if not resp.data:
            return counts
        for row in resp.data:
            rec_id = row.get("recommendation_id")
            rating = row.get("rating", 0)
            if rec_id is None:
                continue
            if rec_id not in counts:
                counts[rec_id] = {"likes": 0, "dislikes": 0}
            if isinstance(rating, (int, float)) and rating >= 4:
                counts[rec_id]["likes"] += 1
            elif isinstance(rating, (int, float)) and rating <= 2:
                counts[rec_id]["dislikes"] += 1
        return counts

    def get_counts_by_food_id(self) -> Dict[int, Dict[str, int]]:
        """
        Returnează pentru fiecare food_id agregatul de likes/dislikes din toate
        feedback-urile, astfel încât alți utilizatori să vadă că o recomandare
        a mai fost apreciată.
        """
        resp = self._client.table(self.TABLE).select("recommendation_id, rating").execute()
        if not resp.data:
            return {}
        rec_ids = {r["recommendation_id"] for r in resp.data if r.get("recommendation_id") is not None}
        if not rec_ids:
            return {}
        rec_resp = (
            self._client.table("recommendations")
            .select("id, food_id")
            .in_("id", list(rec_ids))
            .execute()
        )
        rec_to_food: Dict[int, int] = {}
        if rec_resp.data:
            for r in rec_resp.data:
                fid = r.get("food_id")
                if fid is not None:
                    rec_to_food[r["id"]] = fid
        counts: Dict[int, Dict[str, int]] = {}
        for row in resp.data:
            rec_id = row.get("recommendation_id")
            rating = row.get("rating", 0)
            if rec_id is None or rec_id not in rec_to_food:
                continue
            fid = rec_to_food[rec_id]
            if fid not in counts:
                counts[fid] = {"likes": 0, "dislikes": 0}
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
