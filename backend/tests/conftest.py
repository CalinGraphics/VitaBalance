"""Setări de test: testele nu depind de .env-ul local și nu ating Supabase."""
import pytest


class FakeCheckinRepository:
    """Jurnal de stare în memorie; testele care au nevoie de check-in-uri setează `rows`."""

    rows: list = []

    def list_for_user(self, user_id, limit=120):
        return [r for r in self.rows if r.user_id == user_id][:limit]

    def is_available(self):
        return True


@pytest.fixture(autouse=True)
def _no_network_checkins(monkeypatch):
    import main
    from services.recommendations import materialize

    FakeCheckinRepository.rows = []
    monkeypatch.setattr(materialize, "CheckinRepository", FakeCheckinRepository)
    monkeypatch.setattr(main, "CheckinRepository", FakeCheckinRepository, raising=False)
    yield
