import sys
from pathlib import Path

# Fix encoding pentru Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Adaugă directorul backend la path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import argparse
import os
from typing import Any, Iterable, Optional, Tuple

from sqlalchemy.orm import Session
from database import SessionLocal
from models import Food
from typing import List, Dict
def _looks_like_postgres_url(url: str) -> bool:
    u = (url or "").lower()
    return u.startswith("postgres://") or u.startswith("postgresql://") or "supabase" in u


def _chunked(items: List[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _prepare_food_payload(food_data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalizează payload-ul pentru DB (SQLAlchemy/Supabase) cu valori default."""
    payload = dict(food_data)
    default_nutrients = {
        "folate": 0,
        "vitamin_a": 0,
        "iodine": 0,
        "vitamin_k": 0,
        "potassium": 0,
        "allergens": None,
        "image_url": None,
    }
    for key, default_value in default_nutrients.items():
        payload.setdefault(key, default_value)
    return payload


def generate_foods_supabase(clear_existing: bool = False) -> int:
    """
    Generează și inserează alimente în Supabase folosind clientul REST.
    Returnează numărul total de alimente (după insert).
    """
    # Import lazy: ca scriptul să poată rula și fără dependențele Supabase instalate,
    # atunci când folosim SQLAlchemy/SQLite.
    from supabase_client import get_supabase_client

    sb = get_supabase_client()

    if clear_existing:
        print("Șterg alimentele existente din Supabase...")
        # Nu există "delete all" fără filtru; folosim o condiție mereu adevărată.
        sb.table("foods").delete().neq("id", -1).execute()
        print("[OK] Alimentele existente au fost sterse (Supabase)")

    existing_names: set[str] = set()
    try:
        resp = sb.table("foods").select("name").execute()
        rows = getattr(resp, "data", None) or []
        existing_names = {r.get("name") for r in rows if r.get("name")}
    except Exception:
        # Dacă tabelul e mare / RLS, măcar să nu blocăm complet scriptul.
        existing_names = set()

    to_insert: List[Dict[str, Any]] = []
    for food_data in FOODS_DATA:
        payload = _prepare_food_payload(food_data)
        name = payload.get("name")
        if name and name in existing_names:
            print(f"  [SKIP] {name} exista deja, trec peste...")
            continue
        to_insert.append(payload)

    print(f"\nGenerez {len(FOODS_DATA)} alimente...")
    if to_insert:
        print(f"Inserez {len(to_insert)} alimente în Supabase...")
        for batch in _chunked(to_insert, 100):
            sb.table("foods").insert(batch).execute()
        print("[OK] Inserare completa (Supabase)")
    else:
        print("Nu am nimic de inserat (toate există deja).")

    total = sb.table("foods").select("id", count="exact").execute()
    count = getattr(total, "count", None)
    if isinstance(count, int):
        return count

    # Fallback dacă count nu e disponibil
    total_rows = getattr(total, "data", None) or []
    return len(total_rows)


# Baza de date cu alimente comune românești și valori nutriționale (per 100g)
FOODS_DATA = [
    # ALIMENTE BOGATE ÎN FIER
    {
        'name': 'Ficat de vită',
        'category': 'carne',
        'iron': 6.5,
        'calcium': 5,
        'magnesium': 18,
        'protein': 20,
        'zinc': 4.5,
        'vitamin_c': 0,
        'vitamin_d': 0,
        'vitamin_b12': 60,
        'fiber': 0,
        'calories': 135
    },
    {
        'name': 'Ficat de porc',
        'category': 'carne',
        'iron': 18,
        'calcium': 8,
        'magnesium': 20,
        'protein': 22,
        'zinc': 6.7,
        'vitamin_c': 23,
        'vitamin_d': 0,
        'vitamin_b12': 26,
        'fiber': 0,
        'calories': 130
    },
    {
        'name': 'Sardine în ulei',
        'category': 'peste',
        'iron': 2.9,
        'calcium': 382,
        'magnesium': 39,
        'protein': 25,
        'zinc': 2.9,
        'vitamin_c': 0,
        'vitamin_d': 272,
        'vitamin_b12': 8.9,
        'fiber': 0,
        'calories': 208
    },
    {
        'name': 'Somon',
        'category': 'peste',
        'iron': 0.8,
        'calcium': 12,
        'magnesium': 30,
        'protein': 20,
        'zinc': 0.6,
        'vitamin_c': 0,
        'vitamin_d': 988,
        'vitamin_b12': 3.2,
        'fiber': 0,
        'calories': 208
    },
    {
        'name': 'Carne de vită',
        'category': 'carne',
        'iron': 2.6,
        'calcium': 10,
        'magnesium': 22,
        'protein': 26,
        'zinc': 4.8,
        'vitamin_c': 0,
        'vitamin_d': 0,
        'vitamin_b12': 2.6,
        'fiber': 0,
        'calories': 250
    },
    {
        'name': 'Spanac',
        'category': 'legume',
        'iron': 2.7,
        'calcium': 99,
        'magnesium': 79,
        'protein': 2.9,
        'zinc': 0.5,
        'vitamin_c': 28,
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'fiber': 2.2,
        'calories': 23
    },
    {
        'name': 'Linte roșie',
        'category': 'legume',
        'iron': 7.5,
        'calcium': 35,
        'magnesium': 47,
        'protein': 25,
        'zinc': 3.3,
        'vitamin_c': 4.4,
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'fiber': 7.9,
        'calories': 358
    },
    {
        'name': 'Fasole albă',
        'category': 'legume',
        'iron': 3.7,
        'calcium': 90,
        'magnesium': 63,
        'protein': 21,
        'zinc': 2.5,
        'vitamin_c': 4.5,
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'fiber': 15,
        'calories': 333
    },
    {
        'name': 'Nuci',
        'category': 'fructe_seci',
        'iron': 2.9,
        'calcium': 98,
        'magnesium': 158,
        'protein': 15,
        'zinc': 3.1,
        'vitamin_c': 1.3,
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'fiber': 6.7,
        'calories': 654
    },
    
    # ALIMENTE BOGATE ÎN MAGNEZIU
    {
        'name': 'Semințe de dovleac',
        'category': 'semințe',
        'iron': 8.8,
        'calcium': 46,
        'magnesium': 592,
        'protein': 30,
        'zinc': 7.8,
        'vitamin_c': 1.9,
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'fiber': 6,
        'calories': 559
    },
    {
        'name': 'Semințe de floarea-soarelui',
        'category': 'semințe',
        'iron': 5.3,
        'calcium': 78,
        'magnesium': 325,
        'protein': 21,
        'zinc': 5,
        'vitamin_c': 1.4,
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'fiber': 8.6,
        'calories': 584
    },
    {
        'name': 'Migdale',
        'category': 'fructe_seci',
        'iron': 3.7,
        'calcium': 264,
        'magnesium': 268,
        'protein': 21,
        'zinc': 3.1,
        'vitamin_c': 1.5,
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'fiber': 12,
        'calories': 579
    },
    {
        'name': 'Fasole neagră',
        'category': 'legume',
        'iron': 5,
        'calcium': 123,
        'magnesium': 171,
        'protein': 21,
        'zinc': 3.6,
        'vitamin_c': 2.1,
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'fiber': 15,
        'calories': 341
    },
    {
        'name': 'Banane',
        'category': 'fructe',
        'iron': 0.3,
        'calcium': 5,
        'magnesium': 27,
        'protein': 1.1,
        'zinc': 0.2,
        'vitamin_c': 8.7,
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'fiber': 2.6,
        'calories': 89
    },
    {
        'name': 'Avocado',
        'category': 'fructe',
        'iron': 0.6,
        'calcium': 12,
        'magnesium': 29,
        'protein': 2,
        'zinc': 0.6,
        'vitamin_c': 10,
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'fiber': 6.7,
        'calories': 160
    },
    
    # ALIMENTE BOGATE ÎN CALCIU
    {
        'name': 'Branză telemea',
        'category': 'lactate',
        'iron': 0.2,
        'calcium': 692,
        'magnesium': 31,
        'protein': 16,
        'zinc': 3.5,
        'vitamin_c': 0,
        'vitamin_d': 16,
        'vitamin_b12': 1.5,
        'fiber': 0,
        'calories': 265
    },
    {
        'name': 'Iaurt grec',
        'category': 'lactate',
        'iron': 0.1,
        'calcium': 200,
        'magnesium': 19,
        'protein': 10,
        'zinc': 0.6,
        'vitamin_c': 0,
        'vitamin_d': 0,
        'vitamin_b12': 0.5,
        'fiber': 0,
        'calories': 59
    },
    {
        'name': 'Lapte',
        'category': 'lactate',
        'iron': 0.03,
        'calcium': 113,
        'magnesium': 10,
        'protein': 3.2,
        'zinc': 0.4,
        'vitamin_c': 0,
        'vitamin_d': 1,
        'vitamin_b12': 0.4,
        'fiber': 0,
        'calories': 61
    },
    {
        'name': 'Brânză de capră',
        'category': 'lactate',
        'iron': 0.6,
        'calcium': 298,
        'magnesium': 23,
        'protein': 19,
        'zinc': 1.1,
        'vitamin_c': 0,
        'vitamin_d': 20,
        'vitamin_b12': 0.8,
        'fiber': 0,
        'calories': 364
    },
    {
        'name': 'Broccoli',
        'category': 'legume',
        'iron': 0.7,
        'calcium': 47,
        'magnesium': 21,
        'protein': 2.8,
        'zinc': 0.4,
        'vitamin_c': 89,
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'fiber': 2.6,
        'calories': 34
    },
    
    # ALIMENTE ECHILIBRATE (bune pentru multiple nutrienți)
    {
        'name': 'Ouă',
        'category': 'oua',
        'iron': 1.2,
        'calcium': 56,
        'magnesium': 12,
        'protein': 13,
        'zinc': 1.1,
        'vitamin_c': 0,
        'vitamin_d': 87,
        'vitamin_b12': 1.1,
        'fiber': 0,
        'calories': 155
    },
    {
        'name': 'Pui piept',
        'category': 'carne',
        'iron': 0.7,
        'calcium': 15,
        'magnesium': 28,
        'protein': 31,
        'zinc': 0.9,
        'vitamin_c': 0,
        'vitamin_d': 0,
        'vitamin_b12': 0.3,
        'fiber': 0,
        'calories': 165
    },
    {
        'name': 'Orez brun',
        'category': 'cereale',
        'iron': 0.8,
        'calcium': 10,
        'magnesium': 43,
        'protein': 2.6,
        'zinc': 0.8,
        'vitamin_c': 0,
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'fiber': 1.8,
        'calories': 111
    },
    {
        'name': 'Quinoa',
        'category': 'cereale',
        'iron': 1.5,
        'calcium': 17,
        'magnesium': 64,
        'protein': 4.4,
        'zinc': 1.1,
        'vitamin_c': 0,
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'fiber': 2.8,
        'calories': 120
    },
    {
        'name': 'Mazăre',
        'category': 'legume',
        'iron': 1.5,
        'calcium': 25,
        'magnesium': 33,
        'protein': 5.4,
        'zinc': 1.2,
        'vitamin_c': 40,
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'fiber': 5.1,
        'calories': 81
    },
    
    # ALIMENTE ADĂUGATE PENTRU REGULILE DIN IMPLEMENTARE_PDF.md
    {
        'name': 'Năut',
        'category': 'legume',
        'iron': 4.3,
        'calcium': 49,
        'magnesium': 48,
        'protein': 19,
        'zinc': 2.8,
        'vitamin_c': 4,
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'fiber': 17,
        'calories': 364
    },
    {
        'name': 'Ciuperci expuse la UV',
        'category': 'legume',
        'iron': 0.5,
        'calcium': 3,
        'magnesium': 9,
        'protein': 3.1,
        'zinc': 0.5,
        'vitamin_c': 2.1,
        'vitamin_d': 1136,  # Foarte bogat în vitamina D după expunere UV
        'vitamin_b12': 0,
        'fiber': 1,
        'calories': 22
    },
    {
        'name': 'Morcovi',
        'category': 'legume',
        'iron': 0.3,
        'calcium': 33,
        'magnesium': 12,
        'protein': 0.9,
        'zinc': 0.2,
        'vitamin_c': 5.9,
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'vitamin_a': 835,  # Foarte bogat în vitamina A (beta-caroten)
        'fiber': 2.8,
        'calories': 41
    },
    {
        'name': 'Portocale',
        'category': 'fructe',
        'iron': 0.1,
        'calcium': 40,
        'magnesium': 10,
        'protein': 0.9,
        'zinc': 0.1,
        'vitamin_c': 53.2,  # Foarte bogat în vitamina C
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'folate': 30,  # Bogat în folat
        'fiber': 2.4,
        'calories': 47
    },
    {
        'name': 'Ardei gras',
        'category': 'legume',
        'iron': 0.3,
        'calcium': 7,
        'magnesium': 12,
        'protein': 1,
        'zinc': 0.1,
        'vitamin_c': 143.7,  # Foarte bogat în vitamina C
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'vitamin_a': 313,  # Bogat în vitamina A
        'fiber': 1.5,
        'calories': 31
    },
    {
        'name': 'Roșii',
        'category': 'legume',
        'iron': 0.3,
        'calcium': 10,
        'magnesium': 11,
        'protein': 0.9,
        'zinc': 0.2,
        'vitamin_c': 13.7,  # Bogat în vitamina C
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'vitamin_a': 42,
        'fiber': 1.2,
        'calories': 18
    },
    {
        'name': 'Alge marine',
        'category': 'alge',
        'iron': 2.8,
        'calcium': 168,
        'magnesium': 121,
        'protein': 1.7,
        'zinc': 1.2,
        'vitamin_c': 3,
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'iodine': 2320,  # Foarte bogat în iod
        'fiber': 0.5,
        'calories': 43
    },
    {
        'name': 'Cartofi',
        'category': 'legume',
        'iron': 0.8,
        'calcium': 12,
        'magnesium': 23,
        'protein': 2,
        'zinc': 0.3,
        'vitamin_c': 19.7,
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'potassium': 421,  # Bogat în potasiu
        'fiber': 2.2,
        'calories': 77
    },
    {
        'name': 'Kale',
        'category': 'legume',
        'iron': 1.5,
        'calcium': 150,  # Bogat în calciu
        'magnesium': 47,
        'protein': 4.3,
        'zinc': 0.6,
        'vitamin_c': 120,  # Foarte bogat în vitamina C
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'vitamin_k': 704.8,  # Foarte bogat în vitamina K
        'vitamin_a': 4812,  # Foarte bogat în vitamina A
        'fiber': 2,
        'calories': 49
    },
    {
        'name': 'Tărâțe de ovăz',
        'category': 'cereale',
        'iron': 4.7,
        'calcium': 58,
        'magnesium': 235,  # Foarte bogat în magneziu
        'protein': 17.3,
        'zinc': 3.1,
        'vitamin_c': 0,
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'fiber': 15.4,  # Foarte bogat în fibre
        'calories': 246
    },
    {
        'name': 'Midii',
        'category': 'fructe_de_mare',
        'iron': 6.7,  # Bogat în fier
        'calcium': 26,
        'magnesium': 34,
        'protein': 17.7,
        'zinc': 2.7,  # Bogat în zinc
        'vitamin_c': 8,
        'vitamin_d': 320,
        'vitamin_b12': 20,
        'iodine': 140,
        'fiber': 0,
        'calories': 86
    },
    {
        'name': 'Varză murată',
        'category': 'fermentate',
        'iron': 0.5,
        'calcium': 30,
        'magnesium': 13,
        'protein': 0.9,
        'zinc': 0.2,
        'vitamin_c': 14.7,
        'vitamin_d': 0,
        'vitamin_b12': 0,
        'vitamin_k': 13,  # Bogat în vitamina K
        'fiber': 2.5,
        'calories': 19
    },
]


def classify_food(food_data: Dict) -> Dict[str, bool]:
    """
    Clasifică un aliment după conținutul nutrițional
    
    Returns:
        Dict cu clasificările (ex: {'high_iron': True, 'high_magnesium': False})
    """
    classifications = {
        'high_iron': food_data.get('iron', 0) >= 3.0,
        'high_magnesium': food_data.get('magnesium', 0) >= 100.0,
        'high_calcium': food_data.get('calcium', 0) >= 200.0,
        'high_protein': food_data.get('protein', 0) >= 20.0,
        'high_fiber': food_data.get('fiber', 0) >= 5.0,
    }
    return classifications


def generate_foods(db: Session, clear_existing: bool = False):
    """
    Generează și inserează alimente în baza de date
    
    Args:
        db: Sesiunea de bază de date
        clear_existing: Dacă True, șterge toate alimentele existente
    """
    if clear_existing:
        print("Șterg alimentele existente...")
        db.query(Food).delete()
        db.commit()
        print("[OK] Alimentele existente au fost sterse")
    
    print(f"\nGenerez {len(FOODS_DATA)} alimente...")
    
    classifications_summary = {
        'high_iron': [],
        'high_magnesium': [],
        'high_calcium': [],
        'high_protein': [],
        'high_fiber': []
    }
    
    for food_data in FOODS_DATA:
        food_data = _prepare_food_payload(food_data)
        
        # Clasifică alimentul
        classifications = classify_food(food_data)
        
        # Adaugă la sumar
        for key, value in classifications.items():
            if value:
                classifications_summary[key].append(food_data['name'])
        
        # Verifică dacă alimentul există deja
        existing = db.query(Food).filter(Food.name == food_data['name']).first()
        
        if existing:
            print(f"  [SKIP] {food_data['name']} exista deja, trec peste...")
            continue
        
        # Creează alimentul nou
        food = Food(**food_data)
        db.add(food)
        print(f"  [OK] {food_data['name']} - {food_data['category']}")
    
    db.commit()
    print(f"\n[OK] {len(FOODS_DATA)} alimente procesate!")
    
    # Afișează clasificările
    print("\n" + "="*60)
    print("CLASIFICARE ALIMENTE")
    print("="*60)
    
    print("\nALIMENTE BOGATE IN FIER (>=3mg/100g):")
    for food_name in classifications_summary['high_iron']:
        print(f"   - {food_name}")
    
    print("\nALIMENTE BOGATE IN MAGNEZIU (>=100mg/100g):")
    for food_name in classifications_summary['high_magnesium']:
        print(f"   - {food_name}")
    
    print("\nALIMENTE BOGATE IN CALCIU (>=200mg/100g):")
    for food_name in classifications_summary['high_calcium']:
        print(f"   - {food_name}")
    
    print("\nALIMENTE BOGATE IN PROTEINE (>=20g/100g):")
    for food_name in classifications_summary['high_protein']:
        print(f"   - {food_name}")
    
    print("\nALIMENTE BOGATE IN FIBRE (>=5g/100g):")
    for food_name in classifications_summary['high_fiber']:
        print(f"   - {food_name}")
    
    print("\n" + "="*60)


def main():
    """Funcție principală"""
    parser = argparse.ArgumentParser(description="Generator alimente VitaBalance")
    parser.add_argument(
        "--mode",
        choices=["auto", "sqlalchemy", "supabase"],
        default="auto",
        help="auto: folosește DATABASE_URL dacă există, altfel Supabase dacă există credențiale, altfel SQLite",
    )
    parser.add_argument(
        "--clear",
        dest="clear_existing",
        action="store_true",
        help="Șterge alimentele existente înainte de generare",
    )
    parser.add_argument(
        "--no-clear",
        dest="clear_existing",
        action="store_false",
        help="Nu șterge alimentele existente (default)",
    )
    parser.set_defaults(clear_existing=False)
    args = parser.parse_args()

    print("=" * 60)
    print("GENERATOR ALIMENTE - VitaBalance")
    print("=" * 60)

    database_url = os.getenv("DATABASE_URL", "") or ""
    has_supabase_creds = bool(os.getenv("SUPABASE_URL")) and bool(os.getenv("SUPABASE_KEY"))

    mode = args.mode
    if mode == "auto":
        if _looks_like_postgres_url(database_url):
            mode = "sqlalchemy"
        elif has_supabase_creds:
            mode = "supabase"
        else:
            mode = "sqlalchemy"

    if mode == "supabase":
        print("Mod: Supabase (REST client)")
        total_foods = generate_foods_supabase(clear_existing=args.clear_existing)
        print(f"\nTotal alimente in baza de date: {total_foods}")
        print("\n[OK] Procesul s-a finalizat cu succes!")
        return

    # SQLAlchemy (Postgres dacă DATABASE_URL e setat, altfel SQLite fallback din database.py)
    if _looks_like_postgres_url(database_url):
        print("Mod: SQLAlchemy -> PostgreSQL/Supabase (DATABASE_URL)")
    else:
        print("Mod: SQLAlchemy -> SQLite (fallback, DATABASE_URL lipsa)")

    db = SessionLocal()
    try:
        generate_foods(db, clear_existing=args.clear_existing)
        total_foods = db.query(Food).count()
        print(f"\nTotal alimente in baza de date: {total_foods}")
        print("\n[OK] Procesul s-a finalizat cu succes!")
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
