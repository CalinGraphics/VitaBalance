"""Poza de profil (validare, înlocuire, ștergere) și păstrarea numelui de la înregistrare."""
import base64
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import main as main_module
from domain.models import UserProfile
from services import profile_avatar

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 32
WEBP = b"RIFF\x24\x00\x00\x00WEBPVP8 " + b"\x00" * 32
GIF = b"GIF89a" + b"\x00" * 32


def data_url(raw: bytes, mime: str = "image/png") -> str:
    return f"data:{mime};base64," + base64.b64encode(raw).decode()


def profile(**overrides) -> UserProfile:
    base = dict(
        id=42, email="ana@example.com", name="Ana Pop", age=30, sex="F", weight=60.0, height=165.0,
        activity_level="moderate", diet_type="omnivore", created_at=datetime.now(timezone.utc),
    )
    base.update(overrides)
    return UserProfile(**base)


class DecodeImageTests(unittest.TestCase):
    def test_accepts_png_jpeg_webp_by_content(self):
        for raw, mime in [(PNG, "image/png"), (JPEG, "image/jpeg"), (WEBP, "image/webp")]:
            data, content_type = profile_avatar.decode_image(data_url(raw, "image/png"))
            self.assertEqual(data, raw)
            self.assertEqual(content_type, mime)  # tipul real, nu cel declarat în data URL

    def test_rejects_other_formats_and_garbage(self):
        for bad in [data_url(GIF, "image/gif"), "data:image/png;base64,@@@", "", "nu-e-base64!"]:
            with self.assertRaises(profile_avatar.AvatarError):
                profile_avatar.decode_image(bad)

    def test_rejects_images_over_2_mb(self):
        big = PNG + b"\x00" * (profile_avatar.MAX_AVATAR_BYTES + 1)
        with self.assertRaises(profile_avatar.AvatarError):
            profile_avatar.decode_image(data_url(big))


class SetAvatarTests(unittest.TestCase):
    def setUp(self):
        self.storage = patch.object(profile_avatar, "avatar_storage").start()
        self.storage.signed_url.side_effect = lambda path: f"https://signed/{path}"
        self.addCleanup(patch.stopall)
        self.repo = MagicMock()

    def test_upload_links_new_photo_and_removes_old_one(self):
        url = profile_avatar.set_avatar(profile(avatar_path="42/old.png"), data_url(WEBP), repo=self.repo)

        path, data, content_type = self.storage.upload.call_args.args
        self.assertTrue(path.startswith("42/") and path.endswith(".webp"))
        self.assertEqual((data, content_type), (WEBP, "image/webp"))
        self.repo.set_avatar_path.assert_called_once_with(42, path)
        self.storage.remove.assert_called_once_with("42/old.png")
        self.assertEqual(url, f"https://signed/{path}")

    def test_invalid_image_touches_nothing(self):
        with self.assertRaises(profile_avatar.AvatarError):
            profile_avatar.set_avatar(profile(), data_url(GIF), repo=self.repo)
        self.storage.upload.assert_not_called()
        self.repo.set_avatar_path.assert_not_called()

    def test_remove_clears_path_and_file(self):
        profile_avatar.remove_avatar(profile(avatar_path="42/a.png"), repo=self.repo)
        self.repo.set_avatar_path.assert_called_once_with(42, None)
        self.storage.remove.assert_called_once_with("42/a.png")


class ProfileRouteTests(unittest.TestCase):
    """POST /api/profile cu numele gol nu trebuie să șteargă numele salvat la înregistrare."""

    def setUp(self):
        self.repo = MagicMock()
        self.repo.get_by_email.return_value = profile(age=0, weight=0, height=0)
        self.repo.upsert.side_effect = lambda email, **kw: profile(name=kw["name"])
        patch.object(main_module, "UserRepository", return_value=self.repo).start()
        patch.object(main_module.avatar_storage, "signed_url", return_value=None).start()
        self.addCleanup(patch.stopall)
        main_module.app.dependency_overrides[main_module.get_current_user] = lambda: {"email": "ana@example.com"}
        self.addCleanup(main_module.app.dependency_overrides.clear)
        self.client = TestClient(main_module.app)

    def post_profile(self, name):
        body = {
            "email": "ana@example.com", "name": name, "age": 30, "sex": "F", "weight": 60, "height": 165,
            "activity_level": "moderate", "diet_type": "omnivore",
        }
        return self.client.post("/api/profile", json=body)

    def test_blank_name_keeps_signup_name(self):
        response = self.post_profile("   ")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.repo.upsert.call_args.kwargs["name"], "Ana Pop")
        self.assertEqual(response.json()["name"], "Ana Pop")

    def test_new_name_is_saved_trimmed(self):
        self.post_profile("  Ana Maria Pop ")
        self.assertEqual(self.repo.upsert.call_args.kwargs["name"], "Ana Maria Pop")

    def test_avatar_route_rejects_invalid_image(self):
        response = self.client.post("/api/profile/avatar", json={"image": data_url(GIF, "image/gif")})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
