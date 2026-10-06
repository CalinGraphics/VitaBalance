"""
Auth middleware: validează tokenul Supabase Auth pe rutele protejate.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from services.auth import AuthError, verify_access_token

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    Dependency: cere Bearer token emis de Supabase Auth și returnează identitatea (email, sub).
    Ridică 401 dacă lipsește sau e invalid.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Lipsește tokenul de autentificare",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = verify_access_token(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalid sau expirat",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload
