# Deployment VitaBalance

## Timeout proxy (nginx / Render)

Generarea recomandărilor poate depăși 60s. Aliniază timeout-ul gateway cu clientul (ex. Axios 120s) sau folosește fluxul **GET stored + POST** (frontend afișează lista din DB imediat).

### nginx (exemplu)

```nginx
location /api/recommendations {
    proxy_pass http://backend;
    proxy_read_timeout 130s;
    proxy_connect_timeout 10s;
    proxy_send_timeout 130s;
}
```

### Render

În [Render Dashboard](https://dashboard.render.com), serviciul Web poate fi în spatele unui load balancer; pentru cereri lungi, verifică documentația serviciului pentru limitele HTTP. Alternativ: separă API-ul de generare pe un worker cu coadă (vezi `docs/ASYNC_RECOMMENDATIONS.md`).

## Frontend: `VITE_API_URL`

Build-ul Vite trebuie să trimită cereri către prefixul **`/api`** al backend-ului FastAPI. Poți seta:

- `VITE_API_URL=https://numele-serviciului.onrender.com/api` (recomandat, explicit), sau
- doar `VITE_API_URL=https://numele-serviciului.onrender.com` — în cod, dacă URL-ul are path gol (`/`), se adaugă automat `/api`.

Dacă lipsește `/api`, rutele devin `https://host/recommendations/...` în loc de `https://host/api/recommendations/...` și primești **404 Not Found**.

## Frontend: `VITE_API_URL`

Build-ul Vite trebuie să trimită cereri către prefixul **`/api`** al backend-ului FastAPI. Poți seta:

- `VITE_API_URL=https://numele-serviciului.onrender.com/api` (recomandat, explicit), sau
- doar `VITE_API_URL=https://numele-serviciului.onrender.com` — în cod, dacă URL-ul are path gol (`/`), se adaugă automat `/api`.

Dacă lipsește `/api`, rutele devin `https://host/recommendations/...` în loc de `https://host/api/recommendations/...` și primești **404 Not Found**.

## Variabile de mediu recomandate (producție)

| Variabilă | Valoare |
|-----------|---------|
| `CORS_ALLOW_ALL` | `false` |
| `CORS_ORIGINS` | `https://domeniul-tau-frontend.com` |
| `JWT_SECRET` | secret lung, unic per mediu |
| `RATE_LIMIT_ENABLED` | `true` (implicit) |
| `RATE_LIMIT_AUTH_PER_MIN` | ex. `20` |
| `RATE_LIMIT_RECOMMENDATIONS_PER_MIN` | ex. `40` |

## Indexuri bază de date

Rulează scriptul din [backend/migrations/001_recommendations_indexes.sql](../backend/migrations/001_recommendations_indexes.sql) în Supabase SQL Editor.

## Health check

`GET /health` returnează `checks.supabase: ok|error|skipped` pentru monitorizare.
