"""
Lab results data access – Supabase only.
"""
from typing import Optional, List
from supabase import Client

from supabase_client import get_supabase_client
from domain.models import LabResultItem, row_to_lab_result


class LabResultRepository:
    TABLE = "lab_results"

    def __init__(self, client: Optional[Client] = None) -> None:
        self._client = client or get_supabase_client()

    def get_latest_by_user_id(self, user_id: int) -> Optional[LabResultItem]:
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
        return row_to_lab_result(resp.data[0])

    def get_all_by_user_id(self, user_id: int) -> List[LabResultItem]:
        resp = (
            self._client.table(self.TABLE)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        if not resp.data:
            return []
        return [row_to_lab_result(r) for r in resp.data]

    def create(self, user_id: int, data: dict) -> LabResultItem:
        row = {"user_id": user_id, **{k: v for k, v in data.items() if v is not None}}
        resp = self._client.table(self.TABLE).insert(row).execute()
        if not resp.data or len(resp.data) == 0:
            raise ValueError("Insert lab_results returned no data")
        return row_to_lab_result(resp.data[0])

    def update(self, lab_result_id: int, data: dict) -> LabResultItem:
        """Actualizează un rând existent. Pentru câmpuri goale, data poate conține None (setează NULL)."""
        update_data = {k: v for k, v in data.items() if k != "user_id"}
        resp = (
            self._client.table(self.TABLE)
            .update(update_data)
            .eq("id", lab_result_id)
            .execute()
        )
        if not resp.data or len(resp.data) == 0:
            raise ValueError("Update lab_results returned no data")
        return row_to_lab_result(resp.data[0])

    def upsert_for_user(self, user_id: int, data: dict) -> LabResultItem:
        """
        Dacă utilizatorul are deja rezultate (ultimul rând), actualizează-l.
        Altfel creează un rând nou. Un singur set de analize per user (update în loc de insert).
        """
        latest = self.get_latest_by_user_id(user_id)
        if latest:
            update_data = {k: v for k, v in data.items() if k != "user_id"}
            return self.update(latest.id, update_data)
        return self.create(user_id, data)
