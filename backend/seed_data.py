"""
Script pentru popularea bazei de date cu alimente și valori nutriționale
Date adaptate din baze de date publice (USDA)
"""
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Food

def seed_foods():
    """Populează baza de date cu alimente"""
    db: Session = SessionLocal()
    
    foods_data = [
        # Legume verzi (bogate în fier)
        {
            'name': 'Spanac proaspăt',
            'category': 'legume',
            'iron': 2.7, 'calcium': 99, 'vitamin_d': 0, 'vitamin_b12': 0,
            'magnesium': 79, 'protein': 2.9, 'zinc': 0.53, 'vitamin_c': 28.1,
            'fiber': 2.2, 'calories': 23, 'allergens': None
        },
        {
            'name': 'Linte fiartă',
            'category': 'leguminoase',
            'iron': 3.3, 'calcium': 19, 'vitamin_d': 0, 'vitamin_b12': 0,
            'magnesium': 36, 'protein': 9.0, 'zinc': 1.27, 'vitamin_c': 1.5,
            'fiber': 7.9, 'calories': 116, 'allergens': None
        },
        {
            'name': 'Fasole neagră',
            'category': 'leguminoase',
            'iron': 2.1, 'calcium': 27, 'vitamin_d': 0, 'vitamin_b12': 0,
            'magnesium': 70, 'protein': 8.9, 'zinc': 1.12, 'vitamin_c': 0,
            'fiber': 8.7, 'calories': 132, 'allergens': None
        },
        {
            'name': 'Broccoli',
            'category': 'legume',
            'iron': 0.73, 'calcium': 47, 'vitamin_d': 0, 'vitamin_b12': 0,
            'magnesium': 21, 'protein': 2.8, 'zinc': 0.41, 'vitamin_c': 89.2,
            'fiber': 2.6, 'calories': 34, 'allergens': None
        },
        
        # Carne (bogată în fier heme)
        {
            'name': 'Ficat de vită',
            'category': 'carne',
            'iron': 6.5, 'calcium': 5, 'vitamin_d': 49, 'vitamin_b12': 59.3,
            'magnesium': 18, 'protein': 20.4, 'zinc': 4.9, 'vitamin_c': 1.1,
            'fiber': 0, 'calories': 135, 'allergens': None
        },
        {
            'name': 'Carne de vită',
            'category': 'carne',
            'iron': 2.6, 'calcium': 18, 'vitamin_d': 7, 'vitamin_b12': 2.0,
            'magnesium': 20, 'protein': 26.0, 'zinc': 6.3, 'vitamin_c': 0,
            'fiber': 0, 'calories': 250, 'allergens': None
        },
        {
            'name': 'Carne de porc',
            'category': 'carne',
            'iron': 0.9, 'calcium': 19, 'vitamin_d': 13, 'vitamin_b12': 0.7,
            'magnesium': 22, 'protein': 27.3, 'zinc': 2.9, 'vitamin_c': 0,
            'fiber': 0, 'calories': 242, 'allergens': None
        },
        {
            'name': 'Piept de pui',
            'category': 'carne',
            'iron': 0.7, 'calcium': 15, 'vitamin_d': 5, 'vitamin_b12': 0.3,
            'magnesium': 25, 'protein': 31.0, 'zinc': 0.9, 'vitamin_c': 0,
            'fiber': 0, 'calories': 165, 'allergens': None
        },
        
        # Pește
        {
            'name': 'Somon',
            'category': 'peste',
            'iron': 0.8, 'calcium': 12, 'vitamin_d': 988, 'vitamin_b12': 3.2,
            'magnesium': 30, 'protein': 25.4, 'zinc': 0.6, 'vitamin_c': 0,
            'fiber': 0, 'calories': 208, 'allergens': 'peste'
        },
        {
            'name': 'Ton',
            'category': 'peste',
            'iron': 1.0, 'calcium': 10, 'vitamin_d': 227, 'vitamin_b12': 2.2,
            'magnesium': 50, 'protein': 30.0, 'zinc': 0.9, 'vitamin_c': 0,
            'fiber': 0, 'calories': 144, 'allergens': 'peste'
        },
        {
            'name': 'Sardine',
            'category': 'peste',
            'iron': 2.9, 'calcium': 382, 'vitamin_d': 193, 'vitamin_b12': 8.9,
            'magnesium': 39, 'protein': 24.6, 'zinc': 1.3, 'vitamin_c': 0,
            'fiber': 0, 'calories': 208, 'allergens': 'peste'
        },
        
        # Lactate
        {
            'name': 'Lapte',
            'category': 'lactate',
            'iron': 0.03, 'calcium': 113, 'vitamin_d': 40, 'vitamin_b12': 0.4,
            'magnesium': 10, 'protein': 3.4, 'zinc': 0.4, 'vitamin_c': 0,
            'fiber': 0, 'calories': 61, 'allergens': 'lactoza'
        },
        {
            'name': 'Iaurt grecesc',
            'category': 'lactate',
            'iron': 0.04, 'calcium': 110, 'vitamin_d': 0, 'vitamin_b12': 0.4,
            'magnesium': 11, 'protein': 10.0, 'zinc': 0.5, 'vitamin_c': 0,
            'fiber': 0, 'calories': 59, 'allergens': 'lactoza'
        },
        {
            'name': 'Brânză caș',
            'category': 'lactate',
            'iron': 0.1, 'calcium': 83, 'vitamin_d': 0, 'vitamin_b12': 0.2,
            'magnesium': 8, 'protein': 11.0, 'zinc': 0.4, 'vitamin_c': 0,
            'fiber': 0, 'calories': 98, 'allergens': 'lactoza'
        },
        
        # Cereale și semințe
        {
            'name': 'Semințe de dovleac',
            'category': 'seminte',
            'iron': 3.3, 'calcium': 46, 'vitamin_d': 0, 'vitamin_b12': 0,
            'magnesium': 262, 'protein': 18.6, 'zinc': 6.6, 'vitamin_c': 0.3,
            'fiber': 6.0, 'calories': 446, 'allergens': None
        },
        {
            'name': 'Semințe de chia',
            'category': 'seminte',
            'iron': 7.7, 'calcium': 631, 'vitamin_d': 0, 'vitamin_b12': 0,
            'magnesium': 335, 'protein': 16.5, 'zinc': 4.6, 'vitamin_c': 1.6,
            'fiber': 34.4, 'calories': 486, 'allergens': None
        },
        {
            'name': 'Almonds',
            'category': 'nuci',
            'iron': 3.7, 'calcium': 269, 'vitamin_d': 0, 'vitamin_b12': 0,
            'magnesium': 270, 'protein': 21.2, 'zinc': 3.1, 'vitamin_c': 0,
            'fiber': 12.5, 'calories': 579, 'allergens': 'nuci'
        },
        {
            'name': 'Ovăz',
            'category': 'cereale',
            'iron': 4.7, 'calcium': 54, 'vitamin_d': 0, 'vitamin_b12': 0,
            'magnesium': 177, 'protein': 16.9, 'zinc': 3.97, 'vitamin_c': 0,
            'fiber': 10.6, 'calories': 389, 'allergens': 'gluten'
        },
        
        # Alimente fortificate
        {
            'name': 'Lapte fortificat cu vitamina D',
            'category': 'lactate',
            'iron': 0.03, 'calcium': 113, 'vitamin_d': 120, 'vitamin_b12': 0.4,
            'magnesium': 10, 'protein': 3.4, 'zinc': 0.4, 'vitamin_c': 0,
            'fiber': 0, 'calories': 61, 'allergens': 'lactoza'
        },
        {
            'name': 'Cereale fortificate',
            'category': 'cereale',
            'iron': 18.0, 'calcium': 1000, 'vitamin_d': 100, 'vitamin_b12': 6.0,
            'magnesium': 100, 'protein': 10.0, 'zinc': 15.0, 'vitamin_c': 0,
            'fiber': 10.0, 'calories': 379, 'allergens': 'gluten'
        },
    ]
    
    try:
        # Șterge alimentele existente (opțional - pentru re-seeding)
        # db.query(Food).delete()
        
        # Adaugă alimentele noi
        for food_data in foods_data:
            existing = db.query(Food).filter(Food.name == food_data['name']).first()
            if not existing:
                food = Food(**food_data)
                db.add(food)
        
        db.commit()
        print(f"✅ S-au adăugat {len(foods_data)} alimente în baza de date!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Eroare la popularea bazei de date: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_foods()

