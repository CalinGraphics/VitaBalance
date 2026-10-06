# Latența API — înainte și după

Măsurat pe 7 octombrie 2026, backend-ul rulat local (uvicorn, un proces) legat la baza de date Supabase de
producție (eu-west-1), contul de test `test1`, 20 de cereri după o cerere de încălzire, limitarea de rată oprită
doar pentru măsurătoare. Fiecare drum la Supabase costă ~80–100 ms de la această locație, deci cifrele sunt
dominate de rețea, nu de calcul.

| Endpoint | v1 (înainte de Faza 1) p50 / p95 | după Fazele 1–3 p50 / p95 | după Faza 4 p50 / p95 |
|---|---|---|---|
| `GET /recommendations/stored/{id}` | 464 / 495 ms | 413 / 499 ms | **221 / 341 ms** |
| `GET /recommendations/sync-meta/{id}` | 173 / 189 ms | 181 / 270 ms | **93 / 118 ms** |
| `POST /recommendations` (fără regenerare) | 536 / 578 ms | 542 / 575 ms | **212 / 233 ms** |
| `POST /recommendations?force_regenerate=true` | 839 / 883 ms | 743 / 814 ms | **458 / 517 ms** |

Ce s-a schimbat în Faza 4:
- matricea aliment × nutrient se construiește o singură dată (și la pornire) și scorul e vectorizat cu numpy
  (`services/recommendations/food_matrix.py`); calculul unui clasament e de ordinul milisecundelor;
- cache pe recomandări cu cheia hash(profil + analize + catalog + versiunea scorului): în memorie (cu voturi) și
  salvat în fapte, ca recomandările să nu fie regenerate când se schimbă doar `updated_at` (ex. poza de profil);
- N+1 scos: contorul de voturi venea dintr-o a doua interogare, acum din voturile deja încărcate; profilul nu mai
  e citit de două ori pe aceeași cerere și are un cache de 20 s, golit la orice scriere;
- indexuri noi (migrarea 013): `recommendations (user_id, score desc, id)`, `lab_results (user_id, updated_at desc,
  created_at desc)`;
- răspunsurile `/api/*` au `Cache-Control: private, no-store` (date per utilizator);
- frontend: carduri memoizate, schelet de încărcare, grafic încărcat lazy (chunk separat), voturi optimiste
  (existau deja), schimbarea limbii fără nicio cerere (Faza 3).

## Render

Pe planul gratuit, serviciul „adoarme” după ~15 minute fără trafic: prima cerere a durat **33,7 s** (măsurat pe
`/health`). Asta explică cea mai mare parte din lentoarea percepută la prima deschidere. Soluții:
1. planul plătit Render (Starter) — instanța rămâne pornită; recomandat dacă aplicația e folosită de alții;
2. un ping la `/health` la ~10 minute (ex. un cron extern) — gratuit, dar consumă orele gratuite și nu e garantat.

Vercel servește din `fra1` (Frankfurt), Supabase e în `eu-west-1` (Irlanda); regiunea serviciului Render se vede
doar în Dashboard — ideal Frankfurt, ca drumurile Render → Supabase să rămână scurte.
