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
| `RATE_LIMIT_TRUSTED_PROXY_HOPS` | Nu | Câte proxy-uri adaugă un element în `X-Forwarded-For` (implicit 2: rewrite Vercel + proxy Render). Pune `1` dacă backendul e expus direct, altfel limita se aplică tuturor la comun. |

## Deployment (Render + Vercel)

### Backend pe Render

Configurația recomandată: **Root Directory = `backend`**, Build Command `pip install -r requirements.txt`,
Start Command `uvicorn main:app --host 0.0.0.0 --port $PORT`, Health Check Path `/health`.

Repo-ul funcționează și dacă serviciul rulează din rădăcină (Root Directory gol): există `requirements.txt`
și `main.py` la rădăcină care trimit mai departe către `backend/`. Versiunea de Python e fixată la 3.11.8
prin `.python-version`; altfel Render folosește ultima versiune, incompatibilă cu dependențele.

Variabile obligatorii în **Environment**: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (cheia service_role,
nu anon), `JWT_SECRET`, plus `DEBUG=false` și `CORS_ORIGINS` cu adresa frontend-ului. **Fără `JWT_SECRET`
serviciul pornește și se oprește imediat**, cu mesajul explicit în log.

Există **două** servicii Render, cu același proiect Supabase:

| Serviciu | URL | Branch | Rol |
| --- | --- | --- | --- |
| `VitaBalance` | `https://vitabalance.onrender.com` | `main` | producție |
| `VitaBalance-1` | `https://vitabalance-1.onrender.com` | `Update-Version-1.1` | preview (codul nou) |

Verifici rapid ce cod rulează un serviciu: `curl <url>/openapi.json`. Codul nou are
`/api/recommendations/{user_id}/{recommendation_id}/explanation` și **nu** mai are rutele `magic-link`.

`render.yaml` din rădăcină descrie un al treilea serviciu (`vitabalance-preview`), creat cu **New → Blueprint**.
Nu e creat în acest moment — `VitaBalance-1` joacă rolul de preview. Folosește-l doar dacă vrei serviciul
definit în repo, altfel poți șterge fișierul.

### Frontend pe Vercel

Un push pe un branch diferit de cel de producție creează automat un **Preview Deployment**, cu URL stabil de
forma `…-git-<branch>-<cont>.vercel.app`. Producția rămâne neschimbată până la merge în `main`.

`/api/*` e redirecționat de `vercel.json` (proxy pe server, deci fără CORS).

> ⚠️ **De schimbat înainte de merge în `main`.** Pe branch-ul `Update-Version-1.1`, `/api/*` merge la
> `https://vitabalance-1.onrender.com` — backend-ul care rulează codul acestui branch. `vercel.json` se
> citește din branch-ul care se deployează, iar orice deployment construit din acest branch e un preview,
> deci regula e corectă cât timp lucrăm aici; e greșită din clipa în care branch-ul devine producție.
> La merge, pune înapoi `https://vitabalance.onrender.com` (sau mută serviciul de producție pe codul nou).

Înainte, fișierul trimitea `/api/*` la backendul de **producție**: previzualizarea branch-ului vorbea cu
codul vechi de pe `main` și arăta comportamentul vechi (nume și explicații doar în română, fără
`/explanation`), deși frontend-ul era nou. Atenție, nu doar aliasul `…-git-…​.vercel.app` e un preview:
fiecare deployment are și un URL cu hash (`<proiect>-<hash>-<cont>.vercel.app`), iar o regulă care se uită
doar după `-git-` îl ratează.

Există două `vercel.json` (rădăcină și `frontend/`) — se aplică cel corespunzător **Root Directory**-ului din
proiectul Vercel; ține-le identice ca reguli.

`VITE_API_URL` (build-time, scope Preview/Production) are prioritate față de rewrite și face cereri
**cross-origin**: dacă îl folosești, adaugă adresa Vercel în `CORS_ORIGINS` pe backend, altfel browserul
blochează cererile. Lăsat gol, se folosește rewrite-ul de mai sus.

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

### Conturi rămase fără parolă

Autentificarea prin magic link a fost scoasă, dar conturile create atunci au `password_hash` NULL: nu se pot
loga (nu au parolă) și nici nu se pot înregistra (emailul e deja în tabel). Înregistrarea cu un astfel de
email **setează parola pe rândul existent**, deci utilizatorul își recuperează profilul, analizele și
recomandările. Conturile care au deja parolă sunt respinse ca înainte.

Compromisul acceptat: aplicația nu verifică emailul la înregistrare, deci cine cunoaște una dintre acele
adrese poate revendica acel cont. Lista scade pe măsură ce proprietarii își setează parola; verifici
ce a mai rămas cu `select email from users where password_hash is null`.

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