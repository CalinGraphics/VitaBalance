# 🚀 Ghid de Pornire - VitaBalance

Bun venit la **VitaBalance**! Acest ghid te va ajuta să pornești aplicația rapid.

## 📋 Cerințe Preliminare

- **Python 3.10+** instalat
- **Node.js 18+** și npm instalat
- **Git** (opțional, pentru versionare)

## 🔧 Instalare și Configurare

### 1. Backend (FastAPI)

```bash
# Navighează în folderul backend
cd backend

# Creează un mediu virtual (recomandat)
python -m venv venv

# Activează mediul virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalează dependențele
python.exe -m pip install -r requirements.txt

# Populează baza de date cu alimente
python seed_data.py

# Pornește serverul
python run.py
# SAU
uvicorn main:app --reload
```

Backend-ul va rula pe **http://localhost:8000**

Documentația API (Swagger) este disponibilă la: **http://localhost:8000/docs**

### 2. Frontend (React)

Deschide un **nou terminal** și:

```bash
# Navighează în folderul frontend
cd frontend

# Instalează dependențele
npm install

# Pornește aplicația
npm run dev
```

Frontend-ul va rula pe **http://localhost:3000**

## 🎯 Utilizare

1. **Deschide aplicația** în browser: http://localhost:3000
2. **Completează profilul** cu informațiile tale
3. **Introdu rezultatele analizelor** (opțional)
4. **Vezi recomandările** personalizate generate de sistem
5. **Dă feedback** pentru a îmbunătăți recomandările viitoare
6. **Exportă PDF** pentru a discuta cu medicul tău

## 📁 Structura Proiectului

```
VitaBalance/
├── backend/              # API FastAPI
│   ├── main.py          # Aplicația principală
│   ├── models.py        # Modele baza de date
│   ├── services/        # Logica de business
│   └── seed_data.py     # Script populare date
├── frontend/            # Aplicația React
│   ├── src/
│   │   ├── components/  # Componente React
│   │   └── App.tsx      # Componenta principală
│   └── package.json
└── README.md
```

## 🐛 Rezolvarea Problemelor

### Backend nu pornește
- Verifică că Python 3.10+ este instalat: `python --version`
- Verifică că toate dependențele sunt instalate: `pip list`
- Verifică că portul 8000 nu este ocupat

### Frontend nu pornește
- Verifică că Node.js este instalat: `node --version`
- Șterge `node_modules` și reinstalează: `rm -rf node_modules && npm install`
- Verifică că portul 3000 nu este ocupat

### Eroare la conectarea la API
- Asigură-te că backend-ul rulează pe portul 8000
- Verifică că CORS este configurat corect în `backend/main.py`

### Baza de date goală
- Rulează scriptul de populare: `python backend/seed_data.py`

## 📚 Resurse Suplimentare

- **Documentația FastAPI**: https://fastapi.tiangolo.com/
- **Documentația React**: https://react.dev/
- **Tailwind CSS**: https://tailwindcss.com/

## 💡 Tips

- Folosește **Swagger UI** (http://localhost:8000/docs) pentru a testa API-ul
- Verifică console-ul browser-ului pentru erori JavaScript
- Verifică log-urile serverului pentru erori backend

## 🎉 Succes!

Aplicația ar trebui să funcționeze perfect acum. Dacă întâmpini probleme, verifică secțiunea de rezolvare a problemelor sau consultă documentația.

**Bucură-te de recomandările nutriționale personalizate!** 🥗

