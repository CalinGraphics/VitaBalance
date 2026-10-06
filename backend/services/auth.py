"""
Autentificare prin Supabase Auth: emailul și parola stau în `auth.users`, sesiunea e tokenul emis de Supabase.

Backend-ul vorbește direct cu API-ul GoTrue (`/auth/v1/...`) prin httpx, cu cheia service_role,
și nu semnează tokenuri proprii. Profilul aplicației (`public.users`) se creează / se leagă automat
prin triggerul `on_auth_user_created` (migrarea 007).
"""
import hashlib
import logging
import threading
import time
from typing import Any, Dict, Optional

import httpx

from config import get_settings
from repositories.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

_HTTP_TIMEOUT = httpx.Timeout(10.0, connect=5.0)
# Cât păstrăm în memorie rezultatul validării unui token, ca să nu întrebăm Supabase la fiecare cerere.
_USER_CACHE_TTL_SECONDS = 60.0
_USER_CACHE_MAX = 2048

_ALREADY_REGISTERED = "Acest email este deja înregistrat"
_INVALID_CREDENTIALS = "Email sau parolă incorectă"


class AuthError(Exception):
    """Eroare de autentificare cu codul HTTP care trebuie întors clientului."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


# ---------- HTTP către Supabase Auth ----------
def _auth_base_url() -> str:
    settings = get_settings()
    if not settings.supabase_url:
        raise AuthError(500, "SUPABASE_URL lipsește din configurare")
    return settings.supabase_url.rstrip("/") + "/auth/v1"


def _service_key() -> str:
    key = get_settings().effective_supabase_secret_key()
    if not key:
        raise AuthError(500, "Cheia Supabase (service_role) lipsește din configurare")
    return key


def _service_headers() -> Dict[str, str]:
    key = _service_key()
    headers = {"apikey": key}
    # Cheile vechi (JWT service_role) merg și în Authorization; cele noi `sb_secret_...` doar în apikey.
    if key.count(".") == 2:
        headers["Authorization"] = f"Bearer {key}"
    return headers


def _request(method: str, path: str, *, json: Optional[dict] = None, headers: Optional[dict] = None) -> httpx.Response:
    try:
        with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
            return client.request(method, _auth_base_url() + path, json=json, headers=headers)
    except httpx.HTTPError as exc:
        logger.warning("Supabase Auth indisponibil: %s", exc)
        raise AuthError(503, "Serviciul de autentificare nu răspunde. Încearcă din nou.") from exc


def _error_text(resp: httpx.Response) -> str:
    try:
        body = resp.json()
    except ValueError:
        return resp.text or ""
    if isinstance(body, dict):
        parts = [str(body.get(k) or "") for k in ("error_code", "code", "msg", "message", "error", "error_description")]
        return " ".join(p for p in parts if p)
    return str(body)


def _session_from_token_response(body: Dict[str, Any]) -> Dict[str, Any]:
    user = body.get("user") or {}
    meta = user.get("user_metadata") or {}
    return {
        "access_token": body.get("access_token"),
        "refresh_token": body.get("refresh_token"),
        "expires_in": body.get("expires_in"),
        "expires_at": body.get("expires_at"),
        "auth_user_id": user.get("id"),
        "email": (user.get("email") or "").lower(),
        "fullName": meta.get("full_name") or "",
    }


def _password_grant(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Returnează sesiunea sau None pentru credențiale greșite."""
    resp = _request(
        "POST",
        "/token?grant_type=password",
        json={"email": email, "password": password},
        headers=_service_headers(),
    )
    if resp.status_code == 200:
        return _session_from_token_response(resp.json())
    if resp.status_code in (400, 401, 422):
        return None
    logger.error("Login Supabase Auth: HTTP %s %s", resp.status_code, _error_text(resp)[:300])
    raise AuthError(502, "Autentificarea a eșuat. Încearcă din nou.")


def _admin_create_user(email: str, password: str, full_name: str) -> Dict[str, Any]:
    resp = _request(
        "POST",
        "/admin/users",
        json={
            "email": email,
            "password": password,
            # Nu există pas de confirmare prin email (ca înainte): contul e activ imediat.
            "email_confirm": True,
            "user_metadata": {"full_name": full_name},
        },
        headers=_service_headers(),
    )
    if resp.status_code in (200, 201):
        return resp.json()
    text = _error_text(resp).lower()
    if "already" in text or "exists" in text or "email_exists" in text:
        raise AuthError(400, _ALREADY_REGISTERED)
    if "password" in text and ("weak" in text or "least" in text or "short" in text):
        raise AuthError(400, "Parola este prea slabă (minim 6 caractere)")
    if resp.status_code == 422 and "email" in text:
        raise AuthError(400, "Adresa de email nu este validă")
    logger.error("Creare cont Supabase Auth: HTTP %s %s", resp.status_code, _error_text(resp)[:300])
    raise AuthError(500, "Eroare la crearea contului. Încearcă din nou.")


# ---------- Profilul din public.users ----------
def _profile_row(email: str) -> Optional[Dict[str, Any]]:
    resp = (
        get_supabase_client()
        .table("users")
        .select("id, name, auth_user_id")
        .eq("email", email)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


def _profile_name(email: str) -> str:
    try:
        row = _profile_row(email)
    except Exception:  # noqa: BLE001 - numele e doar cosmetic
        logger.warning("Nu am putut citi numele profilului pentru %s", email)
        return ""
    return (row or {}).get("name") or ""


# ---------- API folosit de rute ----------
def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def sign_in(email: str, password: str) -> Dict[str, Any]:
    email = _normalize_email(email)
    if not email or not password:
        raise AuthError(401, _INVALID_CREDENTIALS)
    session = _password_grant(email, password)
    if session is None:
        raise AuthError(401, _INVALID_CREDENTIALS)
    session["fullName"] = _profile_name(email) or session["fullName"]
    return session


def sign_up(email: str, password: str, full_name: str) -> Dict[str, Any]:
    """
    Creează contul în Supabase Auth și deschide sesiunea.

    Profilele vechi fără parolă (fost magic link) sunt adoptate de trigger: utilizatorul își păstrează
    profilul, analizele și recomandările. Un profil care are deja cont e respins.
    """
    email = _normalize_email(email)
    full_name = (full_name or "").strip()
    if not email:
        raise AuthError(400, "Email-ul este obligatoriu")
    if not full_name:
        raise AuthError(400, "Numele complet este obligatoriu")
    if not password:
        raise AuthError(400, "Parola este obligatorie")
    if not password.strip():
        raise AuthError(400, "Parola nu poate conține doar spații")
    if len(password.strip()) < 6:
        raise AuthError(400, "Parola trebuie să aibă minim 6 caractere")

    existing = _profile_row(email)
    if existing and existing.get("auth_user_id"):
        raise AuthError(400, _ALREADY_REGISTERED)

    _admin_create_user(email, password, full_name)
    session = _password_grant(email, password)
    if session is None:
        raise AuthError(500, "Contul a fost creat, dar autentificarea a eșuat. Încearcă să te loghezi.")
    session["fullName"] = _profile_name(email) or full_name
    return session


def refresh_session(refresh_token: str) -> Dict[str, Any]:
    if not refresh_token:
        raise AuthError(401, "Sesiune expirată")
    resp = _request(
        "POST",
        "/token?grant_type=refresh_token",
        json={"refresh_token": refresh_token},
        headers=_service_headers(),
    )
    if resp.status_code != 200:
        raise AuthError(401, "Sesiune expirată")
    session = _session_from_token_response(resp.json())
    session["fullName"] = _profile_name(session["email"]) or session["fullName"]
    return session


def sign_out(access_token: str) -> None:
    _forget_token(access_token)
    headers = {"apikey": _service_key(), "Authorization": f"Bearer {access_token}"}
    try:
        _request("POST", "/logout", headers=headers)
    except AuthError:
        pass  # deconectarea locală e suficientă; tokenul expiră oricum


# ---------- Validarea tokenului pe rutele protejate ----------
_user_cache: Dict[str, tuple] = {}
_user_cache_lock = threading.Lock()


def _cache_key(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _forget_token(token: str) -> None:
    with _user_cache_lock:
        _user_cache.pop(_cache_key(token), None)


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validează tokenul la Supabase Auth (`GET /auth/v1/user`) și returnează identitatea:
    `{"sub": <auth user id>, "email": ..., "auth_user_id": ...}`, sau None dacă e invalid/expirat.
    """
    if not token:
        return None
    key = _cache_key(token)
    now = time.monotonic()
    with _user_cache_lock:
        hit = _user_cache.get(key)
        if hit and hit[0] > now:
            return dict(hit[1])

    headers = {"apikey": _service_key(), "Authorization": f"Bearer {token}"}
    resp = _request("GET", "/user", headers=headers)
    if resp.status_code != 200:
        return None
    user = resp.json() or {}
    email = (user.get("email") or "").lower()
    if not user.get("id") or not email:
        return None
    payload = {"sub": user["id"], "email": email, "auth_user_id": user["id"]}

    with _user_cache_lock:
        if len(_user_cache) >= _USER_CACHE_MAX:
            for k in [k for k, v in _user_cache.items() if v[0] <= now] or list(_user_cache)[: _USER_CACHE_MAX // 2]:
                _user_cache.pop(k, None)
        _user_cache[key] = (now + _USER_CACHE_TTL_SECONDS, payload)
    return dict(payload)
