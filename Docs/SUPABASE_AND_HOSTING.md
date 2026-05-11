# Supabase, Render și Vercel — VitaBalance

## Proiect Supabase (exemplu)

- URL API: `https://kqvxqoptnmoqybcipacy.supabase.co`
- În **Render** (backend), setează:
  - `SUPABASE_URL` = URL-ul de mai sus
  - `SUPABASE_KEY` = **`service_role`** (secret), nu cheia `anon` — backend-ul folosește PostgREST cu drepturi complete; cheia `anon` nu trebuie expusă în browser.

## Date: tabelul `foods`

- Aplicația așteaptă toate coloanele din `domain.models.FoodItem` (inclusiv `carbs`, `fat`, `free_sugar`, `cholesterol`, `allergens`, `image_url`).
- După import CSV, rulează `backend/migrations/002_users_bio_foods_display.sql` ca să:
  - adaugi `users.bio` dacă lipsea;
  - completezi `allergens` cu `nedeclarat` unde lipsea informația;
  - setezi `image_url` cu placeholder deterministic (Picsum) unde era gol.

## Securitate (lint Supabase)

Supabase Dashboard raportează **RLS dezactivat** și tabele vizibile pentru `anon` — normal pentru prototip dacă **doar backend-ul** vorbește cu DB folosind `service_role`.

Pentru producție dură:

- activezi RLS și definești politici per tabel, **sau**
- revoci `SELECT`/`INSERT` pentru `anon`/`authenticated` pe tabelele sensibile și lași doar accesul prin API-ul tău (Render).

Nu activa RLS fără politici: blochează tot accesul. Ghid: [Row Level Security](https://supabase.com/docs/guides/auth/row-level-security).

## Vercel

- `vercel.json` (rădăcină) face rewrite `/api/*` → URL-ul backend Render. Actualizează `destination` dacă schimbi domeniul serviciului API.
- Build frontend: `VITE_API_URL` poate rămâne ne setat în Vercel dacă folosești proxy-ul `/api` din `vercel.json`. Dacă setezi `VITE_API_URL` la originea Render, folosește fie `https://.../api`, fie doar `https://...` (frontend-ul adaugă `/api` automat când path-ul e gol).
