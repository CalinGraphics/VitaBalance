"""
Pozele de profil în Supabase Storage (bucket privat `avatars`, migrarea 010).

Apeluri REST directe prin httpx, cu cheia service_role (ca în services/auth.py), ca să nu depindem de
versiunea clientului de Storage instalată odată cu supabase-py.
"""
import logging
from typing import Optional
from urllib.parse import quote

import httpx

from config import get_settings
from repositories.supabase_client import service_role_headers

logger = logging.getLogger(__name__)

BUCKET = "avatars"
# Linkul semnat expiră; profilul e citit la fiecare login / reîncărcare, deci un link nou vine des.
SIGNED_URL_TTL_SECONDS = 24 * 3600
_HTTP_TIMEOUT = httpx.Timeout(15.0, connect=5.0)


class AvatarStorageError(Exception):
    pass


def _storage_url() -> str:
    url = get_settings().supabase_url
    if not url:
        raise AvatarStorageError("SUPABASE_URL lipsește din configurare")
    return url.rstrip("/") + "/storage/v1"


def _headers() -> dict:
    key = get_settings().effective_supabase_secret_key()
    if not key:
        raise AvatarStorageError("Cheia Supabase (service_role) lipsește din configurare")
    return service_role_headers(key)


def _object_path(path: str) -> str:
    return f"{BUCKET}/{quote(path, safe='/')}"


def _request(method: str, url: str, **kwargs) -> httpx.Response:
    try:
        with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
            return client.request(method, url, **kwargs)
    except httpx.HTTPError as exc:
        raise AvatarStorageError(f"Supabase Storage indisponibil: {exc}") from exc


def upload(path: str, data: bytes, content_type: str) -> None:
    resp = _request(
        "POST",
        f"{_storage_url()}/object/{_object_path(path)}",
        content=data,
        headers={**_headers(), "Content-Type": content_type, "x-upsert": "true"},
    )
    if resp.status_code not in (200, 201):
        raise AvatarStorageError(f"Upload eșuat: HTTP {resp.status_code} {resp.text[:200]}")


def remove(path: str) -> None:
    """Șterge fișierul; o eroare doar se loghează (un fișier orfan nu strică nimic)."""
    try:
        resp = _request(
            "DELETE",
            f"{_storage_url()}/object/{BUCKET}",
            json={"prefixes": [path]},
            headers=_headers(),
        )
        if resp.status_code not in (200, 204):
            logger.warning("Ștergerea pozei %s a eșuat: HTTP %s", path, resp.status_code)
    except AvatarStorageError as exc:
        logger.warning("Ștergerea pozei %s a eșuat: %s", path, exc)


def signed_url(path: Optional[str]) -> Optional[str]:
    """Link temporar către poză, sau None dacă nu există poză ori Storage nu răspunde."""
    if not path:
        return None
    try:
        resp = _request(
            "POST",
            f"{_storage_url()}/object/sign/{_object_path(path)}",
            json={"expiresIn": SIGNED_URL_TTL_SECONDS},
            headers=_headers(),
        )
    except AvatarStorageError as exc:
        logger.warning("Link semnat indisponibil pentru %s: %s", path, exc)
        return None
    if resp.status_code != 200:
        logger.warning("Link semnat refuzat pentru %s: HTTP %s", path, resp.status_code)
        return None
    signed = (resp.json() or {}).get("signedURL") or (resp.json() or {}).get("signedUrl")
    if not signed:
        return None
    return _storage_url() + "/" + signed.lstrip("/")
