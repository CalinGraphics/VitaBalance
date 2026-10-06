"""
Necesarul zilnic de referință pentru adulți — o singură sursă: EFSA Dietary Reference Values (DRV).

Rezumat oficial: EFSA, „Dietary Reference Values for nutrients – Summary report”, EFSA Supporting Publications
2017:e15121 (actualizat 2019), https://doi.org/10.2903/sp.efsa.2017.e15121
Se folosește PRI (Population Reference Intake) acolo unde există, altfel AI (Adequate Intake).

Unitățile sunt cele din catalogul de alimente (USDA): mg, µg, g. Vitamina D e în µg (1 µg = 40 UI).

Etape de viață: `pregnancy`, `lactation`. Pentru vârste sub 18 ani EFSA are valori separate, care NU sunt în tabel:
TODO — aplicația cere vârsta ≥ 18 pentru recomandări personalizate sau adăugăm valorile pentru copii/adolescenți.
"""
from __future__ import annotations

from typing import Dict, Optional

# nutrient -> (unitate, sursă) ; valorile sunt în funcția reference_intake de mai jos
UNITS: Dict[str, str] = {
    "iron": "mg", "calcium": "mg", "magnesium": "mg", "zinc": "mg", "potassium": "mg", "vitamin_c": "mg",
    "vitamin_d": "µg", "vitamin_b12": "µg", "folate": "µg", "vitamin_a": "µg", "iodine": "µg", "vitamin_k": "µg",
    "protein": "g",
}

SOURCES: Dict[str, str] = {
    # Fier: EFSA NDA Panel, EFSA Journal 2015;13(10):4254. PRI bărbați 11 mg; femei premenopauză 16 mg,
    # postmenopauză 11 mg; sarcină și alăptare 16 mg.
    "iron": "EFSA 2015, EFSA Journal 13(10):4254",
    # Calciu: EFSA Journal 2015;13(5):4101. PRI 18–24 ani 1000 mg; ≥ 25 ani 950 mg; sarcina/alăptarea nu schimbă PRI.
    "calcium": "EFSA 2015, EFSA Journal 13(5):4101",
    # Vitamina D: EFSA Journal 2016;14(10):4547. AI 15 µg/zi pentru adulți, inclusiv sarcină și alăptare.
    "vitamin_d": "EFSA 2016, EFSA Journal 14(10):4547",
    # Vitamina B12: EFSA Journal 2015;13(7):4150. AI 4,0 µg adulți; sarcină 4,5 µg; alăptare 5,0 µg.
    "vitamin_b12": "EFSA 2015, EFSA Journal 13(7):4150",
    # Magneziu: EFSA Journal 2015;13(7):4186. AI bărbați 350 mg, femei 300 mg (inclusiv sarcină/alăptare).
    "magnesium": "EFSA 2015, EFSA Journal 13(7):4186",
    # Proteine: EFSA Journal 2012;10(2):2557. PRI 0,83 g/kg corp/zi adulți; sarcină +1 / +9 / +28 g/zi pe trimestre
    # (folosim +9 g, valoarea trimestrului 2, când trimestrul nu e cunoscut); alăptare +19 g/zi (primele 6 luni).
    "protein": "EFSA 2012, EFSA Journal 10(2):2557",
    # Zinc: EFSA Journal 2014;12(10):3844. PRI depinde de aportul de fitați (LPI 300/600/900/1200 mg/zi).
    # Bărbați: 9,4 / 11,7 / 14,0 / 16,3 mg; femei: 7,5 / 9,3 / 11,0 / 12,7 mg; sarcină +1,6 mg; alăptare +2,9 mg.
    # Alegem LPI 600 mg/zi pentru omnivori și 900 mg/zi pentru vegetarieni/vegani (aport mai mare de cereale
    # integrale și leguminoase). TODO: alegerea LPI per dietă e o aproximare de modelare, nu o valoare EFSA.
    "zinc": "EFSA 2014, EFSA Journal 12(10):3844",
    # Folat: EFSA Journal 2014;12(11):3893. PRI 330 µg DFE adulți; sarcină AI 600 µg; alăptare 500 µg.
    "folate": "EFSA 2014, EFSA Journal 12(11):3893",
    # Vitamina A: EFSA Journal 2015;13(3):4028. PRI bărbați 750 µg RE, femei 650 µg; sarcină 700 µg; alăptare 1300 µg.
    "vitamin_a": "EFSA 2015, EFSA Journal 13(3):4028",
    # Vitamina C: EFSA Journal 2013;11(11):3418. PRI bărbați 110 mg, femei 95 mg; sarcină +10 mg; alăptare +60 mg.
    "vitamin_c": "EFSA 2013, EFSA Journal 11(11):3418",
    # Iod: EFSA Journal 2014;12(5):3660. AI 150 µg adulți; sarcină și alăptare 200 µg.
    "iodine": "EFSA 2014, EFSA Journal 12(5):3660",
    # Vitamina K: EFSA Journal 2017;15(5):4780. AI 70 µg filochinonă/zi adulți (1 µg/kg corp), inclusiv sarcină/alăptare.
    "vitamin_k": "EFSA 2017, EFSA Journal 15(5):4780",
    # Potasiu: EFSA Journal 2016;14(10):4592. AI 3500 mg adulți, inclusiv sarcină; alăptare 4000 mg.
    "potassium": "EFSA 2016, EFSA Journal 14(10):4592",
}

PROTEIN_G_PER_KG = 0.83
PROTEIN_PREGNANCY_EXTRA_G = 9.0
PROTEIN_LACTATION_EXTRA_G = 19.0
DEFAULT_WEIGHT_KG = 70.0


def _sex(sex: Optional[str]) -> str:
    s = (sex or "").strip().upper()
    return s if s in ("M", "F") else "other"


def reference_intake(
    nutrient: str,
    *,
    sex: Optional[str],
    age: Optional[int],
    weight_kg: Optional[float] = None,
    pregnant: bool = False,
    lactating: bool = False,
    diet: Optional[str] = None,
) -> Optional[float]:
    """
    Necesarul zilnic EFSA (unitatea din UNITS) sau None dacă nutrientul nu are valoare de referință.
    Sexul „other”: media valorilor pentru bărbați și femei (alegere de modelare, documentată aici).
    Sarcina/alăptarea se aplică doar dacă sexul nu e „M”.
    """
    s = _sex(sex)
    age = int(age or 30)
    pregnant = pregnant and s != "M"
    lactating = lactating and s != "M" and not pregnant

    def by_sex(m: float, f: float) -> float:
        return m if s == "M" else f if s == "F" else (m + f) / 2

    if nutrient == "iron":
        # Fără informații despre menopauză folosim vârsta de 50 de ani ca aproximare (TODO: întrebare în profil).
        if pregnant or lactating:
            return 16.0
        return by_sex(11.0, 16.0 if age < 50 else 11.0)
    if nutrient == "calcium":
        return 1000.0 if age < 25 else 950.0
    if nutrient == "vitamin_d":
        return 15.0
    if nutrient == "vitamin_b12":
        return 4.5 if pregnant else 5.0 if lactating else 4.0
    if nutrient == "magnesium":
        return 300.0 if (pregnant or lactating) else by_sex(350.0, 300.0)
    if nutrient == "protein":
        weight = weight_kg if weight_kg and weight_kg > 0 else DEFAULT_WEIGHT_KG
        extra = PROTEIN_PREGNANCY_EXTRA_G if pregnant else PROTEIN_LACTATION_EXTRA_G if lactating else 0.0
        return round(PROTEIN_G_PER_KG * weight + extra, 1)
    if nutrient == "zinc":
        plant_based = (diet or "").lower() in ("vegan", "vegetarian")
        base = by_sex(14.0, 11.0) if plant_based else by_sex(11.7, 9.3)
        return round(base + (1.6 if pregnant else 2.9 if lactating else 0.0), 1)
    if nutrient == "folate":
        return 600.0 if pregnant else 500.0 if lactating else 330.0
    if nutrient == "vitamin_a":
        return 700.0 if pregnant else 1300.0 if lactating else by_sex(750.0, 650.0)
    if nutrient == "vitamin_c":
        base = by_sex(110.0, 95.0)
        return base + (10.0 if pregnant else 60.0 if lactating else 0.0)
    if nutrient == "iodine":
        return 200.0 if (pregnant or lactating) else 150.0
    if nutrient == "vitamin_k":
        return 70.0
    if nutrient == "potassium":
        return 4000.0 if lactating else 3500.0
    return None
