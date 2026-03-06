"""
Extrage valorile analizelor medicale din textul unui raport medical (română/engleză).
Suportă formate comune: Hemoglobină 13.2 g/dL, Hb: 13.2, Feritină 45 ng/mL, etc.
"""
import re
from typing import Optional, Dict, Any


def extract_lab_values_from_text(text: str) -> Dict[str, Optional[float]]:
    """
    Parsează textul unui raport medical și extrage valorile pentru câmpurile cunoscute.
    Returnează un dict cu chei ca în LabResultItem (hemoglobin, ferritin, vitamin_d, etc.)
    """
    if not text or not isinstance(text, str):
        return _empty_result()

    # Normalizează: lowercase, înlocuiește virgulă cu punct
    normalized = text.lower().replace(",", ".")
    result = _empty_result()

    # Pattern-uri flexibile pentru fiecare biomarker
    # Format: (regex_pattern, key_in_result)
    # Capturăm grupul 1 ca valoare numerică
    patterns = [
        # Hemoglobină - g/dL
        (r"hemoglobina?\s*[:\s]*(\d+\.?\d*)\s*(?:g/dl|g\/dl|g\.d\.l)", "hemoglobin"),
        (r"\bhb\s*[:\s]*(\d+\.?\d*)\s*(?:g/dl|g\/dl)?", "hemoglobin"),
        (r"hemoglobin[ăa]?\s*[:\s]*(\d+\.?\d*)", "hemoglobin"),

        # Feritină - ng/mL
        (r"feritina?\s*[:\s]*(\d+\.?\d*)\s*(?:ng/ml|μg/l)?", "ferritin"),
        (r"ferritin\s*[:\s]*(\d+\.?\d*)", "ferritin"),

        # Vitamina D - ng/mL
        (r"(?:25-?oh-?d|vitamina?\s*d|vit\.?\s*d)\s*[:\s]*(\d+\.?\d*)\s*(?:ng/ml|nmol/l)?", "vitamin_d"),
        (r"vitamina\s*d\s*[:\s]*(\d+\.?\d*)", "vitamin_d"),

        # Vitamina B12 - pg/mL
        (r"(?:vitamina?\s*b12|b12|b\s*12)\s*[:\s]*(\d+\.?\d*)\s*(?:pg/ml|pmol/l)?", "vitamin_b12"),
        (r"cobalamina\s*[:\s]*(\d+\.?\d*)", "vitamin_b12"),

        # Calciu - mg/dL
        (r"calciu[l]?\s*[:\s]*(\d+\.?\d*)\s*(?:mg/dl|mmol/l)?", "calcium"),
        (r"ca\s*[:\s]*(\d+\.?\d*)\s*(?:mg/dl)?", "calcium"),

        # Magneziu - mg/dL
        (r"magneziu\s*[:\s]*(\d+\.?\d*)\s*(?:mg/dl|mmol/l)?", "magnesium"),
        (r"mg\s*[:\s]*(\d+\.?\d*)\s*(?:mg/dl)?", "magnesium"),

        # Zinc - mcg/dL sau μg/dL
        (r"zinc\s*[:\s]*(\d+\.?\d*)\s*(?:mcg/dl|μg/dl)?", "zinc"),
        (r"zn\s*[:\s]*(\d+\.?\d*)", "zinc"),

        # Proteine - g/dL
        (r"proteine?\s*(?:totale?)?\s*[:\s]*(\d+\.?\d*)\s*(?:g/dl)?", "protein"),
        (r"protein[ăa]?\s*[:\s]*(\d+\.?\d*)", "protein"),

        # Folat / Acid folic - ng/mL
        (r"(?:folat|acid\s*folic|vitamina?\s*b9)\s*[:\s]*(\d+\.?\d*)\s*(?:ng/ml)?", "folate"),
        (r"folat\s*[:\s]*(\d+\.?\d*)", "folate"),

        # Vitamina A - μg/dL
        (r"vitamina?\s*a\s*[:\s]*(\d+\.?\d*)\s*(?:μg/dl|mcg/dl)?", "vitamin_a"),
        (r"retinol\s*[:\s]*(\d+\.?\d*)", "vitamin_a"),

        # Iod - μg/L
        (r"iod\s*[:\s]*(\d+\.?\d*)\s*(?:μg/l|mcg/l)?", "iodine"),

        # Vitamina K - PT/INR (de obicei indirect)
        (r"vitamina?\s*k\s*[:\s]*(\d+\.?\d*)", "vitamin_k"),

        # Potasiu - mmol/L
        (r"potasiu\s*[:\s]*(\d+\.?\d*)\s*(?:mmol/l)?", "potassium"),
        (r"k\s*[:\s]*(\d+\.?\d*)\s*(?:mmol/l)?", "potassium"),
    ]

    for pattern, key in patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)
        if match and result[key] is None:
            try:
                val = float(match.group(1))
                if 0 < val < 10000:  # range rezonabil
                    result[key] = val
            except (ValueError, IndexError):
                pass

    # Pattern secundar: "parametru: valoare" generic (dacă nu am găsit)
    generic = [
        (r"hemoglobina?\s*[:\s]*(\d+\.?\d*)", "hemoglobin"),
        (r"feritina?\s*[:\s]*(\d+\.?\d*)", "ferritin"),
        (r"(?:25-?oh|vit\.?\s*d)\s*[:\s]*(\d+\.?\d*)", "vitamin_d"),
        (r"vit\.?\s*b12\s*[:\s]*(\d+\.?\d*)", "vitamin_b12"),
        (r"calciu\s*[:\s]*(\d+\.?\d*)", "calcium"),
        (r"magneziu\s*[:\s]*(\d+\.?\d*)", "magnesium"),
        (r"zinc\s*[:\s]*(\d+\.?\d*)", "zinc"),
        (r"proteine\s*[:\s]*(\d+\.?\d*)", "protein"),
        (r"folat\s*[:\s]*(\d+\.?\d*)", "folate"),
        (r"vit\.?\s*a\s*[:\s]*(\d+\.?\d*)", "vitamin_a"),
        (r"iod\s*[:\s]*(\d+\.?\d*)", "iodine"),
        (r"potasiu\s*[:\s]*(\d+\.?\d*)", "potassium"),
    ]
    for pattern, key in generic:
        if result[key] is None:
            match = re.search(pattern, normalized, re.IGNORECASE)
            if match:
                try:
                    val = float(match.group(1))
                    if 0 < val < 10000:
                        result[key] = val
                except (ValueError, IndexError):
                    pass

    return result


def _empty_result() -> Dict[str, Optional[float]]:
    return {
        "hemoglobin": None,
        "ferritin": None,
        "vitamin_d": None,
        "vitamin_b12": None,
        "calcium": None,
        "magnesium": None,
        "zinc": None,
        "protein": None,
        "folate": None,
        "vitamin_a": None,
        "iodine": None,
        "vitamin_k": None,
        "potassium": None,
    }
