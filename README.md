# VitaBalance

**Sistem de recomandare nutrițională personalizată bazat pe profil utilizator și analize medicale**

## Rezumat

VitaBalance este o aplicație web care oferă recomandări alimentare personalizate, adaptate nevoilor nutriționale ale utilizatorului. Sistemul utilizează datele de profil (vârstă, sex, greutate, înălțime, nivel de activitate, tip de dietă, alergii, condiții medicale) și, opțional, rezultatele analizelor medicale (feritină, vitamina D, B12, calciu, magneziu, potasiu etc.) pentru a identifica deficiențe nutriționale și a sugera alimente potrivite, cu explicații și export în format PDF.

## Funcționalități

- **Autentificare** – cont cu email și parolă (JWT)
- **Profil utilizator** – gestionare date personale: vârstă, sex, greutate, înălțime, nivel de activitate fizică, tip de dietă (omnivor, vegetarian, vegan, pescatarian), alergii și condiții medicale, plus un **obiectiv caloric zilnic** opțional
- **Analize medicale** – introducere manuală a rezultatelor analizelor de laborator sau încărcare raport PDF pentru extragere automată
- **Recomandări personalizate** – generare de alimente recomandate pe baza deficitelor identificate, cu explicații contextuale și sugestii de porții
- **Export PDF** – export al recomandărilor în format PDF pentru utilizare ușoară
- **Feedback** – utilizatorul poate evalua recomandările și marca dacă le-a încercat sau dacă au fost utile
- **Obiectiv caloric** – dacă a fost setat în profil, panoul arată o bară de progres cu caloriile porțiilor sugerate raportate la obiectiv (strict informativ: nu influențează recomandările)
- **Limbă** – interfața este disponibilă în română și engleză (selector în antet, preferința se păstrează în browser)

## Arhitectură și flux de funcționare

1. **Profilare** – Utilizatorul își creează cont (email + parolă) și completează profilul cu datele personale relevante.
2. **Analize** – Opțional, utilizatorul introduce rezultatele analizelor medicale (hemoglobină, feritină, vitamina D, B12, calciu, magneziu, zinc, potasiu etc.) sau încarcă un raport PDF; sistemul extrage automat valorile disponibile.
3. **Calculul deficitelor** – Modulul `DeficitCalculator` estimează deficiențele nutriționale comparând aportul recomandat zilnic (RDI) cu aportul estimat sau cu valorile din analize, ținând cont de vârstă, sex, greutate și tip de dietă.
4. **Motor de reguli** – `ScopedRulesEngine` și `NutritionalRuleEngine` aplică reguli contextuale (dietă vegan, intoleranță la lactoză, hipertensiune etc.) și selectează alimente din catalogul `foods` care acoperă deficiențele identificate, filtrând conform restricțiilor utilizatorului.
5. **Recomandări** – Alimentele sunt ordonate după scor și procent de acoperire a deficitului; primele 10 sunt salvate și afișate utilizatorului, cu explicații și sfaturi.

## Cerințe

- Python 3.10–3.12 (recomandat 3.11)
- Node.js (pentru frontend)
- Cont Supabase (URL + cheie API)

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

## Variabile de mediu (backend)

| Variabilă | Obligatoriu | Descriere |
|-----------|-------------|-----------|
| `SUPABASE_URL` | Da | URL-ul proiectului Supabase |
| `SUPABASE_KEY` | Da* | Secret API folosit de backend; trebuie să fie JWT **`service_role`**, nu `anon`. *Pe Render, dacă integrarea îți lasă aici doar `anon`, lasă variabila și adaugă `SUPABASE_SERVICE_ROLE_KEY`. |
| `SUPABASE_SERVICE_ROLE_KEY` | Nu | Opțional: același JWT **service_role** din Supabase. Dacă e setat, **îl preferă** în locul lui `SUPABASE_KEY` (util când Render suprascrie `SUPABASE_KEY` cu cheia publică). |
| `JWT_SECRET` | Da (producție) | Secret pentru semnarea token-urilor JWT, minim 24 de caractere. Fără el, aplicația **refuză să pornească** dacă `DEBUG` nu e `true` (valoarea implicită din cod e publică). Generează unul cu `python -c "import secrets; print(secrets.token_urlsafe(48))"`. |
| `CORS_ORIGINS` | Nu | Origini permise, separate prin virgulă (implicit localhost:3000 și :5173) |
| `CORS_ALLOW_ALL` | Nu | Dacă `true`, permite orice origin (doar depanare; în producție lasă `false`) |
| `RATE_LIMIT_ENABLED` | Nu | Implicit `true`; setează `false` doar în dev dacă testezi multe cereri |
| `RATE_LIMIT_AUTH_PER_MIN` | Nu | Limită cereri `/api/auth/*` pe minut per IP (implicit 24) |
| `RATE_LIMIT_RECOMMENDATIONS_PER_MIN` | Nu | Limită `/api/recommendations*` pe minut per IP (implicit 45) |

**Render:** Root Directory `backend`, start `uvicorn main:app --host 0.0.0.0 --port $PORT`. Pe backend folosește cheia **service_role** din Supabase (poți seta `SUPABASE_SERVICE_ROLE_KEY` dacă `SUPABASE_KEY` rămâne anon din integrare).

## Performanță și UX

- **Prefetch**: `GET /api/recommendations/stored/{user_id}` returnează rapid recomandările din baza de date; frontend-ul le afișează înainte de `POST /api/recommendations` (regenerare).
- **Catalog alimente**: cache în memorie TTL pentru `FoodRepository.get_all()` (reduce apeluri Supabase repetate).
- **Motor**: pre-filtrare alimente incompatibile cu profilul înainte de evaluarea costisitoare a regulilor.
- **Indexuri DB**: se aplică direct în Supabase (SQL Editor) pe tabelele folosite intens (`recommendations`, `feedback`, `lab_results` etc.), după nevoile tale de performanță.

### Flux date (rezumat)

```mermaid
flowchart LR
  profile[Profil_si_analize]
  deficits[DeficitCalculator]
  rules[RuleEngines]
  recs[Recomandari_DB]
  ui[Frontend]
  profile --> deficits --> rules --> recs
  recs --> ui
```

## Baza de date

Aplicația folosește **Supabase** (PostgreSQL) ca unică sursă de date. Tabelele principale sunt:

- `users` – profil utilizator
- `foods` – catalog alimente cu valori nutriționale
- `lab_results` – rezultate analize medicale
- `recommendations` – recomandări salvate
- `feedback` – evaluări utilizator

**Schema:** `backend/schema.sql` descrie schema completă (starea țintă după toate migrările) — pentru o bază nouă rulează doar acest fișier. Pentru baza existentă, scripturile din `backend/migrations/` se aplică în ordine în Supabase:

| Migrare | Rol |
|---------|-----|
| `001_add_users_caloric_goal.sql` | coloana opțională `users.caloric_goal` |
| `002_drop_magic_links.sql` | șterge tabelul vechi `magic_links` (rulează-l după ce noua versiune a aplicației este în producție) |
| `003_align_and_harden.sql` | comentarii, unicitate email case-insensitive, `search_path` pe funcții, drepturi retrase pentru `anon`/`authenticated` |
| `004_integrity_and_cleanup.sql` | `CHECK`-uri pe profil, indexuri redundante eliminate, corecții de date |
| `005_feedback_persist_by_food.sql` | feedback unic per (utilizator, aliment), care supraviețuiește regenerării recomandărilor. **Aplică-o înainte de a publica codul care o folosește.** |
| `006_foods_name_en.sql` | `foods.name_en`: numele alimentelor în engleză (interfața și explicațiile EN) |

## Explicații RO/EN

Explicația fiecărei recomandări e **specifică pacientului** și se construiește din fapte, nu din text liber:

1. `services/explanation_facts.py` extrage faptele (valoarea din analize și pragul clinic, nutrientul deficitar, dieta, alergiile, afecțiunile cu restricții, porția) și le salvează în `recommendations.explanation_json.facts`.
2. `services/explanation_renderer.py` le transformă în text cu șabloanele din `services/explanation_i18n.py` (RO/EN), la citire — deci schimbarea limbii nu cere regenerarea recomandărilor.

API: parametrul `?lang=ro|en` (implicit `ro`) pe `GET /api/recommendations/stored/{user_id}` și `POST /api/recommendations`; `GET /api/recommendations/{user_id}/{recommendation_id}/explanation?lang=en` returnează explicația unei singure recomandări. Numele alimentelor vin din `foods.name_en`. Recomandările create înainte de această schimbare se regenerează o singură dată (`sync-meta.explanations_outdated`).

Toate datele (catalogul `foods`, conturile de test) se află exclusiv în Supabase, nu în repo. Catalogul de alimente se gestionează direct din Supabase (import CSV). Schema include coloane pentru macro- și micronutrienți (fier, calciu, magneziu, vitamine, fibre etc.), categorie și alerjeni.

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

## Stack tehnologic

- **Backend:** FastAPI, Supabase (PostgreSQL), JWT
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Framer Motion, Recharts, @react-pdf/renderer, react-i18next

## Disclaimer

Recomandările furnizate sunt sugestii generale și nu constituie sfaturi medicale. Pentru decizii legate de dietă și sănătate, se recomandă consultarea unui medic sau nutriționist.

Proiect realizat în scop academic — Licență 2026.