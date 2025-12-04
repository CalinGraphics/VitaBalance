"""
Script simplu pentru a testa conexiunea la baza de date PostgreSQL / Supabase

Rulează-l din folderul `backend`:

    python test_db_connection.py
"""

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


def main() -> None:
    # Încarcă explicit `.env` din folderul backend (același cu acest fișier)
    backend_dir = Path(__file__).resolve().parent
    env_path = backend_dir / ".env"

    if not env_path.exists():
        print(f"❌ Fișierul .env nu există în: {env_path}")
        print("   Creează-l în folderul `backend/` cu linia DATABASE_URL=...")
        return

    # override=True ca să înlocuiască orice DATABASE_URL vechi din sesiune
    load_dotenv(dotenv_path=env_path, override=True)

    print(f"ℹ️  Citim variabilele din: {env_path}")

    # În proiectul tău folosim o singură variabilă: DATABASE_URL
    raw_value = os.environ.get("DATABASE_URL")
    print(f"ℹ️  Valoare brută DATABASE_URL din env: {repr(raw_value)}")

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ DATABASE_URL nu este setat în .env")
        print("   Deschide `.env` în folderul `backend/` și setează DATABASE_URL de la Supabase.")
        return

    try:
        # Conectare directă cu psycopg2 folosind DATABASE_URL
        connection = psycopg2.connect(database_url)
        print("✅ Conexiune reușită la baza de date!")

        cursor = connection.cursor()
        cursor.execute("SELECT NOW();")
        result = cursor.fetchone()
        print("⏱️  Ora curentă în baza de date:", result[0])

        cursor.close()
        connection.close()
        print("🔌 Conexiune închisă.")

    except Exception as e:
        print(f"❌ Eroare la conectare: {e}")
        print("   Verifică că DATABASE_URL este corect și baza de date este online.")


if __name__ == "__main__":
    main()


