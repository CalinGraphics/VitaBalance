# VitaBalance

Sistem de recomandare cu explicații personalizate pentru deficiențe nutriționale.

## Descriere

VitaBalance este o aplicație web care oferă recomandări nutriționale personalizate bazate pe profilul utilizatorului și rezultatele analizelor medicale. Aplicația folosește algoritmi de machine learning (content-based filtering) pentru a genera recomandări relevante și oferă explicații detaliate pentru fiecare sugestie.

## Caracteristici

- ✅ Profil utilizator complet (vârstă, sex, activitate, dietă, alergii)
- ✅ Introducere rezultate analize medicale
- ✅ Algoritmi de recomandare content-based cu cosine similarity
- ✅ Reguli medicale pentru cazuri critice
- ✅ Explicații detaliate pentru fiecare recomandare
- ✅ Filtrare automată (alergii, restricții dietetice)
- ✅ Visualizări grafice (comparare aport vs necesar)
- ✅ Sistem de feedback
- ✅ Export PDF pentru recomandări
- ✅ Disclaimer medical vizibil
- ✅ Interfață modernă, responsive, cu animații

## Tehnologii

### Backend
- Python 3.10+
- FastAPI
- SQLAlchemy
- SQLite
- NumPy, Pandas

### Frontend
- React 18 + TypeScript
- Vite
- Tailwind CSS
- Framer Motion (animații)
- Recharts (grafice)
- Axios
- jsPDF

## Instalare și Rulare

### Backend

```bash
cd backend
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed_data.py  # Populează baza de date cu alimente
uvicorn main:app --reload
```

Backend-ul va rula pe `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend-ul va rula pe `http://localhost:3000`

## Structura Proiectului

```
VitaBalance/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── seed_data.py
│   └── services/
│       ├── deficit_calculator.py
│       ├── recommender.py
│       └── explanation_generator.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx
│   │   │   ├── Disclaimer.tsx
│   │   │   ├── ProfileForm.tsx
│   │   │   ├── LabResultsForm.tsx
│   │   │   ├── Recommendations.tsx
│   │   │   ├── RecommendationCard.tsx
│   │   │   └── NutrientChart.tsx
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
└── README.md
```

## Algoritmi

### Calculul Deficitelor
- Folosește RDI (Recommended Daily Intake) bazat pe vârstă, sex, activitate
- Prioritizează rezultatele analizelor medicale când sunt disponibile
- Estimează aportul curent bazat pe tipul de dietă

### Scorarea Alimentelor
- Content-based filtering cu cosine similarity
- Vectori nutriționali normalizați
- Aplicare penalități pentru alergii și incompatibilități
- Reguli medicale pentru cazuri critice (ferritin < 15, vitamina D < 20, etc.)

### Explicații
- Explicații detaliate pentru fiecare recomandare
- Calculul acoperirii deficitului
- Sfaturi pentru combinări favorabile
- Alternative similare

## Disclaimer

Această aplicație oferă sugestii generale și nu înlocuiește consultul medical. Pentru probleme de sănătate, vă rugăm să consultați un specialist.

## Licență

Proiect realizat pentru licență 2026.

