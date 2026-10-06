"""
Serializarea explicațiilor pentru DB și API.

Recomandările noi salvează doar FAPTE (explanation_json.facts), independente de limbă; textul RO/EN se construiește
în frontend din șabloanele din locales/{ro,en}.json. Coloanele vechi (explanation, reasons, tips) rămân goale
pentru rândurile noi și sunt citite doar pentru rândurile vechi, fără fapte.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from services.explanations.facts import has_facts, parse_explanation_json


def explanation_to_db_fields(facts: Dict[str, Any]) -> Dict[str, Any]:
    """Câmpuri pentru insert în `recommendations` (coloanele text vechi rămân goale)."""
    return {
        "explanation": "",
        "portion_suggested": float((facts.get("portion") or {}).get("amount") or 0),
        "explanation_json": {"facts": facts},
        "reasons": [],
        "tips": [],
    }


def facts_from_row(explanation_json: Any) -> Optional[Dict[str, Any]]:
    data = parse_explanation_json(explanation_json)
    return data["facts"] if data and has_facts(data) else None


def legacy_explanation(row: Dict[str, Any]) -> Dict[str, Any]:
    """Textul salvat (RO) al unui rând vechi, fără fapte; se afișează așa cum e până la regenerare."""
    data = parse_explanation_json(row.get("explanation_json")) or {}
    return {
        "text": str(data.get("text") or row.get("explanation") or ""),
        "reasons": list(data.get("reasons") or row.get("reasons") or []),
        "tips": list(data.get("tips") or row.get("tips") or []),
    }
