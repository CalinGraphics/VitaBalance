"""
User profile data access – Supabase only.
"""
from typing import Optional, List
from supabase import Client

from supabase_client import get_supabase_client
from domain.models import UserProfile, row_to_user


class UserRepository:
    TABLE = "users"

    def __init__(self, client: Optional[Client] = None):
        self._client = client or get_supabase_client()

    def get_by_id(self, user_id: int) -> Optional[UserProfile]:
        resp = self._client.table(self.TABLE).select("*").eq("id", user_id).execute()
        if not resp.data or len(resp.data) == 0:
            return None
        return row_to_user(resp.data[0])

    def get_by_email(self, email: str) -> Optional[UserProfile]:
        resp = self._client.table(self.TABLE).select("*").eq("email", email).execute()
        if not resp.data or len(resp.data) == 0:
            return None
        return row_to_user(resp.data[0])

    def upsert(
        self,
        email: str,
        *,
        name: str,
        age: int,
        sex: str,
        weight: float,
        height: float,
        activity_level: str,
        diet_type: str,
        allergies: Optional[str] = None,
        medical_conditions: Optional[str] = None,
        full_name: Optional[str] = None,
        bio: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> UserProfile:
        row = {
            "email": email,
            "name": name,
            "full_name": full_name or name,
            "age": age,
            "sex": sex,
            "weight": weight,
            "height": height,
            "activity_level": activity_level,
            "diet_type": diet_type,
            "allergies": allergies if allergies is not None else "",
            "medical_conditions": medical_conditions if medical_conditions is not None else "",
        }
        if user_id is not None:
            resp = self._client.table(self.TABLE).update(row).eq("id", user_id).execute()
        else:
            resp = self._client.table(self.TABLE).upsert(row, on_conflict="email").execute()
        if not resp.data or len(resp.data) == 0:
            raise ValueError("Upsert users returned no data")
        return row_to_user(resp.data[0])
