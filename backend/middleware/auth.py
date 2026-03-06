"""
Auth middleware: validare JWT pe rutele protejate. User atașat în request context.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from services.auth import verify_access_token

security = HTTPBearer(auto_error=False)
optional_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    Dependency: cere Bearer JWT, verifică tokenul, returnează payload (email, sub).
    Ridică 401 dacă lipsește sau e invalid.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Lipsește tokenul de autentificare",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = verify_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalid sau expirat",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
) -> Optional[dict]:
    """Dependency: returnează user din JWT dacă există, altfel None. Nu ridică 401."""
    if not credentials:
        return None
    return verify_access_token(credentials.credentials)
