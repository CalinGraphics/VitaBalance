"""
Testează conexiunea la Supabase (singura sursă de date).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent
load_dotenv(dotenv_path=backend_dir / ".env", override=True)


def main() -> None:
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("SUPABASE_URL și SUPABASE_KEY trebuie setate în .env (backend/)")
        return
    try:
        from supabase_client import get_supabase_client
        client = get_supabase_client()
        r = client.table("foods").select("id", count="exact").limit(1).execute()
        print("Conexiune la Supabase reușită.")
        print("Count foods (sample):", getattr(r, "count", "N/A"))
    except Exception as e:
        print("Eroare la conectare Supabase:", e)


if __name__ == "__main__":
    main()
