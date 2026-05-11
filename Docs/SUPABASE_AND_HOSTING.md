# Supabase, Render și Vercel — VitaBalance

## Proiect Supabase (exemplu)

- URL API: `https://kqvxqoptnmoqybcipacy.supabase.co`
- În **Render** (backend):
  - `SUPABASE_URL` = URL-ul de mai sus
  - `SUPABASE_KEY` = **`service_role`** (secret din Supabase → Settings → API).  
    **Obligatoriu:** backend-ul trebuie să folosească `service_role`, nu `anon`.

## Schema bazei (aliniată la cod)

- **`foods`**: nutrienți + `allergens` (opțional, `NULL` = necunoscut în sursă; fără text de umplutură). **Fără** `image_url` — aplicația nu afișează poze la alimente.
- **`feedback`**: `id`, `user_id`, `recommendation_id`, `rating`, `created_at` — singurele câmpuri folosite de API pentru like/dislike pe recomandare.
- **`users.bio`**: text opțional profil.
- Migrări: `002_users_bio_foods_display.sql` (bio), `003_schema_cleanup_rls.sql` (curățenie + RLS + drop view-uri nefolosite).

## Row Level Security (RLS)

Pe tabelele `public` este activat **RLS**. Rolul **`service_role`** folosit de FastAPI **ocolește** RLS în Supabase, deci aplicația continuă să funcționeze normal.

Acces **direct** la PostgREST din browser cu cheia `anon` către aceste tabele **nu** este suportat de această aplicație (nu există politici pentru `anon`). Dacă ai nevoie de client direct Supabase în frontend, trebuie definite politici RLS dedicate — vezi [Row Level Security](https://supabase.com/docs/guides/auth/row-level-security).

### Advisor Supabase după migrare

- **„RLS disabled”** (ERROR) dispare: RLS este activ.
- Poți vedea **„RLS enabled no policy”** (INFO): e normal cât timp doar backend-ul cu `service_role` accesează tabelele.
- Avertismente **GraphQL / anon poate face SELECT**: rolurile `anon`/`authenticated` au încă drepturi implicite pe obiecte; aplicația nu le folosește. Opțional, în SQL Editor poți revoca `SELECT` pentru `anon` pe tabelele sensibile dacă vrei zero avertismente (testează înainte pe staging).

## Vercel

- `vercel.json` face rewrite `/api/*` către backend-ul Render. Actualizează `destination` dacă schimbi URL-ul API.
- `VITE_API_URL`: vezi `Docs/DEPLOYMENT.md` — poate rămâne gol pe Vercel dacă folosești proxy-ul `/api`.
