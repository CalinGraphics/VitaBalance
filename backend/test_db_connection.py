import os
from pathlib import Path

import psycopg  # psycopg v3 (binary), compatibil cu Python 3.13
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

    print(f"[INFO] Citim variabilele din: {env_path}")

    # În proiectul tău folosim o singură variabilă: DATABASE_URL
    raw_value = os.environ.get("DATABASE_URL")
    print(f"[INFO] Valoare bruta DATABASE_URL din env: {repr(raw_value)}")

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("[ERROR] DATABASE_URL nu este setat in .env")
        print("   Deschide `.env` in folderul `backend/` si seteaza DATABASE_URL de la Supabase.")
        return

    try:
        # Conectare directă cu psycopg (v3) folosind DATABASE_URL
        # Acceptă direct URL de forma postgresql://user:pass@host:port/db?sslmode=require
        connection = psycopg.connect(database_url)
        print("[OK] Conexiune reușită la baza de date!")

        cursor = connection.cursor()
        cursor.execute("SELECT NOW();")
        result = cursor.fetchone()
        print("[INFO] Ora curentă în baza de date:", result[0])

        cursor.close()
        connection.close()
        print("[INFO] Conexiune închisă.")

    except Exception as e:
        print(f"❌ Eroare la conectare: {e}")
        print("   Verifică că DATABASE_URL este corect și baza de date este online.")


if __name__ == "__main__":
    main()