"""
Client Supabase pentru sincronizarea datelor
"""
from typing import Optional
from supabase import create_client, Client
from config import get_settings

# Instanță globală de client Supabase
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Obține instanța de client Supabase (singleton)
    
    Returns:
        Client Supabase configurat
        
    Raises:
        ValueError: Dacă SUPABASE_URL sau SUPABASE_KEY nu sunt setate
    """
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    settings = get_settings()
    
    if not settings.supabase_url or not settings.supabase_key:
        raise ValueError(
            "SUPABASE_URL și SUPABASE_KEY trebuie să fie setate în variabilele de mediu. "
            "Adaugă-le în fișierul .env din folderul backend."
        )
    
    _supabase_client = create_client(settings.supabase_url, settings.supabase_key)
    return _supabase_client
