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


def create_token(email: str, full_name: Optional[str] = None) -> str:
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
    if full_name is not None:
        row["full_name"] = full_name.strip()
    client.table(TABLE).insert(row).execute()
    return token


def consume_token(token: str) -> Optional[dict]:
    """
    Validează tokenul: există, nu e expirat, nu e folosit.
    Îl marchează ca folosit (used_at = now) și returnează {"email": str, "full_name": str|None}.
    Returnează None dacă invalid sau deja folosit.
    """
    client: Client = get_supabase_client()
    r = client.table(TABLE).select("id, email, full_name, expires_at, used_at").eq("token", token).execute()
    if not r.data or len(r.data) == 0:
        return None
    row = r.data[0]
    if row.get("used_at"):
        return None
    expires_at = row.get("expires_at")
    if expires_at:
        try:
            if isinstance(expires_at, str):
                exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            else:
                exp = expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if _now_utc() > exp:
                return None
        except Exception:
            return None
    email = row.get("email")
    if not email:
        return None
    # Marchează ca folosit
    client.table(TABLE).update({"used_at": _now_utc().isoformat()}).eq("id", row["id"]).execute()
    return {"email": email, "full_name": row.get("full_name")}
