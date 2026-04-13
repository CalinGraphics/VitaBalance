"""Încărcare reguli clinice din JSON + normalizare text pentru matching robust."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict


def normalize_clinical_text(value: str) -> str:
    raw = (value or "").strip().lower().replace("_", " ").replace("-", " ")
    folded = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", folded).strip()


def load_medical_rules_config() -> Dict[str, Any]:
    cfg_path = Path(__file__).resolve().parents[1] / "config" / "medical_rules.json"
    if not cfg_path.exists():
        return {"condition_food_rules": [], "condition_trigger_rules": []}
    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"condition_food_rules": [], "condition_trigger_rules": []}
        data.setdefault("condition_food_rules", [])
        data.setdefault("condition_trigger_rules", [])
        return data
    except Exception:
        return {"condition_food_rules": [], "condition_trigger_rules": []}
