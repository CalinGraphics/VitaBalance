# VitaBalance Backend

Backend-ul aplicației VitaBalance - API REST pentru sistemul de recomandare nutrițională.

## Tehnologii

- Python 3.10+
- FastAPI
- SQLAlchemy
- PostgreSQL / Supabase (recomandat) sau SQLite (development)
- NumPy (pentru calcule matematice)
- Pandas (pentru procesarea datelor)

## Instalare

```bash
pip install -r requirements.txt
```

## Configurare Baza de Date

### Opțiunea 1: Supabase (Recomandat pentru producție) ⭐

1. Creează un proiect pe [supabase.com](https://supabase.com)
2. Obține connection string din Settings → Database
3. Creează fișierul `.env` în folderul `backend/`:
   ```env
   DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
   ```
4. Rulează schema SQL în Supabase Dashboard → SQL Editor:
   - Copiază conținutul din `database_schema.sql` și rulează-l
   - Apoi rulează `seed_data.sql` pentru date inițiale

**Sau folosește scriptul helper:**
```bash
python setup_database.py
```

### Opțiunea 2: SQLite (Development local)

Dacă nu setezi `DATABASE_URL`, aplicația va folosi automat SQLite local.

```bash
python seed_data.py  # Populează cu alimente
```

📖 **Vezi `DATABASE_SETUP.md` pentru ghid complet și `MIGRATION_GUIDE.md` pentru detalii.**

## Rulare

```bash
uvicorn main:app --reload
```

API-ul va rula pe `http://localhost:8000`

Documentația API (Swagger) este disponibilă la `http://localhost:8000/docs`

## Structura proiectului

```
backend/
├── main.py                 # Aplicația FastAPI principală
├── database.py             # Configurare bază de date
├── models.py               # Modele SQLAlchemy
├── schemas.py              # Scheme Pydantic pentru validare
├── seed_data.py            # Script pentru popularea bazei de date
└── services/
    ├── deficit_calculator.py    # Calculul deficitelor nutriționale
    ├── recommender.py           # Algoritmi de recomandare
    └── explanation_generator.py # Generarea explicațiilor
```

## Endpoints

- `POST /api/profile` - Creează/actualizează profil utilizator
- `GET /api/profile/{user_id}` - Obține profil utilizator
- `POST /api/lab-results` - Salvează rezultate analize
- `GET /api/lab-results/{user_id}` - Obține analize utilizator
- `POST /api/recommendations` - Generează recomandări
- `POST /api/feedback` - Salvează feedback
- `GET /api/foods` - Listă alimente

