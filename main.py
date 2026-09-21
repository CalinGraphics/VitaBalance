"""
Punct de intrare pentru hosting care rulează din rădăcina repo-ului (ex. un serviciu Render la care
Root Directory nu este setat pe `backend`): expune aceeași aplicație FastAPI ca `backend/main.py`,
deci `uvicorn main:app` funcționează atât de aici, cât și din `backend/`.

Dacă serviciul are Root Directory = backend (varianta recomandată, vezi render.yaml), fișierul acesta
nu este folosit deloc.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent / "backend"

# backend/main.py importă `config`, `services.*`, `repositories.*` relativ la folderul backend.
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Încărcat sub alt nume de modul, ca importul să nu se suprascrie peste modulul curent („main").
_spec = importlib.util.spec_from_file_location("vitabalance_backend_main", BACKEND_DIR / "main.py")
if _spec is None or _spec.loader is None:  # pragma: no cover
    raise ImportError(f"Nu am găsit aplicația în {BACKEND_DIR / 'main.py'}")
_module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)

app = _module.app
