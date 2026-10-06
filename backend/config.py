"""Setări aplicație (Pydantic Settings)."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import base64
import json
import os
from dotenv import load_dotenv


def normalize_supabase_api_key(key: Optional[str]) -> Optional[str]:
    if not key:
        return None
    s = key.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        s = s[1:-1].strip()
    if s.lower().startswith("bearer "):
        s = s[7:].strip()
    return s or None


def _supabase_key_role(supabase_key: str) -> Optional[str]:
    try:
        parts = (supabase_key or "").strip().split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1]
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        role = payload.get("role")
        return str(role) if role is not None else None
    except Exception:
        return None


load_dotenv()


class Settings(BaseSettings):
    app_name: str = os.getenv("APP_NAME", "VitaBalance API")
    debug: bool = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")

    supabase_url: Optional[str] = os.getenv("SUPABASE_URL")
    supabase_key: Optional[str] = os.getenv("SUPABASE_KEY")
    supabase_service_role_key: Optional[str] = None

    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
    cors_allow_all: bool = os.getenv("CORS_ALLOW_ALL", "false").lower() in ("1", "true", "yes")

    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in ("1", "true", "yes")
    rate_limit_auth_per_min: int = int(os.getenv("RATE_LIMIT_AUTH_PER_MIN", "24"))
    rate_limit_recommendations_per_min: int = int(os.getenv("RATE_LIMIT_RECOMMENDATIONS_PER_MIN", "45"))
    # Câte proxy-uri adaugă un element în X-Forwarded-For înainte să ajungă cererea la aplicație.
    # Implicit 2 = rewrite Vercel + proxy Render; 1 dacă backend-ul e expus direct.
    rate_limit_trusted_proxy_hops: int = int(os.getenv("RATE_LIMIT_TRUSTED_PROXY_HOPS", "2"))

    openfoodfacts_enabled: bool = os.getenv("OPENFOODFACTS_ENABLED", "true").lower() in ("1", "true", "yes")
    openfoodfacts_timeout_seconds: float = float(os.getenv("OPENFOODFACTS_TIMEOUT_SECONDS", "0.35"))
    openfoodfacts_blocking_mode: bool = os.getenv("OPENFOODFACTS_BLOCKING_MODE", "false").lower() in (
        "1",
        "true",
        "yes",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_cors_origins_list(self) -> List[str]:
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return self.cors_origins if isinstance(self.cors_origins, list) else ["http://localhost:3000", "http://localhost:5173"]

    def effective_supabase_secret_key(self) -> Optional[str]:
        explicit = normalize_supabase_api_key(self.supabase_service_role_key)
        if explicit:
            return explicit
        return normalize_supabase_api_key(self.supabase_key)

    def validate_runtime(self) -> None:
        if self.supabase_url:
            secret = self.effective_supabase_secret_key()
            if secret:
                role = _supabase_key_role(secret)
                if role == "anon":
                    # Rolul anon nu are drepturi pe tabele, iar crearea conturilor (Supabase Auth admin)
                    # cere service_role: cu cheia anon înregistrarea, loginul și profilul ar răspunde 500
                    # fără nicio indicație despre cauză. Mai bine oprim pornirea cu mesajul corect.
                    raise ValueError(
                        "Cheia Supabase este `anon`, dar backend-ul are nevoie de `service_role` "
                        "(RLS activ, fără politici). Pune cheia service_role în SUPABASE_SERVICE_ROLE_KEY."
                    )
                elif role and role not in ("service_role",):
                    print(f"[Config] Rol JWT neașteptat: {role} (așteptat service_role).")


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        sr = normalize_supabase_api_key(os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
        if sr and not (normalize_supabase_api_key(_settings.supabase_service_role_key) or "").strip():
            _settings.supabase_service_role_key = sr
        _settings.validate_runtime()
    return _settings
