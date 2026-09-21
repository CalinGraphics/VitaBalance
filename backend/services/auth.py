"""
Serviciu de autentificare: email + parolă (bcrypt) și sesiune JWT.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path
import bcrypt
from passlib.context import CryptContext

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from supabase_client import get_supabase_client
from supabase import Client
from config import get_settings
from jose import JWTError, jwt

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__ident="2b"  # Folosim identitatea bcrypt 2b
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        plain_password = password_bytes.decode('utf-8', errors='replace')
    
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        error_str = str(e).lower()
        if "72" in error_str and "bytes" in error_str:
            password_bytes = plain_password.encode('utf-8')[:72]
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        try:
            password_bytes = plain_password.encode('utf-8')[:72]
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except:
            raise


def get_password_hash(password: str) -> str:
    """
    Generează hash pentru parolă
    Bcrypt acceptă maxim 72 bytes - trunchează automat
    """
    if not password:
        raise ValueError("Parola nu poate fi goală")
    
    # TRUNCHEAZĂ PAROLA LA 72 BYTES ÎNAINTE DE HASH
    # Convertim la bytes, trunchem dacă este necesar
    # IMPORTANT: Trebuie să trunchiem ÎNAINTE de a apela pwd_context.hash()
    # pentru a evita eroarea "password cannot be longer than 72 bytes"
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        password = password_bytes.decode('utf-8', errors='replace')
    
    # Hash - parola este garantat <= 72 bytes
    # Folosim bcrypt direct ca fallback dacă passlib aruncă eroare
    try:
        return pwd_context.hash(password)
    except (ValueError, Exception) as e:
        error_str = str(e).lower()
        # Dacă eroarea este despre 72 bytes, folosim bcrypt direct
        if "72" in error_str and "bytes" in error_str:
            # Folosim bcrypt direct pentru a evita validarea passlib
            password_bytes = password.encode('utf-8')[:72]
            hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
            return hashed.decode('utf-8')
        # Pentru alte erori, le propagăm
        raise ValueError(f"Eroare la hash-uirea parolei: {str(e)}")


def authenticate_user(email: str, password: str) -> Optional[Dict]:
    """
    Autentifică un utilizator folosind Supabase
    
    Returns:
        Dict cu informațiile utilizatorului dacă autentificarea reușește, None altfel
    """
    try:
        supabase: Client = get_supabase_client()
        
        # Emailurile sunt stocate cu litere mici (vezi create_user și indexul users_email_lower_key)
        response = supabase.table('users').select('*').eq('email', email.strip().lower()).execute()
        
        if not response.data or len(response.data) == 0:
            return None
        
        user = response.data[0]
        
        # Verifică dacă utilizatorul are parolă hash-uită
        if not user.get('password_hash'):
            return None
        
        # Verifică parola
        if verify_password(password, user['password_hash']):
            return {
                "email": user.get('email'),
                "fullName": user.get('name') or "",
            }
        
        return None
    except Exception as e:
        print(f"Eroare la autentificare: {e}")
        return None


def _adopt_passwordless_user(
    supabase: Client,
    *,
    user_id: Any,
    email: str,
    password_hash: str,
    fullName: str,
    existing_name: Optional[str],
) -> Dict:
    """Setează parola pe un cont vechi fără `password_hash` (era magic link) și îl returnează."""
    row = {"password_hash": password_hash, "name": fullName or (existing_name or "")}
    # `is_('password_hash', 'null')` păstrează operația idempotentă: dacă între verificare și update
    # altcineva a setat deja o parolă, update-ul nu atinge niciun rând și refuzăm înregistrarea.
    resp = (
        supabase.table('users')
        .update(row)
        .eq('id', user_id)
        .is_('password_hash', 'null')
        .execute()
    )
    if not resp.data or len(resp.data) == 0:
        raise ValueError("Acest email este deja înregistrat")
    updated = resp.data[0]
    return {
        "email": updated.get('email') or email,
        "fullName": updated.get('name') or fullName or (existing_name or ""),
    }


def create_user(email: str, password: str, fullName: str) -> Dict:
    """
    Creează un utilizator nou în Supabase.

    Conturile rămase din perioada magic link nu au `password_hash` (vezi migrarea 002): proprietarul
    lor nu se poate loga (nu are parolă) și nici nu se poate înregistra (emailul e deja în tabel).
    Pentru ele înregistrarea *setează* parola pe rândul existent, deci utilizatorul își păstrează
    profilul, analizele și recomandările. Un cont care are deja parolă rămâne respins.

    Returns:
        Dict cu informațiile utilizatorului creat
    """
    try:
        # Validare input
        if not email or not email.strip():
            raise ValueError("Email-ul este obligatoriu")
        if not password:
            raise ValueError("Parola este obligatorie")
        if not fullName or not fullName.strip():
            raise ValueError("Numele complet este obligatoriu")
        
        supabase: Client = get_supabase_client()
        email = email.strip().lower()
        
        # Verifică dacă email-ul este deja folosit
        existing_row = None
        try:
            existing = supabase.table('users').select('id, password_hash, name').eq('email', email).execute()
            
            if existing.data and len(existing.data) > 0:
                existing_row = existing.data[0]
                if existing_row.get('password_hash'):
                    raise ValueError("Acest email este deja înregistrat")
        except ValueError:
            raise
        except Exception as check_error:
            # Eroare de conexiune la verificare: continuăm cu insert-ul, care are oricum
            # constrângerea de unicitate pe email.
            print(f"Eroare la verificarea email-ului: {check_error}")
        
        # Creează utilizatorul nou
        password_hash = get_password_hash(password)

        if existing_row is not None:
            return _adopt_passwordless_user(
                supabase,
                user_id=existing_row.get('id'),
                email=email,
                password_hash=password_hash,
                fullName=fullName.strip(),
                existing_name=existing_row.get('name'),
            )
        
        new_user_data = {
            "email": email,
            "password_hash": password_hash,
            "name": fullName.strip(),
        }
        
        try:
            response = supabase.table('users').insert(new_user_data).execute()
        except Exception as insert_error:
            error_str = str(insert_error)
            # Verifică dacă eroarea este despre email duplicat
            if "unique" in error_str.lower() or "duplicate" in error_str.lower() or "already exists" in error_str.lower():
                raise ValueError("Acest email este deja înregistrat")
            raise ValueError(f"Eroare la crearea utilizatorului: {error_str}")
        
        if not response.data or len(response.data) == 0:
            raise ValueError("Eroare la crearea utilizatorului - nu s-au returnat date")
        
        created_user = response.data[0]
        email_val = created_user.get('email') or email
        full_name_val = created_user.get('name') or fullName.strip()
        return {
            "email": email_val,
            "fullName": full_name_val,
        }
    except ValueError:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"Eroare la crearea utilizatorului: {error_msg}")
        # Dacă eroarea este deja un ValueError, o propagăm
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Eroare la crearea contului: {error_msg}")


# ---------- JWT (sesiune după login/înregistrare cu parolă) ----------
def create_access_token(data: Dict[str, Any]) -> str:
    """Creează JWT cu email și sub (user id sau email)."""
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode["exp"] = expire
    to_encode["iat"] = datetime.now(timezone.utc)
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verifică JWT și returnează payload (ex.: email, sub) sau None."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None
