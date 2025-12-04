# 🗄️ Setup Baza de Date - Ghid Rapid

## ⚡ Quick Start (Supabase - Recomandat)

### 1. Creează cont Supabase
- Mergi la [supabase.com](https://supabase.com) și creează un proiect nou
- **SALVEAZĂ PAROLA** când o setezi!

### 2. Obține Connection String
- Settings → Database → Connection String → **URI**
- Copiază string-ul (ex: `postgresql://postgres:password@db.xxx.supabase.co:5432/postgres`)

### 3. Configurează Backend
```bash
cd backend

# Creează .env
echo "DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.xxx.supabase.co:5432/postgres" > .env

# Instalează dependențe
pip install -r requirements.txt
```

### 4. Rulează Schema SQL
**Opțiunea A - Via Supabase Dashboard (Cel mai ușor):**
1. Mergi la **SQL Editor** în Supabase
2. Deschide `backend/database_schema.sql`
3. Copiază tot conținutul și lipește în editor
4. Click **Run**

**Opțiunea B - Via Script Python:**
```bash
python setup_database.py
```

**Opțiunea C - Via psql:**
```bash
psql "YOUR_CONNECTION_STRING" -f database_schema.sql
```

### 5. Populează cu Date
**Via Supabase Dashboard:**
1. SQL Editor → deschide `backend/seed_data.sql`
2. Copiază și rulează

**Via Script:**
```bash
python setup_database.py  # Va întreba dacă vrei să adaugi seed data
```

### 6. Testează
```bash
python run.py
# Sau
uvicorn main:app --reload
```

---

## 📁 Fișiere Create

- ✅ `database_schema.sql` - Schema completă PostgreSQL
- ✅ `seed_data.sql` - Date inițiale (alimente)
- ✅ `setup_database.py` - Script helper pentru setup
- ✅ `MIGRATION_GUIDE.md` - Ghid detaliat de migrare
- ✅ `database.py` - Actualizat pentru PostgreSQL/SQLite

---

## 🔄 Fallback la SQLite

Dacă nu setezi `DATABASE_URL` în `.env`, aplicația va folosi automat SQLite local (`vitabalance.db`). Perfect pentru development rapid!

---

## 📖 Documentație Completă

Vezi `MIGRATION_GUIDE.md` pentru instrucțiuni detaliate și troubleshooting.

