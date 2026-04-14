"""
Configurație aplicație folosind Pydantic Settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import os
from dotenv import load_dotenv

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

    # Food intelligence API (OpenFoodFacts) – opțional, pentru reducerea hardcodării la alergeni ascunși
    openfoodfacts_enabled: bool = os.getenv("OPENFOODFACTS_ENABLED", "true").lower() in ("1", "true", "yes")
    openfoodfacts_timeout_seconds: float = float(os.getenv("OPENFOODFACTS_TIMEOUT_SECONDS", "1.2"))
    
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


# Instanță globală de settings
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Obține instanța de settings (singleton)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

