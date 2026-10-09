"""
Matricea aliment × nutrient (valori la 100 g, NaN = necunoscut), construită o singură dată pentru un catalog și
refolosită la fiecare recomandare. Scorul pe nutrient se calculează vectorizat (numpy) pentru toate alimentele;
doar alimentele care contează sunt transformate apoi în componente explicabile (scoring.Component).
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

import numpy as np

from domain.models import FoodItem
from services.nutrition.needs import NUTRIENTS
from services.recommendations.cache import catalog_signature

# Fierul din carne, pasăre, pește și fructe de mare e parțial hem; din ouă, lactate și plante e doar non-hem.
HEME_IRON_SOURCES = frozenset({"meat", "poultry", "fish", "shellfish"})


@dataclass(frozen=True)
class FoodMatrix:
    foods: Tuple[FoodItem, ...]
    index: Dict[int, int]            # food.id -> rând
    values: np.ndarray               # (n_foods, n_nutrients), NaN = necunoscut
    kcal: np.ndarray                 # (n_foods,), NaN = necunoscut
    portion: np.ndarray              # (n_foods,), grame; NaN dacă lipsește
    high_oxalate: np.ndarray         # (n_foods,), bool
    heme_iron: np.ndarray            # (n_foods,), bool — carne, pasăre, pește, fructe de mare (fier hem)
    columns: Dict[str, int]          # nutrient -> coloană

    def column(self, nutrient: str) -> np.ndarray:
        return self.values[:, self.columns[nutrient]]


def _num(v) -> float:
    return float("nan") if v is None else float(v)


def build_matrix(foods: Sequence[FoodItem]) -> FoodMatrix:
    foods = tuple(foods)
    columns = {n: i for i, n in enumerate(NUTRIENTS)}
    values = np.array([[_num(getattr(f, n, None)) for n in NUTRIENTS] for f in foods], dtype=float).reshape(len(foods), len(NUTRIENTS))
    return FoodMatrix(
        foods=foods,
        index={f.id: i for i, f in enumerate(foods)},
        values=values,
        kcal=np.array([_num(f.calories) for f in foods], dtype=float),
        portion=np.array([_num(f.portion_g) for f in foods], dtype=float),
        high_oxalate=np.array([f.has_flag("high_oxalate") for f in foods], dtype=bool),
        heme_iron=np.array([f.animal_source in HEME_IRON_SOURCES for f in foods], dtype=bool),
        columns=columns,
    )


_lock = threading.Lock()
_cache: Dict[Tuple[Tuple[int, ...], str], FoodMatrix] = {}


def matrix_for(foods: Sequence[FoodItem]) -> FoodMatrix:
    """
    Același catalog -> aceeași matrice, construită o singură dată. Cheia include valorile, nu doar id-urile: catalogul
    se reîncarcă din DB la 10 minute, iar o valoare corectată trebuie să ajungă în scor fără repornirea serverului.
    """
    key = (tuple(f.id for f in foods), catalog_signature(foods, validated_only=False))
    with _lock:
        m = _cache.get(key)
        if m is None:
            if len(_cache) > 8:
                _cache.clear()
            m = build_matrix(foods)
            _cache[key] = m
    return m


def nutrient_scores(
    m: FoodMatrix, nutrient: str, daily_ref: float, weight: float, *, density_cap: float, min_share: float,
    min_kcal: float, bio: np.ndarray,
) -> Dict[str, np.ndarray]:
    """Pentru toate alimentele: densitate, cota din porție și contribuția (0 unde nutrientul nu contează)."""
    v100 = m.column(nutrient)
    with np.errstate(invalid="ignore", divide="ignore"):
        per100kcal = v100 / np.maximum(m.kcal, min_kcal) * 100.0
        density = per100kcal / daily_ref
        amount = v100 * m.portion / 100.0
        share = amount / daily_ref
    valid = ~np.isnan(v100) & (v100 > 0) & ~np.isnan(m.kcal) & ~np.isnan(m.portion) & (share >= min_share)
    contribution = np.where(valid, weight * np.minimum(density, density_cap) * bio, 0.0)
    return {"valid": valid, "per100": v100, "per100kcal": per100kcal, "density": density, "amount": amount,
            "share": share, "bio": bio, "contribution": contribution}


def rows(m: FoodMatrix, foods: List[FoodItem]) -> np.ndarray:
    return np.array([m.index[f.id] for f in foods], dtype=int)
