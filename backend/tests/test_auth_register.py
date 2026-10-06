"""Autentificare prin Supabase Auth: înregistrare, login, profile vechi și validarea tokenului."""
import unittest
from unittest.mock import patch

import httpx

from services import auth as auth_module


class FakeSupabaseAuth:
    """Imită API-ul GoTrue (`/auth/v1/...`) și triggerul care leagă profilul din public.users."""

    def __init__(self, profiles):
        self.profiles = profiles  # email -> rând public.users
        self.accounts = {}  # email -> {"id", "password", "full_name"}
        self.tokens = {}  # access_token -> email
        self._seq = 0

    def _json(self, status, body):
        return httpx.Response(status, json=body, request=httpx.Request("POST", "http://test"))

    def _session(self, email):
        self._seq += 1
        token = f"access-{self._seq}"
        self.tokens[token] = email
        acc = self.accounts[email]
        return {
            "access_token": token,
            "refresh_token": f"refresh-{email}",
            "expires_in": 3600,
            "expires_at": 1_900_000_000,
            "user": {"id": acc["id"], "email": email, "user_metadata": {"full_name": acc["full_name"]}},
        }

    def request(self, method, path, *, json=None, headers=None):
        if path == "/token?grant_type=password":
            acc = self.accounts.get(json["email"])
            if not acc or acc["password"] != json["password"]:
                return self._json(400, {"error_code": "invalid_credentials", "msg": "Invalid login credentials"})
            return self._json(200, self._session(json["email"]))
        if path == "/token?grant_type=refresh_token":
            email = json["refresh_token"].removeprefix("refresh-")
            if email not in self.accounts:
                return self._json(400, {"error_code": "refresh_token_not_found"})
            return self._json(200, self._session(email))
        if path == "/admin/users":
            email = json["email"]
            if email in self.accounts:
                return self._json(422, {"error_code": "email_exists", "msg": "A user with this email address has already been registered"})
            # Triggerul on_auth_user_created (migrarea 009): creează profilul sau preia unul vechi aprobat;
            # un profil vechi neaprobat face să eșueze crearea contului.
            row = self.profiles.get(email)
            if row is not None and not row.get("legacy_adoption_approved_at"):
                return self._json(500, {"error_code": "unexpected_failure", "msg": "Database error creating new user"})
            self.accounts[email] = {
                "id": f"uuid-{email}",
                "password": json["password"],
                "full_name": json["user_metadata"]["full_name"],
            }
            if row is None:
                self.profiles[email] = {"id": len(self.profiles) + 1, "name": json["user_metadata"]["full_name"], "auth_user_id": f"uuid-{email}"}
            else:
                row["auth_user_id"] = f"uuid-{email}"
                row["name"] = row.get("name") or json["user_metadata"]["full_name"]
            return self._json(200, {"id": f"uuid-{email}", "email": email})
        if path == "/user":
            token = headers["Authorization"].removeprefix("Bearer ")
            email = self.tokens.get(token)
            if not email:
                return self._json(401, {"msg": "invalid JWT"})
            return self._json(200, {"id": self.accounts[email]["id"], "email": email})
        if path == "/logout":
            self.tokens.pop(headers["Authorization"].removeprefix("Bearer "), None)
            return self._json(204, {})
        raise AssertionError(f"rută neașteptată: {method} {path}")


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeSupabaseAuth(
            {
                # profile vechi fără cont (fost magic link): blocat, respectiv aprobat de admin
                "vechi@example.com": {"id": 7, "name": "Vechi", "auth_user_id": None, "legacy_adoption_approved_at": None},
                "aprobat@example.com": {
                    "id": 9,
                    "name": "Aprobat",
                    "auth_user_id": None,
                    "legacy_adoption_approved_at": "2026-10-06T00:00:00Z",
                },
            }
        )
        auth_module._user_cache.clear()
        patches = [
            patch.object(auth_module, "_request", side_effect=self.fake.request),
            patch.object(auth_module, "_profile_row", side_effect=lambda email: self.fake.profiles.get(email)),
            patch.object(auth_module, "_service_key", return_value="service-key"),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def test_register_new_account_returns_session(self):
        session = auth_module.sign_up("Nou@Example.COM", "parola-mea", "Ion Popescu")
        self.assertEqual(session["email"], "nou@example.com")
        self.assertEqual(session["fullName"], "Ion Popescu")
        self.assertTrue(session["access_token"])
        self.assertTrue(session["refresh_token"])
        self.assertIn("nou@example.com", self.fake.profiles)

    def test_register_existing_account_is_rejected(self):
        auth_module.sign_up("a@example.com", "prima-parola", "Primul")
        with self.assertRaises(auth_module.AuthError) as ctx:
            auth_module.sign_up("a@example.com", "a-doua-parola", "Al Doilea")
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.detail, "Acest email este deja înregistrat")

    def test_register_on_unapproved_legacy_profile_is_blocked(self):
        with self.assertRaises(auth_module.AuthError) as ctx:
            auth_module.sign_up("vechi@example.com", "parola-noua", "Intrus")
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("profil vechi", ctx.exception.detail)
        self.assertIsNone(self.fake.profiles["vechi@example.com"]["auth_user_id"])
        self.assertNotIn("vechi@example.com", self.fake.accounts)

    def test_register_adopts_approved_legacy_profile(self):
        session = auth_module.sign_up("aprobat@example.com", "parola-noua", "Nume Nou")
        self.assertEqual(self.fake.profiles["aprobat@example.com"]["id"], 9)
        self.assertEqual(self.fake.profiles["aprobat@example.com"]["auth_user_id"], "uuid-aprobat@example.com")
        # numele existent al profilului are prioritate
        self.assertEqual(session["fullName"], "Aprobat")

    def test_register_validates_input(self):
        for args in [("", "parola-mea", "Nume"), ("x@example.com", "12345", "Nume"), ("x@example.com", "parola", " ")]:
            with self.assertRaises(auth_module.AuthError) as ctx:
                auth_module.sign_up(*args)
            self.assertEqual(ctx.exception.status_code, 400)

    def test_login_with_correct_and_wrong_password(self):
        auth_module.sign_up("b@example.com", "parola-buna", "B")
        session = auth_module.sign_in("B@example.com ", "parola-buna")
        self.assertEqual(session["email"], "b@example.com")
        with self.assertRaises(auth_module.AuthError) as ctx:
            auth_module.sign_in("b@example.com", "gresita")
        self.assertEqual(ctx.exception.status_code, 401)

    def test_passwordless_profile_cannot_login(self):
        with self.assertRaises(auth_module.AuthError) as ctx:
            auth_module.sign_in("vechi@example.com", "orice")
        self.assertEqual(ctx.exception.status_code, 401)

    def test_verify_token_refresh_and_logout(self):
        session = auth_module.sign_up("c@example.com", "parola-c", "C")
        identity = auth_module.verify_access_token(session["access_token"])
        self.assertEqual(identity["email"], "c@example.com")
        self.assertEqual(identity["sub"], "uuid-c@example.com")
        self.assertIsNone(auth_module.verify_access_token("token-inventat"))

        refreshed = auth_module.refresh_session(session["refresh_token"])
        self.assertNotEqual(refreshed["access_token"], session["access_token"])
        with self.assertRaises(auth_module.AuthError):
            auth_module.refresh_session("refresh-nimeni@example.com")

        auth_module.sign_out(refreshed["access_token"])
        self.assertIsNone(auth_module.verify_access_token(refreshed["access_token"]))


if __name__ == "__main__":
    unittest.main()
