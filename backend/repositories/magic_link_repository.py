"""Tokenuri magic link în Supabase."""
from datetime import datetime, timezone
from typing import Optional
from supabase import Client

from supabase_client import get_supabase_client
from config import get_settings


TABLE = "magic_links"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_token(email: str) -> str:
    import secrets
    from datetime import timedelta

    token = secrets.token_urlsafe(32)
    settings = get_settings()
    expires_at = _now_utc() + timedelta(hours=settings.magic_link_expire_hours)
    client: Client = get_supabase_client()
    row = {
        "email": email.strip().lower(),
        "token": token,
        "expires_at": expires_at.isoformat(),
        "used_at": None,
    }
    try:
        client.table(TABLE).insert(row).execute()
    except Exception as exc:  # noqa: BLE001
        raw = str(exc) + repr(exc)
        raw_l = raw.lower()
        if "42501" in raw or "row-level security" in raw_l or "violates row-level security" in raw_l:
            raise RuntimeError(
                "Nu s-a putut salva tokenul (RLS). Pune cheia service_role din Supabase "
                "în SUPABASE_SERVICE_ROLE_KEY sau SUPABASE_KEY pe server."
            ) from exc
        raise
    return token


def consume_token(token: str) -> Optional[dict]:
    client: Client = get_supabase_client()
    now_iso = _now_utc().isoformat()
    updated = (
        client.table(TABLE)
        .update({"used_at": now_iso})
        .eq("token", token)
        .is_("used_at", "null")
        .gt("expires_at", now_iso)
        .execute()
    )
    if not updated.data or len(updated.data) == 0:
        return None
    row = updated.data[0]
    email = row.get("email")
    if not email:
        return None
    return {"email": email}
