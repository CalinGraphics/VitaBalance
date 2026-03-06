# VitaBalance

Aplicație web pentru recomandări nutriționale personalizate: utilizatorul își completează profilul (vârstă, activitate, dietă, alergii), introduce rezultatele analizelor medicale, iar sistemul sugerează alimente potrivite cu explicații și export PDF.

Datele sunt stocate în **Supabase**; autentificarea se face doar prin **magic link** (link trimis pe email; contul se creează automat la prima utilizare). Toate rutele API sunt protejate cu JWT.

---

## Ce ai nevoie

- Python 3.10–3.12 (recomandat 3.11)
- Node.js (pentru frontend)
- Cont Supabase (URL + cheie API)
- Opțional: cont Resend pentru trimitere email (magic link); fără Resend, linkul apare doar în consola backend-ului

---

## Pornire rapidă

**1. Backend**

```bash
cd backend
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python run.py
```

Creează fișierul `backend/.env` cu:

```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
```

API-ul rulează pe **http://localhost:8000**. Documentație: http://localhost:8000/docs

**2. Frontend**

Într-un al doilea terminal:

```bash
cd frontend
npm install
npm run dev
```

Interfața este pe **http://localhost:3000**.

---

## Variabile de mediu (backend)

| Variabilă | Obligatoriu | Descriere |
|-----------|-------------|-----------|
| `SUPABASE_URL` | Da | URL-ul proiectului Supabase |
| `SUPABASE_KEY` | Da | Cheia API (service role sau anon, în funcție de RLS) |
| `JWT_SECRET` | Recomandat | Secret pentru semnarea token-urilor; în producție folosește un string lung și aleatoriu |
| `RESEND_API_KEY` | Nu | Dacă e setat, magic link-ul se trimite pe email; altfel linkul apare în consolă |
| `RESEND_FROM_EMAIL` | Nu | Adresa expeditor (implicit `onboarding@resend.dev`) |
| `FRONTEND_BASE_URL` | Nu | URL-ul frontend-ului pentru linkul din email. În dev: `http://localhost:3000`; la hosting: URL-ul domeniului tău |

---

## Alimente în baza de date

Tabelele (users, foods, lab_results, recommendations, feedback, magic_links) se creează și gestionează din **Supabase** (Dashboard sau migrări).

Pentru a popula tabelul `foods` cu alimente predefinite:

```bash
cd backend
python scripts/generate_foods.py
```

Poți rula cu `--clear` dacă vrei să ștergi alimentele existente înainte.

---

## Structura proiectului

- **backend** – FastAPI: rute în `main.py`, logică în `services/`, acces date prin `repositories/` (doar Supabase), modele de domeniu în `domain/`, auth și JWT în `middleware/` și `services/auth.py`.
- **frontend** – React (Vite, TypeScript): pagini în `src/features/`, API și auth în `src/services/`, export PDF în `src/features/recommendations/pdf/`.

---

## Tehnologii

Backend: FastAPI, Supabase (PostgreSQL), JWT, Resend (opțional).  
Frontend: React 18, TypeScript, Vite, Tailwind, Framer Motion, Recharts, @react-pdf/renderer pentru PDF.

---

## Disclaimer

Recomandările sunt sugestii generale și nu înlocuiesc consultul medical. Pentru decizii legate de dietă și sănătate, consultă un medic sau nutriționist.

---

Proiect realizat pentru licență 2026.
