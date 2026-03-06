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
