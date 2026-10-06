"""Pacienții-tip (tests/golden/*.json): datele și așteptările clinice, citite o singură dată."""
from __future__ import annotations

import json
from pathlib import Path

GOLDEN_DIR = Path(__file__).resolve().parent
PATIENTS = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(GOLDEN_DIR.glob("p*.json"))]
