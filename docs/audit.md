# Audit VitaBalance — Faza 0

Data: 7 octombrie 2026 · Branch: `Update-Version-1.1` (HEAD `90d6acb`) · Fără modificări de cod.

Auditul a fost făcut citind codul, interogând catalogul `foods` din Supabase (doar `SELECT`) și rulând motorul real
local, pe catalogul real, cu pacienți sintetici (fără nicio scriere în baza de date). Scriptul de reproducere nu e
în repo; rezultatele relevante sunt citate mai jos.

## Scara de severitate

| Nivel | Înțeles |
|---|---|
| **Critic** | Poate face rău (siguranță alimentară, contraindicații) sau face ca recomandarea să fie greșită pentru aproape toți utilizatorii. |
| **Ridicat** | Rezultat vizibil greșit (cifre, ordine, text) pentru o parte importantă dintre utilizatori. |
| **Mediu** | Inconsecvență sau experiență proastă, fără impact direct asupra corectitudinii medicale. |
| **Scăzut** | Calitatea codului, mentenanță, observații. |

## Rezumat

Problema de fond nu e în formule, ci în **date**: catalogul de 591 de alimente amestecă valori per porție cu valori
la 100 g, iar micronutrienții par în mare parte valori de umplutură (vezi §4.0). Peste aceste date, motorul
ierarhizează după acoperirea per porție (nu după densitate), cu porții implicite pe categorie, fără filtre de
contraindicații pentru sarcină sau tratamente. Rezultatul: bagel și crutoane ies primele la magneziu, sashimi e
recomandat unei femei însărcinate, iar caloriile porțiilor sunt greșite de 3–8 ori.

| # | Problemă | Severitate |
|---|---|---|
| 4.0 | Catalog: valori per porție tratate ca valori la 100 g; micronutrienți aparent inventați | **Critic** |
| 4.7 | Pește crud (sashimi, ceviche), brânză Brie, ton recomandate în sarcină; nicio regulă de contraindicație | **Critic** |
| 4.3 | Bagel/crutoane/clătite peste nuci, semințe, leguminoase la magneziu | **Critic** |
| 4.A | Vitamina D: deficit în UI (IU) comparat cu alimente în µg → deficitul de vitamina D practic nu e acoperit | **Critic** |
| 4.2 | Calorii greșite pe porție (crutoane 76 kcal în loc de ~620; nuci 60 în loc de ~180) | **Ridicat** |
| 4.1 | Porție identică pentru toată categoria (152 g cereale, 136 g pește) | **Ridicat** |
| 4.4 | „Ai menționat…” când nevoia vine din analize | **Ridicat** |
| 4.5 | „Alternative similare” din altă categorie | **Ridicat** |
| 4.6 | Obiectiv caloric 1200 kcal acceptat fără avertisment | **Ridicat** |
| 4.8 | Schimbarea limbii așteaptă după server (~5 s; 30+ s la Render „adormit”) | **Ridicat** |
| 4.B | Praguri de laborator: vitamina D 20 ng/mL, feritină 30 pentru ambele sexe; severitatea e „aplatizată” | **Ridicat** |
| 4.C | Orice mențiune a unui nutrient în observații creează un deficit („iau vitamina D” → deficit) | **Ridicat** |
| 3 | Graficul Top 5 și cardurile pot arăta ordini și procente diferite | **Mediu** |
| 4.D | Două procente diferite pe același card („acoperire” vs „% din necesar”) | **Mediu** |
| 4.E | Reguli de categorie moarte (nume de categorii care nu există în catalog) | **Mediu** |
| 4.F | Valorile lipsă devin 0 (nu `null`) | **Mediu** |
| 4.G | Open Food Facts e folosit doar pentru alergeni (soia), cu cache în memorie, nu în Supabase | **Mediu** |
| 4.H | Testele „golden” folosesc alimente sintetice, nu catalogul; nu există CI | **Mediu** |
| 5 | Render pe planul gratuit: prima cerere 33,7 s | **Ridicat** (perceput ca lentoare) |

---

## 1. Harta fluxului

| Pas | Fișier : funcție | Observații |
|---|---|---|
| Profil | `frontend/src/features/medical/hooks/useProfileForm.ts`, `backend/main.py:294` `create_profile`, `backend/domain/schemas.py:23` | `caloric_goal` validat doar 500–10000 kcal. |
| Necesar de referință | `backend/services/nutrition/deficit_calculator.py:17` `RDI_TABLES`, `:165` `get_rdi` | Valori IOM/NIH (SUA), fără sursă citată; vitamina D în IU. Sarcina se deduce din text (`:138`). |
| Citirea analizelor | Manual: `MedicalLabResultsPage.tsx`; PDF: `shared/utils/pdfTextExtractor.ts` → `labLocalExtract.ts` + `backend/services/nutrition/lab_text_extractor.py` → `main.py:411` | Valorile se salvează fără unitate; se presupune unitatea din `CLINICAL_THRESHOLDS`. |
| Detectarea deficitelor | `deficit_calculator.py:294` `calculate_deficits`, `:540` `_calculate_deficit_from_labs`, `:391` `_parse_preferred_nutrients`, `:514` `describe_need` | Deficitul e în unitatea RDI (mg/µg/IU), nu în unitatea de laborator. |
| Context clinic | `backend/services/rules/clinical_context.py` `build_effective_user_profile` | Lipește observațiile din analize la `medical_conditions`. |
| Baza de alimente | `backend/repositories/food_repository.py:24` `get_all` (cache 10 min/proces), `domain/models.py:186` `row_to_food` | 591 rânduri, 36 de categorii. |
| Filtre | `rule_engine.py:951` `_is_compatible` → `services/rules/compatibility_core.py` (dietă, alergii, Open Food Facts pentru soia) + `data/medical_rules.json` | Filtrare prin cuvinte cheie în nume/categorie. |
| Scor / ierarhizare | `services/recommendations/recommender.py:28` `generate_recommendations`; `rule_engine.py:112` `evaluate_food`, `:1093` `_calculate_coverage`; `services/rules/scoped_rules.py` | Sortare finală după `(coverage, score)` (`recommender.py:181, 253`). |
| Porție | `services/recommendations/portion_calculator.py:172` `suggest_portion` | Porție pe categorie × factori sex/greutate/activitate. |
| kcal | Backend: `materialize.py:61` `kcal_per_100g_for_display`; frontend: `features/recommendations/utils/calories.ts:8` `estimatePortionCalories` | Formula e corectă (`kcal/100 × g / 100`); datele de intrare nu. |
| Textul explicației | `services/explanations/facts.py:96` `build_facts` → `renderer.py:63` `render_explanation` → șabloane `i18n.py` `SENTENCES`, `TIPS` | Faptele se salvează în `recommendations.explanation_json.facts`. |
| Persistare | `materialize.py:139` `_prepare_insert_rows`, `:256` `materialize_recommendations` | Max. 20 recomandări/utilizator. |
| Traduceri (i18n) | Backend: `i18n.py`; nume: `foods.name_en` (migrarea 006) + `domain/models.py:65` `food_display_name`; frontend: `shared/i18n/locales/{ro,en}.json` | Textele recomandărilor se randează pe **server**, în limba din `?lang=`. |
| Afișare | `Recommendations.tsx`, `RecommendationCard.tsx`, `NutrientChart.tsx`, `CaloricGoalProgress.tsx` | |

## 2. De ce poate diferi ordinea textului din cardurile cu recomandări de cea din graficul „Top 5”

Graficul (`NutrientChart.tsx:34`) ia **primele 5 din lista completă** `recommendations`, cu câmpul `coverage`.
Cardurile (`Recommendations.tsx:386–406`) afișează `filteredRecommendations`, adică lista **după filtrul de
categorie**. Cauzele divergenței:

1. **Filtrul de categorie.** Dacă utilizatorul alege „Nuci”, cardurile arată doar nuci, iar graficul rămâne pe
   top 5 global (bagel, crutoane…).
2. **Ordinea se schimbă între generare și citire.** La generare, lista e ordonată de `recommender.py:253`
   (recomandările de completare la final, apoi nutrienții „obligatorii”, apoi `coverage`, `score`, plus
   `_promote_required_nutrient_items`). La citire, `RecommendationRepository.get_by_user_id` reordonează după
   `coverage_percentage DESC, score DESC`. Același set apare deci în ordini diferite după un refresh.
3. **Două procente diferite.** Graficul și bara de pe card folosesc `coverage` (o medie ponderată cu randament
   descrescător, `rule_engine.py:1142`: `portion/(portion+deficit)`), iar textul cardului spune „~X% din necesarul
   zilnic” (`facts.py:120`: `amount/RDI`). Un aliment poate avea 40% în grafic și 21% în text.
4. Graficul trunchiază numele la 15 caractere, deci „Crutoane cu Usturoi” și „Crutoane” arată la fel.

## 3. Bug-urile din producție, reproduse

Pacientul P1 din brief (bărbat, 34 de ani, 79 kg, 182 cm, activitate moderată, omnivor, vitamina D 18 ng/mL,
magneziu 1,6 mg/dL), rulat pe catalogul real:

```
 1. [Cereale]      Bagel Simplu                 152g ≈ 410 kcal | cov=40.7 | covers=['magnesium']
 2. [Cereale]      Crutoane cu Usturoi          152g ≈  76 kcal | cov=39.9 | covers=['magnesium']
 3. [Cereale]      Brioșă Engleză Integrală     152g ≈ 204 kcal | cov=39.4
 4. [Cereale]      Clătite Americane (2 medii)  152g ≈ 274 kcal | cov=39.0
 5. [Mese/Cereale] Mămăligă Cremoasă            152g ≈ 228 kcal | cov=37.6
 7. [Proteine/Pește] Sashimi Somon (3 bucăți)   136g ≈ 163 kcal
 9. [Mese/Pește]   Ceviche de Pește             136g ≈ 245 kcal
11. [Nuci]         Amestec de Nuci               30g ≈  60 kcal | cov=16.0
14. [Nuci]         Migdale                       30g ≈  49 kcal | cov=14.5
```

Niciuna dintre cele 14 recomandări nu acoperă vitamina D (vezi §4.A), deși titlul fiecăreia spune „analizele tale
arată valori sub pragul clinic pentru: magneziu și vitamina D”.

### 4.0 Catalogul de alimente — **Critic** (cauza principală pentru 4.2 și 4.3)

Tabela `foods` e descrisă ca „nutrienți per 100 g”, dar:

- **273 din 591** de nume conțin o cantitate („(1 bucată)”, „(2 medii)”, „(1 lingură)”): valorile sunt per bucată
  sau per porție. Exemple: Migdale 164 kcal (= 1 uncie ≈ 28 g; USDA: ~579 kcal/100 g), Amestec de Nuci 200 kcal,
  Crutoane cu Usturoi 50 kcal (≈ o porție de ~14 g), Stridie Crudă (1 medie) 8 kcal, Ouă Benedict (1 porție)
  600 kcal.
- **Verificarea Atwater nu prinde problema.** Rândurile per porție sunt consistente intern (crutoane:
  4·1,5 + 4·7 + 9·2 = 52 ≈ 50 kcal), deci trec. 54 de rânduri ies din toleranța de ±15%, iar 33 din ±30%
  (calcul cu carbohidrați neți + 2·fibre). Pentru valorile per porție e nevoie de o a doua verificare: densitatea
  energetică comparată cu USDA FoodData Central.
- **16 rânduri** au macronutrienți care însumează peste 100 g „la 100 g”, deci sunt imposibile fizic (preparate
  „Mese/…”). Backend-ul trimite `calories: null` pentru ele, dar le recomandă în continuare.
- **Micronutrienții par generați, nu măsurați.** Magneziul are aproape aceeași distribuție în aproape toate
  categoriile (medie ~20 mg, interval 5–35, abatere standard ~9): legume, fructe, deserturi, carne, băuturi,
  leguminoase. Leguminoasele (medie 19 mg) au mai puțin magneziu decât cerealele (41 mg) — invers față de realitate.
  Vitamina D are ~0,5 µg în aproape toate categoriile; **190 de alimente vegetale** (cereale, legume, fructe,
  nuci) au vitamina D > 0 (crutoane 0,9 µg, clătite 0,9 µg), deși plantele nu conțin vitamina D în afara
  ciupercilor expuse la UV. Gin tonic: 24 µg vitamina K; Kale: 56 µg (USDA, crud: de ordinul sutelor de µg).
- **Lipsesc** chiar alimentele pe care brief-ul le cere ca referință: spanac simplu, semințe de dovleac
  (există doar „Spanac cu Smântână” și „Dip de Spanac”). Semințele de pin sunt în categoria „Nuci”.

Concluzie: nicio corecție de formulă nu face recomandările corecte cât timp datele rămân așa. Catalogul trebuie
reconstruit din USDA FoodData Central (vezi „Decizie necesară” la final).

### 4.1 Aceeași porție pentru toată categoria — **Ridicat**

`portion_calculator.py:25` are o porție de bază pe categorie (`cereale` 150 g, `peste` 130 g), înmulțită în
`_sex_multiplier` (`:123`) cu sexul, greutatea și activitatea:

- cereale: 150 × 1,06 (bărbat) × 0,956 (79 kg) × 1,0 (moderat) = **152 g**;
- pește: 130 × 1,06 × 1,03 (bias pește, bărbat) × 0,956 = **136 g**.

Numele alimentului contează doar pentru deserturi, băuturi și câteva cereale (`:203`): orice altă „Cereale”
primește 152 g, iar un ou mare („Ou Fiert Tare (1 mare)”) primește 132 g în loc de 50 g. Pentru preparate
(„mese”) porția e 350 g × factori, deci „Ouă Benedict (1 porție)” ajunge la 345 g ≈ 2070 kcal. Porția de bază nu
ține cont de forma produsului (crutoane, clătite, bagel) și nici nu are sens să crească pentru că omul e mai greu
(porția pentru un nutrient nu e o rație calorică).

### 4.2 Calorii greșite — **Ridicat**

Formula e corectă (`calories.ts:15`, `materialize.py:61`: `kcal_la_100g × grame / 100`). Problema e combinația
dintre §4.0 și §4.1:

- Crutoane cu Usturoi: catalogul spune 50 „kcal/100 g” (de fapt per ~14 g) × 152 g = **76 kcal**. Realist
  (crutoane condimentate, ~400–465 kcal/100 g în USDA): 152 g ≈ **610–700 kcal**.
- Amestec de Nuci: 200 „kcal/100 g” (de fapt per ~30 g) × 30 g = **60 kcal**. Realist (~600 kcal/100 g):
  30 g ≈ **180 kcal**.

Filtrul `kcal_per_100g_for_display` (macronutrienți > 100,5 g) prinde doar 16 rânduri. Valorile per porție cu
macronutrienți mici trec neobservate.

### 4.3 Bagel și crutoane înaintea nucilor la magneziu — **Critic**

Trei cauze care se adună:

1. **Date** (§4.0): magneziu în catalog — crutoane 55, bagel 57, clătite 53, migdale 71 (per 28 g!),
   fasole neagră 29. Valori USDA aproximative la 100 g, de confirmat în Faza 1: migdale ~270 mg, semințe de dovleac
   ~590 mg, spanac crud ~79 mg, fasole neagră fiartă ~70 mg, bagel simplu ~20–30 mg.
2. **Ierarhizarea e după acoperirea per porție, nu după densitate.** Sortare `(coverage, score)`
   (`recommender.py:181`); `coverage = porție × valoare / deficit`. Cerealele primesc 152 g, nucile 30 g, deci
   bagelul aduce 87 mg „pe porție”, iar nucile 24 mg. Calculat la 100 kcal, cu date USDA, ordinea ar fi:
   spanac (~340 mg/100 kcal) > semințe de dovleac (~105) > fasole neagră (~53) > migdale (~47) ≫ bagel (~10).
3. **Penalizarea procesatelor nu se aplică.** `_active_deficit_quality_factor` (`recommender.py:882`) caută
   „procesat” în categorie, dar bagelul, crutoanele și clătitele sunt în „Cereale”, nu în „Cereale/Procesate”.
   Nu există niciun criteriu pentru făină rafinată, zahăr adăugat sau sare.

Aceeași regulă de magneziu (`magnesium_moderate_medium`, scor 8,1) se aplică identic bagelului și migdalelor:
scorul nu diferențiază, iar ordinea e decisă doar de `coverage`.

### 4.4 „Ai menționat nevoia de magneziu” când nevoia vine din analize — **Ridicat**

Sursa textului: `i18n.py` `SENTENCES.headline_notes` / `reason_notes`, ales în `renderer.py:85` când
`need.source == "notes"`. Sursa e decisă de `describe_need` (`deficit_calculator.py:514`):

- „lab” doar dacă valoarea e sub **pragul fix al aplicației** (`CLINICAL_THRESHOLDS`, ex. Mg 1,7 mg/dL);
- altfel, „notes” dacă `_parse_preferred_nutrients` găsește nutrientul în observații.

Reprodus: magneziu 1,75 mg/dL (sub limita minimă a multor laboratoare, peste pragul aplicației) + sugestia
„Deficiență de magneziu” bifată → toate cele 10 carduri spun „pentru că ai menționat nevoia de: magneziu”.
Problemele de fond:

- Aplicația nu știe intervalul de referință al laboratorului; folosește propriul prag, deci o valoare marcată
  „scăzut” pe buletin poate fi tratată ca normală, iar textul cade pe „ai menționat”.
- Textul din observații vine adesea din **butoanele de sugestii** (`MedicalLabResultsPage.tsx:51`, ex.
  „Deficiență de magneziu”), nu din ce a scris omul. Fiind salvate în `lab_results.notes`, ele sunt tratate ca
  afirmația utilizatorului.
- Expresiile regulate sunt prea largi (§4.C), deci orice mențiune a nutrientului devine „nevoie”.

TODO pentru Faza 1: sursa deficitului trebuie salvată când deficitul e **creat** (nu dedusă la randare) și să fie
„lab” ori de câte ori există o valoare de laborator sub interval.

### 4.5 „Alternative similare” din altă categorie — **Ridicat**

`facts.py:170` `alternatives_for` caută doar printre celelalte recomandări (max. 20) pe cele care au **același
nutrient principal**, fără nicio condiție de categorie. La P1 toate acoperă doar magneziu, deci alternativele
nucilor sunt „Bagel Simplu, Crutoane cu Usturoi, Brioșă Engleză Integrală” — primele trei din listă, pentru
fiecare card. În plus, „nutrientul principal” e primul din `facts.nutrients`, ales după `valoare × deficit`
(`facts.py:82`), nu după ce a decis motorul.

### 4.6 Obiectivul caloric de 1200 kcal acceptat fără avertisment — **Ridicat**

Nu există nicio estimare a metabolismului bazal sau a consumului total (nici Mifflin-St Jeor, nici factor de
activitate) — `grep` după „bmr/mifflin/tdee” nu găsește nimic. Validarea e doar `500 ≤ caloric_goal ≤ 10000`
(`schemas.py:23` + CHECK în DB). Pentru P1: Mifflin-St Jeor = 10·79 + 6,25·182 − 5·34 + 5 = **1762 kcal**;
× 1,55 (moderat) ≈ **2730 kcal/zi**. 1200 kcal e sub metabolismul bazal și cu 56% sub consumul total.
`UserProfile.caloric_goal` e marcat explicit „strict informativ”, iar `CaloricGoalProgress.tsx` afișează doar
suma caloriilor (greșite, §4.2) față de obiectiv.

### 4.7 Pește crud și alte alimente riscante în sarcină — **Critic**

Pacient sintetic: femeie, 31 de ani, pescetariană, „Sunt însărcinată în luna 4”, vitamina D 15 ng/mL. Recomandări
reale din catalog: **Ceviche de Pește** (locul 4), **Sashimi Somon** (locul 6), **Ton la Conservă** (locul 2),
**Salată de Ton**, **Brânză Brie** (brânză moale cu mucegai, risc de listerioză). Catalogul conține și „Stridie
Crudă” și „Ficat de Pui”.

Cauze: nu există nicio regulă pentru sarcină, imunitate scăzută, pește crud, pește bogat în mercur, ficat
(vitamina A preformată), warfarină, hemocromatoză sau boală cronică de rinichi ca regulă de fosfor. Sarcina e
detectată doar pentru a crește necesarul de folat și fier (`deficit_calculator.py:138, 193`). Warfarina apare
doar într-un sfat generic despre vitamina K (`i18n.py:155`); nu filtrează nimic. Regula renală
(`medical_rules.json`) exclude spanacul prin cuvânt cheie, iar potasiul e doar penalizat prin praguri
(`recommender.py:938`), pe date de potasiu care par la fel de inventate.

### 4.8 Limba se schimbă abia după ~5 secunde — **Ridicat**

Cauza e arhitecturală, nu o traducere prin API sau LLM:

1. Numele și textele alimentelor se **randează pe server** în limba din `?lang=`
   (`materialize.py:107` `_api_item_from_rec`, `food_display_name`, `render_explanation`).
2. La schimbarea limbii, `Recommendations.tsx:263–283` face `GET /api/recommendations/stored/{id}?lang=en` și
   **păstrează textul vechi până vine răspunsul**. Sesiunea are cache pe limbă (`recommendationsSessionCache.ts`),
   dar nu e citit în acest efect.
3. O cerere `stored` înseamnă: verificarea tokenului la Supabase Auth (cache pe token), `users`, `recommendations`
   + `feedback` (în paralel), `foods` (591 rânduri; cache doar 10 minute, per proces), apoi
   `feedback_counts`, adică 4–6 drumuri Render → Supabase. Pe instanța „caldă” `/health` (un singur query) răspunde
   în ~0,74 s, deci câteva secunde pentru `stored` e plauzibil; dacă instanța a adormit, **33,7 s** (măsurat).
4. UI-ul (etichete, butoane) se traduce instant, din `locales/*.json`; doar conținutul recomandărilor întârzie,
   ceea ce dă impresia de pagină „pe jumătate tradusă”.

Datele independente de limbă (id-uri, chei de nutrienți, cifre, `facts`) **există deja** în
`explanation_json.facts`; doar că serverul le transformă în text în loc să le trimită. `foods.name_en` există
deja pentru toate cele 591 de alimente (traduceri făcute automat în septembrie, de revizuit). Categoriile nu au
traducere în baza de date (se traduc în frontend prin `resolveFoodCategory`).

## 5. Alte probleme găsite

### 4.A Vitamina D: unități amestecate — **Critic**

`RDI_TABLES.vitamin_d` e în **IU** (600/800), iar catalogul e în **µg**. `_calculate_deficit_from_labs` produce
un deficit de 180 (IU), iar `_calculate_coverage` (`rule_engine.py:1135`) îl compară direct cu porția în µg.
Rezultat: acoperirea vitaminei D e de ~1–3% chiar și pentru somon, deci vitamina D nu urcă niciodată în top.
`facts.py:56` face conversia `/40` corect, dar doar pentru text. (Factor de conversie: 1 µg = 40 IU.)

### 4.B Praguri de laborator și severitate — **Ridicat**

`deficit_calculator.py:86`:

- vitamina D: prag **20 ng/mL**; brief-ul (și multe laboratoare) folosesc 30 ng/mL ca limită minimă.
  P1 cu 25 ng/mL → niciun deficit. TODO: alegerea pragului (20 = suficiență EFSA/IOM pentru populație, 30 =
  Endocrine Society) e o decizie clinică; propun să afișăm intervalul laboratorului când îl avem.
- feritină: **30 ng/mL** pentru ambele sexe; hemoglobina are deja praguri pe sexe (13,5 / 12,0 g/dL).
- severitatea e „aplatizată”: `normalized_deficit = clamp((prag − valoare)/prag, 0,3, 1,5)` (`:550`). Mg 1,6 și
  Mg 1,0 dau deficite 126 și 173 mg, dar orice valoare ușor sub prag sare direct la 30% din necesar.
  `_classify_deficiency` (`rule_engine.py:611`) clasifică apoi severitatea după mg de deficit, nu după cât de jos e
  valoarea de laborator.
- valorile de laborator se salvează fără unitate; un magneziu introdus în mmol/L (0,8, normal) e tratat ca
  deficit sever în mg/dL.

### 4.C Deficite create din orice mențiune — **Ridicat**

`_parse_preferred_nutrients` (`deficit_calculator.py:391`) potrivește `\bvit(?:amina)?\s*d\b`, `\bfier\b`,
`\bcoagulare\b` etc. oriunde în profil + observații. „Iau vitamina D zilnic” sau „tratament pentru coagulare”
creează un deficit (30% din necesar) și textul „ai menționat nevoia de…”. Fără analize, singurele deficite sunt
cele din text, deci un simplu cuvânt schimbă tot topul.

### 4.D Două procente pe același card — **Mediu**

Bara „acoperire” (`RecommendationCard.tsx:448`, `coverage` din motor) și „~X% din necesarul zilnic” din text
(`facts.py:120`) sunt metrici diferite, afișate unul lângă altul.

### 4.E Reguli de categorie care nu se aplică niciodată — **Mediu**

`_category_preference_factor` și `_rebalance_by_category` (`recommender.py:1150–1220`) caută categorii ca
„carne”, „peste & fructe de mare”, „nuci & seminte”, „oua”; catalogul folosește „Proteine/Carne”,
„Proteine/Pește”, „Nuci”. Regula „cel puțin 2 surse animale pentru omnivori” și preferințele pescetariene nu se
aplică. Plafonul pe categorie e 4 (nu 3), iar cheia e categoria completă, deci „Cereale” și „Mese/Cereale” se
numără separat (P1: 5 cereale în top 5).

### 4.F Valorile lipsă devin 0 — **Mediu**

`row_to_food` → `_num(..., default=0)` (`domain/models.py:146, 186`), iar coloanele au `DEFAULT 0`. Nu se poate
distinge „nu conține” de „nu știm”. Contravine regulii „nu inventa valori”.

### 4.G Open Food Facts — **Mediu**

Integrarea existentă (`services/nutrition/food_intelligence_api.py`) e folosită doar de `compatibility_core.py`
pentru un verdict de **alergen (soia)**, prin căutare după nume, cu timeout 0,35 s și cache **în memorie** (6 h,
pierdut la fiecare restart/adormire Render). Nu aduce valori nutriționale, nu validează produse și nu are cache în
Supabase. Căutarea unui aliment generic („Somon la grătar”) în OFF dă produse ambalate arbitrare.

### 4.H Teste și CI — **Mediu**

153 de teste backend trec. `test_recommendations_golden.py` folosește alimente construite în test (ex. „Spanac
fiert”, fier 3,6), nu catalogul real, deci trece deși producția recomandă bagel. Frontend-ul nu are runner de
teste (doar `lint`). Nu există `.github/workflows` → nicio verificare automată la merge.

### Alte observații (Scăzut)

- `MAX_FOODS_TO_SCORE = 45` (`recommender.py:16`): doar 45 de alimente sunt evaluate, preselectate după
  `valoare × deficit` pe datele greșite.
- Textele motorului (`rule_engine.py`, `scoped_rules.py`, fallback-ul din `recommender.py:825`) sunt doar în
  română și se salvează în `matched_rules`/`explanations`, dar nu se afișează (se afișează faptele).
- `ExplanationGenerator` vechi a fost scos; `explanation_json` păstrează și textul RO randat la generare.
- `/api/recommendations/audit/{id}` recalculează totul (~60 s pe Render, notat anterior).

## 6. Infrastructură

| Verificare | Rezultat |
|---|---|
| Render „adoarme”? | **Da.** Prima cerere `/health`: **33,7 s**; următoarele: 0,74 s. Explică o parte importantă din lentoarea raportată (la prima deschidere, iar la schimbarea limbii dacă a trecut timp). |
| Regiune | Vercel servește din **fra1** (Frankfurt). Supabase e în **eu-west-1** (Irlanda), nu în Frankfurt. Regiunea serviciului Render nu se vede din headere; de verificat în Dashboard (dacă e Oregon, fiecare query face un drum transatlantic). |
| CORS | Frontend-ul folosește rewrite-ul Vercel `/api/* → vitabalance-1.onrender.com` (proxy server-side, fără CORS). Backend-ul are `allow_credentials=False` și listă de origini din `CORS_ORIGINS`. OK. |
| Cache HTTP | Răspunsurile API au `Cache-Control: public, max-age=0, must-revalidate` (de la Vercel). Pentru date per utilizator ar trebui `private, no-store`; nu e o scurgere de date (fiecare cerere are token), dar „public” e greșit semantic. |
| Chei | `.env` local cu service role; frontend-ul nu are cheia service role. OK. |

Soluții pentru „adormire”: (a) planul plătit Render Starter (instanța rămâne pornită); (b) un ping periodic la
`/health` la ~10 minute (cron extern gratuit). Varianta (b) e un artificiu care consumă orele gratuite și nu
garantează nimic; recomand (a) dacă aplicația e folosită de alții.

## 7. Întrebări deschise / TODO

1. **Catalogul.** Reconstruiesc valorile din USDA FoodData Central (Foundation + SR Legacy, descărcare publică,
   fără cheie API) cu FDC ID salvat pe fiecare aliment? Alimentele fără corespondent clar (ex. „Vitello Tonnato”,
   „Ou de Secol”) primesc `null` și ies din scor, sau le scoatem din catalog?
2. **Pragul vitaminei D**: 20 sau 30 ng/mL? Propun să salvăm intervalul laboratorului din PDF când există și să
   folosim pragul aplicației doar ca rezervă.
3. **Sursa necesarului**: brief-ul cere EFSA (UE) sau NIH ca rezervă; codul actual e pe NIH/IOM. Propun EFSA DRV
   (2017+), cu vitamina D în µg.
4. **Sarcina / imunitatea** nu sunt câmpuri în profil, ci se deduc din text. Adaug câmpuri explicite (sarcină,
   alăptare, anticoagulante, boală renală, hemocromatoză) în profil? Ar face filtrele sigure și testabile.
5. **Sugestiile de la observații**: le păstrăm, dar marcate ca „bifate”, nu „scrise de tine”?

## 8. Ce propun pentru Faza 1 (după OK)

În ordinea riscului: (1) reguli de contraindicații ca filtre stricte înainte de scor + câmpuri explicite în
profil; (2) catalog validat (USDA, `null` pentru lipsuri, porții realiste per aliment, verificare Atwater +
densitate energetică) printr-o migrare versionată; (3) necesar EFSA în `backend/data/reference_values.py`, unități
corecte pentru vitamina D, praguri pe sexe, severitate după valoarea de laborator, sursa deficitului salvată;
(4) scor după densitate la 100 kcal, penalizare pentru procesate, maximum 3 pe categorie, alternative din aceeași
categorie; (5) avertisment Mifflin-St Jeor; (6) teste golden pe catalogul real. Graficul și cardurile vor folosi
aceeași listă ordonată de backend.
