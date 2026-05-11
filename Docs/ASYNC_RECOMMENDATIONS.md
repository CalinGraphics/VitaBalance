# Regenerare recomandări (async / scalare)

## Ce face aplicația acum

1. **`GET /api/recommendations/stored/{user_id}`** — citește recomandările deja salvate (rapid).
2. **`POST /api/recommendations`** — poate regenera lista dacă profilul sau analizele sunt mai noi decât recomandările.

Frontend-ul apelează **GET stored**, afișează lista existentă, apoi **POST** pentru actualizare; utilizatorul vede conținut imediat (stale-while-revalidate).

## Evoluții opționale

- **Coadă (Redis + RQ / Celery)**: POST enfilează job-ul, răspunde `202 Accepted`, worker-ul scrie în DB; UI face polling la GET stored.
- **WebSocket**: server notifică când regenerarea s-a terminat.
- **PostgreSQL `LISTEN/NOTIFY`**: pentru clienți conectați la același Postgres.

Pentru licență, fluxul GET+POST este suficient de documentat ca „strategie hibridă sincronă cu prefetch”.
