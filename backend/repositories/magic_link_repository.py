"""
Magic link tokens – stocate în Supabase. Un token = un link unic, expiră, invalid după folosire.
"""
from datetime import datetime, timezone
from typing import Optional
from supabase import Client

from supabase_client import get_supabase_client
from config import get_settings


TABLE = "magic_links"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_token(email: str) -> str:
    """Generează token unic, îl salvează în Supabase, returnează tokenul."""
    import secrets
    token = secrets.token_urlsafe(32)
    settings = get_settings()
    expires_at = _now_utc()
    from datetime import timedelta
    expires_at = expires_at + timedelta(hours=settings.magic_link_expire_hours)
    client: Client = get_supabase_client()
    row = {
        "email": email.strip().lower(),
        "token": token,
        "expires_at": expires_at.isoformat(),
        "used_at": None,
    }
    client.table(TABLE).insert(row).execute()
    return token


def consume_token(token: str) -> Optional[dict]:
    """
    Validează tokenul: există, nu e expirat, nu e folosit.
    Îl marchează ca folosit (used_at = now) și returnează {"email": str}.
    Returnează None dacă invalid sau deja folosit.
    """
    client: Client = get_supabase_client()
    now_iso = _now_utc().isoformat()
    # Consum atomic: un singur UPDATE condiționat pe token + folosit/neexpirat.
    # Dacă două request-uri rulează în paralel, doar unul va actualiza rândul.
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
