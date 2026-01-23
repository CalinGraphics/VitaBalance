import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from database import engine, SessionLocal
from models import Base

def migrate_database():
    """Adauga coloanele noi la baza de date existenta"""
    db = SessionLocal()
    
    try:
        print("Verificare si adaugare coloane noi...")
        
        new_columns = {
            'foods': [
                ('folate', 'FLOAT DEFAULT 0'),
                ('vitamin_a', 'FLOAT DEFAULT 0'),
                ('vitamin_c', 'FLOAT DEFAULT 0'),
                ('iodine', 'FLOAT DEFAULT 0'),
                ('vitamin_k', 'FLOAT DEFAULT 0'),
                ('potassium', 'FLOAT DEFAULT 0'),
            ],
            'lab_results': [
                ('folate', 'FLOAT'),
                ('vitamin_a', 'FLOAT'),
                ('vitamin_c', 'FLOAT'),
                ('iodine', 'FLOAT'),
                ('vitamin_k', 'FLOAT'),
                ('potassium', 'FLOAT'),
            ]
        }
        
        print("\nVerificare tabel 'foods'...")
        result = db.execute(text("PRAGMA table_info(foods)"))
        existing_columns = [row[1] for row in result]
        
        for column_name, column_def in new_columns['foods']:
            if column_name not in existing_columns:
                print(f"  Adauga coloana: {column_name}")
                db.execute(text(f"ALTER TABLE foods ADD COLUMN {column_name} {column_def}"))
            else:
                print(f"  Coloana {column_name} exista deja")
        
        print("\nVerificare tabel 'lab_results'...")
        result = db.execute(text("PRAGMA table_info(lab_results)"))
        existing_columns = [row[1] for row in result]
        
        for column_name, column_def in new_columns['lab_results']:
            if column_name not in existing_columns:
                print(f"  Adauga coloana: {column_name}")
                db.execute(text(f"ALTER TABLE lab_results ADD COLUMN {column_name} {column_def}"))
            else:
                print(f"  Coloana {column_name} exista deja")
        
        db.commit()
        print("\nMigrarea finalizata cu succes!")
        
    except Exception as e:
        db.rollback()
        print(f"\nEroare la migrare: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_database()
