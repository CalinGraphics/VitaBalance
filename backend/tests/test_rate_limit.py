"""Rate limit: fereastra e per client real, nu per proxy (Vercel → Render adaugă X-Forwarded-For)."""
import unittest

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from fastapi.testclient import TestClient

from middleware.rate_limit import RateLimitMiddleware, _client_ip


def _build_client(max_per_window: int = 2, trusted_proxy_hops: int = 1) -> TestClient:
    async def ok(_request):
        return JSONResponse({"ok": True})

    app = Starlette(routes=[Route("/api/auth/login", ok, methods=["POST"])])
    app.add_middleware(
        RateLimitMiddleware,
        enabled=True,
        auth_max_per_window=max_per_window,
        recommendations_max_per_window=max_per_window,
        trusted_proxy_hops=trusted_proxy_hops,
    )
    return TestClient(app)


def _req(forwarded=None, host="10.0.0.2"):
    class Req:
        headers = {"x-forwarded-for": forwarded} if forwarded else {}
        client = type("C", (), {"host": host})()

    return Req()


class ClientIpTests(unittest.TestCase):
    def test_counts_back_through_the_trusted_proxies(self):
        """Vercel pune clientul, Render adaugă IP-ul Vercel: clientul e al doilea de la coadă."""
        self.assertEqual(_client_ip(_req("203.0.113.7, 76.76.21.1"), 2), "203.0.113.7")

    def test_ignores_a_value_the_client_tried_to_inject(self):
        """Antetul falsificat rămâne în stânga lanțului, deci nu ajunge în poziția de încredere."""
        chain = "1.2.3.4, 203.0.113.7, 76.76.21.1"
        self.assertEqual(_client_ip(_req(chain), 2), "203.0.113.7")

    def test_uses_the_only_entry_when_the_chain_is_shorter(self):
        self.assertEqual(_client_ip(_req("203.0.113.7"), 2), "203.0.113.7")

    def test_falls_back_to_socket_address(self):
        self.assertEqual(_client_ip(_req()), "10.0.0.2")


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
