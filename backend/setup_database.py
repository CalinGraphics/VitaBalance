"""
Script helper pentru setup-ul bazei de date
Rulează schema SQL și seed data automat
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def setup_database():
    """Rulează schema SQL și seed data"""
    
    # Verifică dacă există DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("⚠️  DATABASE_URL nu este setat în .env")
        print("📝 Aplicația va folosi SQLite local (vitabalance.db)")
        print("\n💡 Pentru PostgreSQL/Supabase:")
        print("   1. Creează fișierul .env în folderul backend/")
        print("   2. Adaugă: DATABASE_URL=postgresql://...")
        print("   3. Rulează din nou acest script")
        return
    
    # Verifică dacă este PostgreSQL
    if not database_url.startswith("postgresql"):
        print("⚠️  DATABASE_URL nu este PostgreSQL")
        print("📝 Pentru SQLite, schema se creează automat la prima rulare")
        return
    
    print(f"🔗 Conectare la: {database_url.split('@')[1] if '@' in database_url else 'database'}")
    
    try:
        # Creează engine
        engine = create_engine(database_url)
        
        # Citește și rulează schema SQL
        print("\n📋 Rulează schema SQL...")
        with open("database_schema.sql", "r", encoding="utf-8") as f:
            schema_sql = f.read()
        
        with engine.connect() as conn:
            # Rulează schema (fiecare statement separat)
            statements = [s.strip() for s in schema_sql.split(";") if s.strip() and not s.strip().startswith("--")]
            for statement in statements:
                if statement:
                    try:
                        conn.execute(text(statement))
                        conn.commit()
                    except Exception as e:
                        # Ignoră erori de tip "already exists"
                        if "already exists" not in str(e).lower():
                            print(f"   ⚠️  {str(e)[:100]}")
        
        print("✅ Schema creată cu succes!")
        
        # Verifică dacă există deja date
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM foods"))
            count = result.scalar()
            
            if count > 0:
                print(f"📊 Baza de date conține deja {count} alimente")
                response = input("   Vrei să adaugi datele din seed_data.sql? (s/n): ")
                if response.lower() != 's':
                    print("⏭️  Sărit seed data")
                    return
        
        # Citește și rulează seed data
        print("\n🌱 Populează cu date inițiale...")
        with open("seed_data.sql", "r", encoding="utf-8") as f:
            seed_sql = f.read()
        
        with engine.connect() as conn:
            statements = [s.strip() for s in seed_sql.split(";") if s.strip() and not s.strip().startswith("--")]
            for statement in statements:
                if statement:
                    try:
                        conn.execute(text(statement))
                        conn.commit()
                    except Exception as e:
                        if "duplicate key" not in str(e).lower() and "already exists" not in str(e).lower():
                            print(f"   ⚠️  {str(e)[:100]}")
        
        print("✅ Date populate cu succes!")
        
        # Verifică rezultatul
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM foods"))
            count = result.scalar()
            print(f"\n📊 Total alimente în baza de date: {count}")
        
        print("\n🎉 Setup complet!")
        print("💡 Poți rula acum: python run.py")
        
    except FileNotFoundError as e:
        print(f"❌ Eroare: Fișierul {e.filename} nu a fost găsit")
        print("   Asigură-te că rulezi scriptul din folderul backend/")
    except Exception as e:
        print(f"❌ Eroare la conectare: {e}")
        print("\n💡 Verifică:")
        print("   1. DATABASE_URL este corect în .env")
        print("   2. Baza de date există și este accesibilă")
        print("   3. Credențialele sunt corecte")

if __name__ == "__main__":
    setup_database()

