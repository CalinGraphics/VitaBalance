"""Headerele de securitate apar pe orice răspuns al API-ului, inclusiv pe erori."""
import unittest

from fastapi.testclient import TestClient

import main as main_module


class SecurityHeadersTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main_module.app)

    def assert_security_headers(self, response):
        self.assertEqual(response.headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(response.headers.get("x-frame-options"), "DENY")
        self.assertEqual(response.headers.get("referrer-policy"), "no-referrer")

    def test_headers_on_success(self):
        self.assert_security_headers(self.client.get("/"))

    def test_headers_on_auth_error(self):
        response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, 401)
        self.assert_security_headers(response)


if __name__ == "__main__":
    unittest.main()
