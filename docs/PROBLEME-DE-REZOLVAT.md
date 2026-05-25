# VitaBalance — Probleme identificate de rezolvat

Document generat din analiza codului și a fluxurilor critice (procesare, recomandare, mesaje generate, extragere).  
**Ultima actualizare:** 2026-05-25

---

## Rezumat executiv

| Severitate | Număr | Focus principal |
|------------|-------|-----------------|
| Critic     | 4     | Viteză login, persistență explicații, motor O(n) |
| Major      | 6     | Polling, feedback, regenerare, extragere lab |
| Minor      | 5     | Cache, timeout-uri, UX text, concurență |

**Prioritate recomandată:** C1 → C2 → C4 → C3 → M1 → M4 → restul.

---

## 1. Procesare

### C1 — `GET /recommendations/stored` lent (hidratare la fiecare request)

- **Locație:** `backend/services/recommendation_materialize.py` → `hydrate_stored_recommendations_for_user()`
- **Descriere:** La login/listă, pentru fiecare recomandare salvată (până la 20) se apelează `ExplanationGenerator.generate_explanation()`. Nu se citește un payload complet din DB.
- **Impact:** Timp mare până la afișarea cardurilor; utilizatorul percepe întârziere la „De ce îl recomand” / „Sfaturi”.
- **Remediere:**
  - [ ] Returnare rapidă din DB fără regenerare la `listStored`.
  - [ ] Hidratare doar la materializare/regenerare sau migrare one-shot.
  - [ ] Opțional: cache per `user_id` + `recommendation_id` cu TTL scurt.

---

### C3 — Motor recomandare cu complexitate ridicată

- **Locație:** `backend/services/recommender.py` → `generate_recommendations()`; `backend/services/rule_engine.py` → `evaluate_food()`
- **Descriere:** Pentru fiecare aliment compatibil se evaluează toți nutrienții cu deficit; fiecare nutrienț declanșează reguli scoped. Complexitate aproximativă **O(alimente × deficite × reguli)**.
- **Impact:** Regenerare și înlocuire recomandare durează mult (secunde–zeci de secunde).
- **Remediere:**
  - [ ] Pre-filtrare/index: mapare `nutrient → [food_id]` sau top-K pe nutrienț înainte de evaluare completă.
  - [ ] Early exit: oprire după N candidați buni dacă scopul e doar replace (1 aliment nou).
  - [ ] Profilare cu metrici `foods_evaluated`, `elapsed_ms`.

---

### M1 — Polling frontend până la 120s

- **Locație:** `frontend/src/features/recommendations/components/Recommendations.tsx` (`SYNC_POLL_MAX_MS = 120000`, interval 1200ms)
- **Descriere:** După `refresh-async`, clientul face poll repetat pe `sync-meta` până la 2 minute.
- **Impact:** Latență percepută mare; multe request-uri inutile.
- **Remediere:**
  - [ ] Backoff exponențial (ex. 1s → 2s → 4s), plafon 30–45s.
  - [ ] Mesaj UI clar după timeout: „procesare în fundal”.
  - [ ] Opțional: WebSocket sau `job_id` + status pe server.

---

### M2 — Dublă rulare `generate_recommendations` (OpenFoodFacts)

- **Locație:** `backend/services/recommendation_materialize.py` (blocuri `if not rec_list and openfoodfacts_enabled`)
- **Descriere:** Dacă prima generare returnează listă goală, motorul rulează din nou integral.
- **Impact:** Timp dublu în cazuri edge.
- **Remediere:**
  - [ ] Integrare verificare OFF în loop-ul de scoring, fără rerun complet.
  - [ ] Sau flag explicit „a doua trecere” doar pe subset de alimente.

---

### M3 — Query `get_by_user_id(limit=1000)` la fiecare materializare

- **Locație:** `backend/services/recommendation_materialize.py`
- **Descriere:** Pentru maparea feedback → food se încarcă până la 1000 rânduri de recomandări per user la fiecare request de materializare.
- **Impact:** I/O Supabase suplimentar, latență.
- **Remediere:**
  - [ ] Limitare la recomandările active (ex. 20) + feedback direct cu `food_id` în tabelul `feedback`.
  - [ ] Index DB pe `(user_id, recommendation_id)` dacă lipsește.

---

### m1 — Cache catalog alimente fără cache hidratare user

- **Locație:** `backend/repositories/food_repository.py` (TTL 180s OK); `hydrate_stored_*` fără cache
- **Remediere:** [ ] Cache separat pentru payload-ul API returnat utilizatorului (invalidare la regenerare).

---

### m2 — Timeout axios 120s pe orice URL `/recommendations`

- **Locație:** `frontend/src/services/api.ts` (interceptor)
- **Descriere:** Include și `stored`, nu doar operații grele.
- **Remediere:**
  - [ ] `stored`: 15–30s; `replace`/`materialize`: 60–90s; `feedback`: 18s (deja parțial separat).

---

### m4 — `refresh-async` fără status job

- **Locație:** `backend/main.py` → `recommendations_refresh_async`; job în `BackgroundTasks` cu `except Exception` log-only
- **Impact:** Utilizatorul nu știe dacă job-ul a eșuat; race la tab-uri multiple.
- **Remediere:**
  - [ ] Tabel/câmp `refresh_status` (pending / done / failed + mesaj).
  - [ ] Propagare erori către `sync-meta` sau endpoint dedicat.

---

## 2. Recomandare

### C4 — Înlocuire (dislike + „Da”) = regenerare completă

- **Locație:** `backend/services/recommendation_materialize.py` → ramura `is_replace_only`
- **Descriere:** La replace se apelează `generate_recommendations()` pe tot setul filtrat, nu doar selectarea următorului candidat.
- **Impact:** Buton dislike + înlocuire procesează greu.
- **Remediere:**
  - [ ] Endpoint `replace` care returnează **un** aliment nou (top-1 exclusiv).
  - [ ] Răspuns minimal: lista actualizată fără re-hidratare 20 explicații.
  - [ ] Frontend: feedback rapid apoi replace (flux deja parțial implementat).

---

### C2 — `reasons` și `tips` nu sunt persistate în DB

- **Locație:** `backend/services/recommendation_materialize.py` (insert); schema `recommendations`
- **Descriere:** Se salvează doar `explanation` (text) și `portion_suggested`. `reasons` / `tips` se regenerează la citire.
- **Impact:** Inconsistență UI; dependență de C1; imposibil de auditat ce a văzut userul.
- **Remediere:**
  - [ ] Coloană `explanation_json` (JSONB) sau coloane `reasons`, `tips`.
  - [ ] La `listStored`: citire directă, fără `ExplanationGenerator`.
  - [ ] Migrare date existente (opțional, la regenerare forțată).

---

### M4 — Feedback pe recomandare ștearsă (legătură food_id fragilă)

- **Locație:** `feedback` legat de `recommendation_id`; `materialize` → `feedback_by_food` (parțial `feedback_food_by_rec_id` la replace curent)
- **Descriere:** După ștergerea rândului de recomandare, feedback-ul rămâne orfan; motorul poate ignora dislike-ul la generări viitoare.
- **Impact:** Dislike fără înlocuire trebuie să persiste; dislike la înlocuire trebuie să influențeze alimentul vechi exclus.
- **Remediere:**
  - [ ] Coloană `food_id` pe `feedback` (obligatorie la insert/upsert).
  - [ ] `feedback_by_food` construit direct din `food_id`, fără join pe recomandări șterse.
  - [ ] Test: dislike → Nu → reload → încă marcat; dislike → Da → aliment vechi exclus la următoarele recomandări.

---

### M5 — Regenerare completă la schimbare profil/analize

- **Locație:** `materialize_recommendations` → `delete_by_user_id` + motor complet
- **Descriere:** Comportament corect funcțional, dar costisitor.
- **Remediere:**
  - [ ] Regenerare incrementală (doar carduri afectate de nutrienți schimbați).
  - [ ] Sau regenerare în background cu listă stale afișată (deja parțial în UI).

---

### Bias și diversitate (calitate recomandare)

- **Locație:** `recommender.py` → `MIN_RECOMMENDATIONS_TARGET`, `fallback_profile_based`
- **Descriere:** Dacă regulile pe deficite lasă puține variante, se completează cu alimente generice de profil.
- **Remediere:**
  - [ ] Metrică `fallback_profile_ratio` în audit.
  - [ ] Documentare în UI când recomandarea e „de completare profil” vs „țintită pe deficit”.

---

## 3. Mesaje generate

### UI / formatare (parțial remediat în cod, date vechi în DB)

| Problemă | Status cod | Acțiune rămasă |
|----------|------------|----------------|
| Separator `---` vizibil ca bullet | Remediat (`\x1e` + filtru) | [ ] Regenerare/migrare texte vechi din DB |
| „Detaliu nutrienți” duplicat (porție + rezumat) | Remediat pentru profil nou | [ ] Verificare pe toate tipurile de explicație (reguli scoped) |
| Contribuții / acoperire pe același rând | Remediat în `recommender.py` (`\n`) | [ ] Validare vizuală după deploy |
| Formulări „orientative” / „consult medical” pe card | Scoase din generator | [ ] Curățare texte persistate vechi |

---

### m3 — Formulări tehnice în texte afișate

- **Exemple:** „aportul zilnic recomandat”, „din model”, „date catalog”.
- **Remediere:** [ ] Glosar UI simplificat pentru utilizator final; păstrare detaliu tehnic doar în PDF/export medic.

---

### Calitate semantică (fără LLM)

- **Risc halucinație:** scăzut (mesaje deterministe).
- **Risc inconsistență:** mediu (template + regenerare la citire).
- **Remediere:** [ ] Persistență mesaj la write-time (vezi C2); [ ] teste golden pe texte explicație per profil QA.

---

## 4. Extragere (lab / PDF)

### M6 — Extragere valori lab din text (regex)

- **Locație:** `backend/services/lab_text_extractor.py`; `frontend` extract local paralel
- **Descriere:** Multe pattern-uri regex pe text integral + linii; PDF-uri cu litere separate necesită `_collapse_spaced_letters`.
- **Impact:** Valori greșite sau lipsă; încredere scăzută la PDF-uri deformate.
- **Remediere:**
  - [ ] Validare intervale clinice post-extragere + flag „încredere scăzută” în UI.
  - [ ] Limită dimensiune text (ex. 50k caractere) + timeout.
  - [ ] Teste fixture pe PDF-uri reale din `Demo Test/`.

---

### Gestionare erori extragere

- **Remediere:**
  - [ ] Răspuns API cu câmpuri `extracted` + `warnings[]` per parametru.
  - [ ] UI: nu salva automat valori suspecte fără confirmare user.

---

## 5. Stabilitate și corectitudine

| ID | Problemă | Remediere |
|----|----------|-----------|
| S1 | Job `refresh-async` eșuat fără feedback în UI | Status job + mesaj eroare |
| S2 | Materializări paralele (tab-uri) pot suprascrie lista | Lock per `user_id` sau versiune `rec_generation_id` |
| S3 | Corectitudine 100% nefezabilă (model estimativ, catalog) | Disclaimer la nivel aplicație (componentă globală, nu per card) |

---

## 6. Checklist implementare (ordine sugerată)

### Faza 1 — Viteză percepută (1–2 zile)
- [ ] C2: Persistă `reasons`, `tips`, `text` (JSON sau coloane)
- [ ] C1: `listStored` fără `hydrate_stored` (citește din DB)
- [ ] m2: Timeout-uri separate pe rute API frontend
- [ ] M1: Polling cu backoff + plafon 45s

### Faza 2 — Replace & feedback (1 zi)
- [ ] C4: Replace top-1, răspuns lean
- [ ] M4: `food_id` pe `feedback`
- [ ] Teste manuale/automate dislike Nu / Da

### Faza 3 — Motor & scalabilitate (2–3 zile)
- [ ] C3: Indexare / early exit
- [ ] M2: Eliminare dublu `generate_recommendations`
- [ ] M3: Reducere query 1000 rânduri
- [ ] m4: Status job refresh

### Faza 4 — Calitate & extragere (1–2 zile)
- [ ] M6: Validare lab + warnings
- [ ] Migrare texte explicație vechi (fără `---`)
- [ ] Metrici monitorizare (secțiunea 7)

---

## 7. Metrici de monitorizat după remedieri

| Metrică | Țintă orientativă |
|---------|-------------------|
| `p95` `GET /recommendations/stored` | < 500 ms |
| `p95` `POST /recommendations` (replace) | < 5 s |
| `p95` `generate_recommendations` | < 3 s |
| `hydrate_explanation_count` la listStored | 0 |
| `poll_cycles_until_fresh` (median) | < 5 |
| `feedback_persist_success_rate` | > 99% |
| `fallback_profile_ratio` (top-10) | < 30% |
| `lab_extract_low_confidence_rate` | monitorizat, fără țintă fixă inițial |

---

## 8. Fișiere cheie de modificat

| Fișier | Probleme legate |
|--------|-----------------|
| `backend/services/recommendation_materialize.py` | C1, C2, C4, M2, M3, M4 |
| `backend/services/recommender.py` | C3, C4, bias |
| `backend/services/rule_engine.py` | C3 |
| `backend/services/explanation_generator.py` | C2, mesaje |
| `backend/repositories/feedback_repository.py` | M4 |
| `backend/main.py` | M4 (schema), m4 |
| `frontend/src/features/recommendations/components/Recommendations.tsx` | M1, M5 |
| `frontend/src/features/recommendations/components/RecommendationCard.tsx` | replace, feedback UX |
| `frontend/src/services/api.ts` | m2 |
| `backend/services/lab_text_extractor.py` | M6 |
| Supabase migrations | C2, M4 (`explanation_json`, `feedback.food_id`) |

---

## 9. Probleme deja abordate în conversații recente (verificare post-deploy)

Următoarele au patch-uri în cod; **rămân de verificat în producție** și pe **date vechi din DB**:

- [ ] Dislike optimist + client HTTP dedicat `/feedback`
- [ ] Feedback + replace: două request-uri (feedback apoi replace)
- [ ] Separator intern `\x1e` în loc de `---`
- [ ] Contribuții / acoperire pe linii separate în text nou
- [ ] `feedback_food_by_rec_id` la replace (sesiune curentă)

---

*Acest document poate fi folosit ca backlog pentru licență, sprint sau issue tracker (GitHub Issues).*
