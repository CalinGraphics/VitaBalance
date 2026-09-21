"""Rate limit: fereastra e per client real, nu per proxy (Vercel → Render adaugă X-Forwarded-For)."""
import unittest

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from fastapi.testclient import TestClient

from middleware.rate_limit import RateLimitMiddleware, _client_ip


def _build_client(max_per_window: int = 2) -> TestClient:
    async def ok(_request):
        return JSONResponse({"ok": True})

    app = Starlette(routes=[Route("/api/auth/login", ok, methods=["POST"])])
    app.add_middleware(
        RateLimitMiddleware,
        enabled=True,
        auth_max_per_window=max_per_window,
        recommendations_max_per_window=max_per_window,
    )
    return TestClient(app)


class ClientIpTests(unittest.TestCase):
    def test_prefers_first_forwarded_for_entry(self):
        class Req:
            headers = {"x-forwarded-for": "203.0.113.7, 70.0.0.1, 10.0.0.2"}
            client = type("C", (), {"host": "10.0.0.2"})()

        self.assertEqual(_client_ip(Req()), "203.0.113.7")

    def test_falls_back_to_socket_address(self):
        class Req:
            headers = {}
            client = type("C", (), {"host": "10.0.0.2"})()

        self.assertEqual(_client_ip(Req()), "10.0.0.2")


class RateLimitWindowTests(unittest.TestCase):
    def setUp(self):
        RateLimitMiddleware._hits.clear()

    def test_limits_each_forwarded_client_separately(self):
        client = _build_client(max_per_window=2)
        for _ in range(2):
            resp = client.post("/api/auth/login", headers={"X-Forwarded-For": "203.0.113.7"})
            self.assertEqual(resp.status_code, 200)

        blocked = client.post("/api/auth/login", headers={"X-Forwarded-For": "203.0.113.7"})
        self.assertEqual(blocked.status_code, 429)

        # Alt utilizator, prin același proxy: nu trebuie afectat de vecinul care a atins limita.
        other = client.post("/api/auth/login", headers={"X-Forwarded-For": "198.51.100.4"})
        self.assertEqual(other.status_code, 200)


if __name__ == "__main__":
    unittest.main()
