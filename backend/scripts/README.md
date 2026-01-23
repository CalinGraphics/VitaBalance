# Scripts pentru VitaBalance

Acest director conține script-uri utilitare pentru gestionarea bazei de date.

## generate_foods.py

Script pentru generarea și clasificarea alimentelor în baza de date.

### Caracteristici:
- Generează alimente comune românești cu valori nutriționale reale
- Clasifică alimentele după conținut nutrițional:
  - Alimente bogate în fier (≥3mg/100g)
  - Alimente bogate în magneziu (≥100mg/100g)
  - Alimente bogate în calciu (≥200mg/100g)
  - Alimente bogate în proteine (≥20g/100g)
  - Alimente bogate în fibre (≥5g/100g)

### Utilizare:

```bash
# Din directorul backend
cd backend
python scripts/generate_foods.py
```

### Opțiuni:
- La rulare, script-ul va întreba dacă vrei să ștergi alimentele existente
- Dacă un aliment există deja, va fi trecut peste (nu va fi duplicat)
- Script-ul afișează un sumar cu clasificarea alimentelor

### Exemple de alimente incluse:
- **Bogate în fier**: Ficat de vită, Sardine, Spanac, Linte, etc.
- **Bogate în magneziu**: Semințe de dovleac, Migdale, Fasole neagră, etc.
- **Bogate în calciu**: Brânză telemea, Iaurt grec, Lapte, etc.

### Structura datelor:

Fiecare aliment conține următoarele informații nutriționale (per 100g):
- iron (mg)
- calcium (mg)
- magnesium (mg)
- protein (g)
- zinc (mg)
- vitamin_c (mg)
- vitamin_d (IU)
- vitamin_b12 (mcg)
- fiber (g)
- calories (kcal)

Plus informații generale:
- name (nume aliment)
- category (categorie: carne, peste, legume, lactate, etc.)

### Note:
- Valorile nutriționale sunt bazate pe date reale din baze de date nutriționale
- Script-ul este idempotent: poate fi rulat de mai multe ori fără a crea duplicate
- Datele sunt salvate în tabelul `foods` din baza de date

## test_supabase_sync.py

Script pentru testarea și verificarea sincronizării datelor între SQLite și Supabase.

### Caracteristici:
- Testează conexiunea cu Supabase
- Compară numărul de înregistrări din SQLite cu Supabase pentru fiecare tabel
- Verifică dacă ultimele înregistrări sunt sincronizate corect
- Identifică diferențe de sincronizare

### Utilizare:

```bash
# Din directorul backend
cd backend
python scripts/test_supabase_sync.py
```

### Ce verifică:
1. **Conexiune Supabase**: Verifică dacă aplicația se poate conecta la Supabase
2. **Număr înregistrări**: Compară numărul de înregistrări din SQLite cu Supabase pentru:
   - `users`
   - `lab_results`
   - `recommendations`
   - `feedback`
3. **Sincronizare recentă**: Verifică dacă ultimele 5 înregistrări din fiecare tabel sunt sincronizate

### Interpretare rezultate:
- ✅ = Sincronizare corectă
- ⚠️ = Diferențe sau erori minore
- ❌ = Date lipsă sau erori majore

### Note:
- Asigură-te că variabilele de mediu `SUPABASE_URL` și `SUPABASE_KEY` sunt setate
- Script-ul nu modifică date, doar verifică sincronizarea
- Poate fi rulat oricând pentru a verifica starea sincronizării
