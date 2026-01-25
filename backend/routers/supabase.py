"""
Router pentru endpoint-uri Supabase (dacă sunt necesare)
"""
from fastapi import APIRouter, HTTPException, Depends
from config import get_settings

router = APIRouter(prefix="/api/supabase", tags=["supabase"])


@router.get("/health")
async def supabase_health_check(settings=Depends(get_settings)):
    """
    Verifică dacă configurația Supabase este disponibilă
    """
    if not settings.supabase_url or not settings.supabase_key:
        raise HTTPException(
            status_code=503,
            detail="Supabase nu este configurat. Verifică variabilele de mediu SUPABASE_URL și SUPABASE_KEY."
        )
    
    return {
        "status": "configured",
        "url_configured": bool(settings.supabase_url),
        "key_configured": bool(settings.supabase_key)
    }
