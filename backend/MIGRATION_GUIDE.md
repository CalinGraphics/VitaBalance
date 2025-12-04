# 📘 Ghid de Migrare: SQLite → Supabase/PostgreSQL

Acest ghid te va ajuta să migrezi baza de date de la SQLite local la Supabase (PostgreSQL).

## 🎯 Opțiuni Disponibile

### Opțiunea 1: Supabase (Recomandat) ⭐
- **Avantaje**: 
  - Gratuit până la 500MB storage
  - Backup automat
  - Interfață web frumoasă
  - Scalabil ușor
  - Autentificare integrată (pentru viitor)

### Opțiunea 2: PostgreSQL Local
- **Avantaje**: 
  - Control complet
  - Fără dependențe externe
- **Dezavantaje**: 
  - Trebuie instalat manual
  - Backup manual

---

## 🚀 Migrare la Supabase (Recomandat)

### Pasul 1: Creează cont Supabase

1. Mergi la [supabase.com](https://supabase.com)
2. Creează un cont (gratuit)
3. Click pe "New Project"
4. Completează:
   - **Name**: `vitabalance` (sau ce vrei tu)
   - **Database Password**: **SALVEAZĂ-L BINE!** (nu îl vei mai vedea)
   - **Region**: Alege cel mai apropiat (ex: `West Europe` pentru România)
5. Așteaptă ~2 minute ca proiectul să fie creat

### Pasul 2: Obține Connection String

1. În Supabase Dashboard, mergi la **Settings** → **Database**
2. Scroll până la **Connection String**
3. Selectează **URI** (nu Session mode)
4. Copiază string-ul (arată așa):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```
5. **IMPORTANT**: Înlocuiește `[YOUR-PASSWORD]` cu parola ta reală!

### Pasul 3: Configurează Backend-ul

1. În folderul `backend/`, creează fișierul `.env`:
   ```bash
   # Windows PowerShell
   Copy-Item .env.example .env
   
   # Linux/Mac
   cp .env.example .env
   ```

2. Deschide `.env` și adaugă connection string-ul:
   ```env
   DATABASE_URL=postgresql://postgres:your_actual_password@db.xxxxx.supabase.co:5432/postgres
   ```

3. **IMPORTANT**: Adaugă `.env` în `.gitignore` dacă nu este deja acolo!

### Pasul 4: Instalează Dependențele

```bash
cd backend
pip install -r requirements.txt
```

### Pasul 5: Rulează Schema SQL în Supabase

**Metoda 1: Via Supabase Dashboard (Recomandat)**

1. Mergi la **SQL Editor** în Supabase Dashboard
2. Click pe **New Query**
3. Deschide fișierul `backend/database_schema.sql` din proiectul tău
4. Copiază tot conținutul și lipește-l în editor
5. Click pe **Run** (sau `Ctrl+Enter`)
6. Ar trebui să vezi "Success. No rows returned"

**Metoda 2: Via psql (Command Line)**

```bash
# Instalează psql dacă nu îl ai (inclus în PostgreSQL)
# Windows: descarcă de la postgresql.org
# Mac: brew install postgresql
# Linux: sudo apt-get install postgresql-client

psql "postgresql://postgres:your_password@db.xxxxx.supabase.co:5432/postgres" -f backend/database_schema.sql
```

### Pasul 6: Populează cu Date Inițiale

**Metoda 1: Via Supabase Dashboard**

1. Mergi la **SQL Editor**
2. Deschide `backend/seed_data.sql`
3. Copiază conținutul și rulează-l

**Metoda 2: Via psql**

```bash
psql "postgresql://postgres:your_password@db.xxxxx.supabase.co:5432/postgres" -f backend/seed_data.sql
```

### Pasul 7: Testează Conexiunea

```bash
cd backend
python -c "from database import engine; print('✅ Conexiune OK!' if engine else '❌ Eroare')"
```

Sau rulează aplicația:

```bash
python run.py
# sau
uvicorn main:app --reload
```

### Pasul 8: Verifică în Supabase

1. Mergi la **Table Editor** în Supabase Dashboard
2. Ar trebui să vezi tabelele: `users`, `lab_results`, `foods`, `recommendations`, `feedback`
3. Click pe `foods` - ar trebui să vezi alimentele populate

---

## 🗄️ Migrare la PostgreSQL Local

### Pasul 1: Instalează PostgreSQL

**Windows:**
- Descarcă de la [postgresql.org/download/windows](https://www.postgresql.org/download/windows/)
- Instalează cu setările default
- Notează parola pentru user `postgres`

**Mac:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Pasul 2: Creează Baza de Date

```bash
# Conectează-te la PostgreSQL
psql -U postgres

# În psql prompt:
CREATE DATABASE vitabalance;
\q
```

### Pasul 3: Configurează Backend-ul

1. Creează `.env`:
   ```env
   DATABASE_URL=postgresql://postgres:your_password@localhost:5432/vitabalance
   ```

2. Instalează dependențele:
   ```bash
   pip install -r requirements.txt
   ```

### Pasul 4: Rulează Schema și Seed Data

```bash
psql -U postgres -d vitabalance -f backend/database_schema.sql
psql -U postgres -d vitabalance -f backend/seed_data.sql
```

---

## 🔄 Migrare Date Existente (SQLite → PostgreSQL)

Dacă ai deja date în SQLite și vrei să le migrezi:

### Metoda 1: Export/Import Manual

```bash
# Export din SQLite
sqlite3 vitabalance.db .dump > dump.sql

# Ajustează dump.sql pentru PostgreSQL (înlocuiește sintaxa SQLite)
# Apoi importă în PostgreSQL
psql -U postgres -d vitabalance -f dump.sql
```

### Metoda 2: Script Python (Recomandat)

Creează `backend/migrate_sqlite_to_postgres.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, SessionLocal
from models import User, LabResult, Food, Recommendation, Feedback
import sqlite3

# Conectează-te la SQLite
sqlite_conn = sqlite3.connect('vitabalance.db')
sqlite_conn.row_factory = sqlite3.Row

# Conectează-te la PostgreSQL (din .env)
from database import engine as pg_engine
pg_session = sessionmaker(bind=pg_engine)()

# Migrează fiecare tabel
tables = [User, Food, LabResult, Recommendation, Feedback]

for table in tables:
    rows = sqlite_conn.execute(f'SELECT * FROM {table.__tablename__}').fetchall()
    for row in rows:
        data = dict(row)
        # Elimină id dacă există pentru auto-increment
        if 'id' in data:
            del data['id']
        pg_obj = table(**data)
        pg_session.add(pg_obj)

pg_session.commit()
print("✅ Migrare completă!")
```

---

## ✅ Verificare Finală

1. **Testează API-ul:**
   ```bash
   curl http://localhost:8000/api/foods
   ```

2. **Verifică în Supabase Dashboard:**
   - Table Editor → vezi datele
   - SQL Editor → rulează query-uri

3. **Verifică logs:**
   - Dacă vezi erori de conexiune, verifică `.env`
   - Dacă vezi erori SQL, verifică schema

---

## 🐛 Troubleshooting

### Eroare: "password authentication failed"
- Verifică parola în `.env`
- Pentru Supabase: folosește parola din crearea proiectului

### Eroare: "could not connect to server"
- Verifică că Supabase project este activ
- Verifică firewall-ul
- Pentru local: verifică că PostgreSQL rulează (`pg_isready`)

### Eroare: "relation does not exist"
- Rulează `database_schema.sql` din nou
- Verifică că ai selectat baza de date corectă

### Eroare: "psycopg2 not found"
```bash
pip install psycopg2-binary
```

---

## 📝 Note Importante

1. **Nu commita `.env` în git!** (ar trebui să fie în `.gitignore`)
2. **Backup regulat**: Supabase face backup automat, dar pentru local trebuie să faci tu
3. **Performance**: Supabase are limitări pe tier-ul gratuit (500MB, 2GB bandwidth/lună)
4. **Security**: Folosește variabile de mediu pentru toate credențialele

---

## 🎉 Gata!

Acum ai baza de date migrată la Supabase/PostgreSQL! Aplicația va folosi automat PostgreSQL dacă `DATABASE_URL` este setat în `.env`, altfel va folosi SQLite pentru development local.

