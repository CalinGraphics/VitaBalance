"""
Seed data: folosește doar Supabase.
- Alimente: rulează scripts/generate_foods.py (--clear opțional).
- Schema: creează tabelele din Supabase Dashboard sau din SQL-ul din docs.
"""

def main():
    print("Pentru a popula alimentele, rulează: python scripts/generate_foods.py")
    print("Asigură-te că SUPABASE_URL și SUPABASE_KEY sunt setate în .env")


if __name__ == "__main__":
    main()
