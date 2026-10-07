"""
Jurnalul de stare (wellbeing_checkins, migrarea 015) – Supabase only.

Dacă tabelul nu există încă (migrarea neaplicată), citirile întorc o listă goală și scrierile ridică
CheckinStoreUnavailable, ca restul aplicației (recomandările) să funcționeze în continuare.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import List, Optional

from supabase import Client

from domain.models import CheckIn, row_to_checkin
from repositories.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

_MISSING_TABLE_CODES = {"PGRST205", "42P01"}


class CheckinStoreUnavailable(RuntimeError):
    pass


def _is_missing_table(exc: Exception) -> bool:
    code = getattr(exc, "code", None) or (exc.args[0].get("code") if exc.args and isinstance(exc.args[0], dict) else None)
    text = str(exc)
    return code in _MISSING_TABLE_CODES or "wellbeing_checkins" in text and ("does not exist" in text or "Could not find" in text)


class CheckinRepository:
    TABLE = "wellbeing_checkins"

    def __init__(self, client: Optional[Client] = None):
        self._client = client or get_supabase_client()

    def list_for_user(self, user_id: int, limit: int = 120) -> List[CheckIn]:
        try:
            resp = (
                self._client.table(self.TABLE)
                .select("*")
                .eq("user_id", user_id)
                .order("checked_on", desc=True)
                .limit(limit)
                .execute()
            )
        except Exception as exc:  # noqa: BLE001
            if _is_missing_table(exc):
                logger.warning("Tabelul wellbeing_checkins lipsește (migrarea 015 neaplicată).")
                return []
            raise
        return [row_to_checkin(r) for r in resp.data or []]

    def is_available(self) -> bool:
        try:
            self._client.table(self.TABLE).select("id").limit(1).execute()
            return True
        except Exception as exc:  # noqa: BLE001
            if _is_missing_table(exc):
                return False
            raise

    def upsert_for_day(self, user_id: int, checked_on: date, data: dict) -> CheckIn:
        row = {
            "user_id": user_id,
            "checked_on": checked_on.isoformat(),
            "symptoms": data.get("symptoms") or [],
            "severity": data.get("severity"),
            "energy": data.get("energy"),
            "weight": data.get("weight"),
            "notes": data.get("notes"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            resp = self._client.table(self.TABLE).upsert(row, on_conflict="user_id,checked_on").execute()
        except Exception as exc:  # noqa: BLE001
            if _is_missing_table(exc):
                raise CheckinStoreUnavailable() from exc
            raise
        if not resp.data:
            raise ValueError("Upsert wellbeing_checkins returned no data")
        return row_to_checkin(resp.data[0])

    def delete(self, user_id: int, checkin_id: int) -> bool:
        try:
            resp = self._client.table(self.TABLE).delete().eq("id", checkin_id).eq("user_id", user_id).execute()
        except Exception as exc:  # noqa: BLE001
            if _is_missing_table(exc):
                raise CheckinStoreUnavailable() from exc
            raise
        return bool(resp.data)
