"""
Poza de profil: validarea imaginii primite de la client și legarea ei de profil.

Frontend-ul micșorează imaginea în browser (256 × 256) și o trimite ca data URL. Aici verificăm tipul
real după conținut (nu după ce declară clientul), mărimea, și înlocuim poza veche.
"""
import base64
import binascii
import uuid
from typing import Optional, Tuple

from domain.models import UserProfile
from repositories import UserRepository
from repositories import avatar_storage

MAX_AVATAR_BYTES = 2 * 1024 * 1024  # aceeași limită ca bucket-ul (migrarea 010)
# Un data URL base64 e cu ~4/3 mai lung decât fișierul; respingem din start textele vădit prea mari.
MAX_DATA_URL_CHARS = MAX_AVATAR_BYTES * 4 // 3 + 128

_EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


class AvatarError(ValueError):
    """Imagine respinsă; mesajul ajunge la utilizator."""


def detect_image_type(data: bytes) -> Optional[str]:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def decode_image(image: str) -> Tuple[bytes, str]:
    """Data URL (sau base64 simplu) -> (octeți, tip MIME). Ridică AvatarError dacă nu e o imagine acceptată."""
    if not image or len(image) > MAX_DATA_URL_CHARS:
        raise AvatarError("Imaginea lipsește sau este prea mare (maxim 2 MB)")
    payload = image.split(",", 1)[1] if image.startswith("data:") else image
    try:
        data = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AvatarError("Imaginea nu a putut fi citită") from exc
    if not data or len(data) > MAX_AVATAR_BYTES:
        raise AvatarError("Imaginea lipsește sau este prea mare (maxim 2 MB)")
    content_type = detect_image_type(data)
    if content_type is None:
        raise AvatarError("Formatul imaginii nu este acceptat (folosește JPG, PNG sau WebP)")
    return data, content_type


def set_avatar(profile: UserProfile, image: str, repo: Optional[UserRepository] = None) -> Optional[str]:
    """Salvează poza nouă, o leagă de profil, șterge poza veche și întoarce un link semnat."""
    data, content_type = decode_image(image)
    # Nume nou la fiecare schimbare: browserul nu mai poate afișa poza veche din cache.
    path = f"{profile.id}/{uuid.uuid4().hex}.{_EXTENSIONS[content_type]}"
    avatar_storage.upload(path, data, content_type)
    (repo or UserRepository()).set_avatar_path(profile.id, path)
    if profile.avatar_path and profile.avatar_path != path:
        avatar_storage.remove(profile.avatar_path)
    return avatar_storage.signed_url(path)


def remove_avatar(profile: UserProfile, repo: Optional[UserRepository] = None) -> None:
    if not profile.avatar_path:
        return
    (repo or UserRepository()).set_avatar_path(profile.id, None)
    avatar_storage.remove(profile.avatar_path)
