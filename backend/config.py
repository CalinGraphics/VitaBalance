"""
Configurație aplicație folosind Pydantic Settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import base64
import json
import os
from dotenv import load_dotenv


def _supabase_key_role(supabase_key: str) -> Optional[str]:
    """Citește claim-ul `role` din JWT-ul Supabase (fără verificare semnătură — doar diagnostic)."""
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

# Încarcă variabilele de mediu din .env
load_dotenv()


class Settings(BaseSettings):
    """Settings pentru aplicație"""
    
    # App metadata
    app_name: str = os.getenv("APP_NAME", "VitaBalance API")
    debug: bool = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")
    
    # Supabase Configuration (singura sursă de date)
    supabase_url: Optional[str] = os.getenv("SUPABASE_URL")
    supabase_key: Optional[str] = os.getenv("SUPABASE_KEY")
    
    # Auth: JWT + Magic Link
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-production-use-long-random-string")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
    magic_link_expire_hours: int = int(os.getenv("MAGIC_LINK_EXPIRE_HOURS", "24"))
    
    # Email (Resend) – opțional; fără RESEND_* magic link-ul apare doar în consolă (dev)
    resend_api_key: Optional[str] = os.getenv("RESEND_API_KEY")
    resend_from_email: str = os.getenv("RESEND_FROM_EMAIL", "VitaBalance <onboarding@resend.dev>")
    # Opțional: în modul de test Resend permite trimiterea doar către o singură adresă
    # (de obicei adresa ta de cont). Dacă setezi RESEND_TEST_RECIPIENT, toate emailurile
    # de autentificare vor fi trimise către această adresă, indiferent ce introduce
    # utilizatorul în formular (tokenul rămâne generat pentru emailul introdus).
    resend_test_recipient: Optional[str] = os.getenv("RESEND_TEST_RECIPIENT")
    # URL-ul frontend-ului – linkul magic trimite utilizatorul aici. Pentru dev local: http://localhost:3000
    frontend_base_url: str = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
    
    # CORS Origins (poate fi string separată prin virgulă sau listă)
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
    # Dacă true, permite orice origin (doar dev / depanare). În producție lasă false.
    cors_allow_all: bool = os.getenv("CORS_ALLOW_ALL", "false").lower() in ("1", "true", "yes")

    # Rate limit în memorie (per proces) — dezactivează cu RATE_LIMIT_ENABLED=false
    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in ("1", "true", "yes")
    rate_limit_auth_per_min: int = int(os.getenv("RATE_LIMIT_AUTH_PER_MIN", "24"))
    rate_limit_recommendations_per_min: int = int(os.getenv("RATE_LIMIT_RECOMMENDATIONS_PER_MIN", "45"))

    # Food intelligence API (OpenFoodFacts) – opțional, pentru reducerea hardcodării la alergeni ascunși
    # Activ implicit: rulare continuă cu strategie non-blocantă + cache în memorie.
    openfoodfacts_enabled: bool = os.getenv("OPENFOODFACTS_ENABLED", "true").lower() in ("1", "true", "yes")
    openfoodfacts_timeout_seconds: float = float(os.getenv("OPENFOODFACTS_TIMEOUT_SECONDS", "0.35"))
    # False (default): dacă nu e în cache, pornim fetch în background și nu blocăm request-ul.
    # True: fetch sincron (poate crește latența).
    openfoodfacts_blocking_mode: bool = os.getenv("OPENFOODFACTS_BLOCKING_MODE", "false").lower() in ("1", "true", "yes")
    
    # Configurație Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignoră variabilele de mediu care nu sunt definite în clasă
    )
    
    def get_cors_origins_list(self) -> List[str]:
        """Convertește CORS_ORIGINS string în listă"""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return self.cors_origins if isinstance(self.cors_origins, list) else ["http://localhost:3000", "http://localhost:5173"]

    def validate_runtime(self) -> None:
        """Validări minime pentru a evita erori de auth/config greu de diagnosticat."""
        if not self.jwt_secret or not self.jwt_secret.strip():
            raise ValueError("JWT_SECRET este obligatoriu.")
        if len(self.jwt_secret.strip()) < 24:
            raise ValueError("JWT_SECRET este prea scurt. Folosește un secret lung (minim 24 caractere).")
        if self.jwt_expire_minutes <= 0:
            raise ValueError("JWT_EXPIRE_MINUTES trebuie să fie > 0.")

        base = (self.frontend_base_url or "").strip()
        if not base:
            raise ValueError("FRONTEND_BASE_URL este obligatoriu pentru magic link.")
        if not (base.startswith("http://") or base.startswith("https://")):
            raise ValueError("FRONTEND_BASE_URL trebuie să înceapă cu http:// sau https://.")
        if "localhost" in base and not self.debug:
            print(
                "[Config] WARNING: FRONTEND_BASE_URL conține localhost în mod non-debug. "
                "Magic link-urile pot eșua în producție."
            )
        if self.jwt_secret == "change-me-in-production-use-long-random-string":
            print(
                "[Config] WARNING: JWT_SECRET este pe valoarea implicită. "
                "Setează un secret dedicat per mediu."
            )

        if self.supabase_url and self.supabase_key:
            role = _supabase_key_role(self.supabase_key)
            if role == "anon":
                raise ValueError(
                    "SUPABASE_KEY folosește rolul «anon» — RLS din Supabase blochează INSERT/UPDATE "
                    "(ex.: tabela magic_links, 42501). Pe server folosește cheia «service_role» "
                    "(Project Settings → API → service_role secret). Nu expune această cheie în "
                    "frontend sau în repo; rămâne doar în variabilele de mediu ale backend-ului."
                )
            if role and role not in ("service_role",):
                print(
                    f"[Config] WARNING: SUPABASE_KEY are rol JWT «{role}». "
                    "Backend-ul VitaBalance presupune «service_role» pentru a ocoli RLS pe tabele interne."
                )


# Instanță globală de settings
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Obține instanța de settings (singleton)"""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.validate_runtime()
    return _settings

