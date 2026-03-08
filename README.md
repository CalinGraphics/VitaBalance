# VitaBalance

**Sistem de recomandare nutrițională personalizată bazat pe profil utilizator și analize medicale**

---

## Rezumat

VitaBalance este o aplicație web care oferă recomandări alimentare personalizate, adaptate nevoilor nutriționale ale utilizatorului. Sistemul utilizează datele de profil (vârstă, sex, greutate, înălțime, nivel de activitate, tip de dietă, alergii, condiții medicale) și, opțional, rezultatele analizelor medicale (feritină, vitamina D, B12, calciu, magneziu, potasiu etc.) pentru a identifica deficiențe nutriționale și a sugera alimente potrivite, cu explicații și export în format PDF.

---

## Funcționalități

- **Profil utilizator** – gestionare date personale: vârstă, sex, greutate, înălțime, nivel de activitate fizică, tip de dietă (omnivor, vegetarian, vegan, pescatarian), alergii și condiții medicale
- **Analize medicale** – introducere manuală a rezultatelor analizelor de laborator sau încărcare raport PDF pentru extragere automată
- **Recomandări personalizate** – generare de alimente recomandate pe baza deficitelor identificate, cu explicații contextuale și sugestii de porții
- **Export PDF** – export al recomandărilor în format PDF pentru utilizare ușoară
- **Feedback** – utilizatorul poate evalua recomandările și marca dacă le-a încercat sau dacă au fost utile

---

## Arhitectură și flux de funcționare

1. **Profilare** – Utilizatorul își creează cont prin magic link (email) și completează profilul cu datele personale relevante.
2. **Analize** – Opțional, utilizatorul introduce rezultatele analizelor medicale (hemoglobină, feritină, vitamina D, B12, calciu, magneziu, zinc, potasiu etc.) sau încarcă un raport PDF; sistemul extrage automat valorile disponibile.
3. **Calculul deficitelor** – Modulul `DeficitCalculator` estimează deficiențele nutriționale comparând aportul recomandat zilnic (RDI) cu aportul estimat sau cu valorile din analize, ținând cont de vârstă, sex, greutate și tip de dietă.
4. **Motor de reguli** – `ScopedRulesEngine` și `NutritionalRuleEngine` aplică reguli contextuale (dietă vegan, intoleranță la lactoză, hipertensiune etc.) și selectează alimente din catalogul `foods` care acoperă deficiențele identificate, filtrând conform restricțiilor utilizatorului.
5. **Recomandări** – Alimentele sunt ordonate după scor și procent de acoperire a deficitului; primele 10 sunt salvate și afișate utilizatorului, cu explicații și sfaturi.

---

## Cerințe

- Python 3.10–3.12 (recomandat 3.11)
- Node.js (pentru frontend)
- Cont Supabase (URL + cheie API)
- Opțional: cont Resend pentru trimitere email (magic link)

---

## Instalare și rulare

**1. Backend**

```bash
cd backend
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python run.py
```

Creează fișierul `backend/.env` cu variabilele necesare (vezi secțiunea următoare). API-ul rulează pe **http://localhost:8000**; documentație interactivă: http://localhost:8000/docs

**2. Frontend**

```bash
cd frontend
npm install
npm run dev
```

Interfața este disponibilă la **http://localhost:3000**.

---

## Variabile de mediu (backend)

| Variabilă | Obligatoriu | Descriere |
|-----------|-------------|-----------|
| `SUPABASE_URL` | Da | URL-ul proiectului Supabase |
| `SUPABASE_KEY` | Da | Cheia API (service role sau anon) |
| `JWT_SECRET` | Recomandat | Secret pentru semnarea token-urilor JWT |
| `RESEND_API_KEY` | Nu | Pentru trimitere magic link pe email; în lipsa lui, linkul apare în consolă |
| `RESEND_FROM_EMAIL` | Nu | Adresa expeditor pentru email |
| `FRONTEND_BASE_URL` | Nu | URL-ul frontend-ului (ex.: `http://localhost:3000`) |

---

## Baza de date

Aplicația folosește **Supabase** (PostgreSQL) ca unică sursă de date. Tabelele principale sunt:

- `users` – profil utilizator
- `foods` – catalog alimente cu valori nutriționale
- `lab_results` – rezultate analize medicale
- `recommendations` – recomandări salvate
- `feedback` – evaluări utilizator

Catalogul de alimente (`foods`) se gestionează direct din Supabase, prin import CSV. Schema include coloane pentru macro- și micronutrienți (fier, calciu, magneziu, vitamine, fibre etc.), categorie și alerjeni.

---

## Structura proiectului

```
VitaBalance/
├── backend/           # API FastAPI
│   ├── domain/        # Modele de domeniu
│   ├── repositories/  # Acces date (Supabase)
│   ├── services/      # Logică (deficit, reguli, recomandări)
│   ├── middleware/    # Autentificare JWT
│   └── main.py        # Rute API
└── frontend/          # Aplicație React (Vite, TypeScript)
    └── src/
        ├── features/  # Pagini (profil, analize, recomandări, PDF)
        └── services/  # Apeluri API și autentificare
```

---

## Stack tehnologic

- **Backend:** FastAPI, Supabase (PostgreSQL), JWT, Resend
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Framer Motion, Recharts, @react-pdf/renderer

---

## Disclaimer

Recomandările furnizate sunt sugestii generale și nu constituie sfaturi medicale. Pentru decizii legate de dietă și sănătate, se recomandă consultarea unui medic sau nutriționist.

---

Proiect realizat în scop academic — Licență 2026.