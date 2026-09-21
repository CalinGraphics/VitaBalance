"""
Feedback data access – Supabase only.

Feedback-ul e unic per (user_id, food_id) și persistă când recomandarea e regenerată sau înlocuită
(feedback.recommendation_id devine NULL, rândul rămâne).
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

    def _owned_recommendation_food_id(self, user_id: int, recommendation_id: int) -> Optional[int]:
        """food_id-ul recomandării dacă există și aparține utilizatorului, altfel None."""
        resp = (
            self._client.table("recommendations")
            .select("food_id")
            .eq("id", recommendation_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        if resp.data and resp.data[0].get("food_id") is not None:
            return int(resp.data[0]["food_id"])
        return None

    def upsert(
        self,
        user_id: int,
        recommendation_id: Optional[int],
        rating: int,
        food_id: Optional[int] = None,
    ) -> FeedbackItem:
        """
        Creează sau actualizează votul pentru alimentul recomandat (un singur rând per user_id + food_id).

        Alimentul se ia din recomandare când aceasta există și e a utilizatorului (sursa de adevăr);
        dacă a fost deja ștearsă, se folosește `food_id` primit și feedback-ul se salvează fără legătură la recomandare.
        """
        rec_food_id = (
            self._owned_recommendation_food_id(user_id, recommendation_id)
            if recommendation_id is not None
            else None
        )
        resolved_food_id = rec_food_id if rec_food_id is not None else food_id
        if resolved_food_id is None:
            raise ValueError("Recomandarea nu a fost găsită și nu s-a primit food_id pentru feedback.")

        row = {
            "user_id": user_id,
            "food_id": int(resolved_food_id),
            "recommendation_id": recommendation_id if rec_food_id is not None else None,
            "rating": rating,
        }
        resp = self._client.table(self.TABLE).upsert(row, on_conflict="user_id,food_id").execute()
        if not resp.data or len(resp.data) == 0:
            raise ValueError("Upsert feedback returned no data")
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
