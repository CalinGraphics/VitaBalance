"""Client Supabase."""
from typing import Optional
from supabase import create_client, Client
from config import get_settings

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    settings = get_settings()

    key = settings.effective_supabase_secret_key()
    if not settings.supabase_url or not key:
        raise ValueError(
            "Lipsesc SUPABASE_URL sau cheia (SUPABASE_KEY / SUPABASE_SERVICE_ROLE_KEY). Vezi README."
        )

    _supabase_client = create_client(settings.supabase_url, key)
    return _supabase_client
