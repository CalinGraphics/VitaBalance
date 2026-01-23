# Instrucțiuni de Pornire - VitaBalance

## Setup Inițial (doar prima dată)

### Backend

1. **Navighează în folderul backend:**
```bash
cd backend
```

2. **Activează mediul virtual:**
```bash
venv\Scripts\activate
```

3. **Instalează dependențele:**
```bash
pip install -r requirements.txt
```

4. **Generează datele alimentelor (doar prima dată):**
```bash
python scripts/generate_foods.py
```

### Frontend

1. **Navighează în folderul frontend:**
```bash
cd frontend
```

2. **Instalează dependențele:**
```bash
npm install
```

---

## Rularea Sistemului (de fiecare dată)

### Pasul 1: Pornește Backend-ul

Într-un terminal:

```bash
cd backend
venv\Scripts\activate
python run.py
```

Backend-ul va rula pe: **http://localhost:8000**

Poți verifica că funcționează accesând: http://localhost:8000/docs (documentație API)

### Pasul 2: Pornește Frontend-ul

Într-un alt terminal:

```bash
cd frontend
npm run dev
```

Frontend-ul va rula pe: **http://localhost:5173** (sau alt port dacă 5173 e ocupat)

---

## Verificare

1. Backend: http://localhost:8000/docs
2. Frontend: http://localhost:5173

---

## Notă

- **Backend-ul trebuie să fie pornit înainte de frontend**
- Dacă schimbi codul backend, serverul se reîncarcă automat (reload=True)
- Dacă schimbi codul frontend, Vite reîncarcă automat pagina în browser
