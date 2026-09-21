"""Setări de test: testele nu depind de .env-ul local și nu ating Supabase."""
import os

# config.py refuză secretul JWT implicit când DEBUG nu e true; testele își definesc propriul secret.
os.environ.setdefault("JWT_SECRET", "test-only-secret-not-used-outside-pytest-0123456789")
