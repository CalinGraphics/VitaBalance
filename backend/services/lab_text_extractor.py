"""
Extrage valorile analizelor medicale din textul unui raport medical (română/engleză).
Suportă formate comune: Hemoglobină 13.2 g/dL, Hb: 13.2, Feritină 45 ng/mL, tabele, etc.
"""
import re
import unicodedata
from typing import Optional, Dict


def _collapse_spaced_letters(text: str) -> str:
    """
    Unește secvențele de litere separate de spații (ex: "H e m o g l o b i n ă" -> "Hemoglobină").
    PDF-urile pot separa fiecare caracter, iar asta rupe matching-ul regex bazat pe cuvinte.
    Regula: doar secvențe de >=4 token-uri alfabetice cu lungime 1 sunt lipite.
    """
    if not text:
        return ""
    parts = re.split(r"(\s+)", text)
    out = []
    acc = []

    def flush_acc():
        nonlocal acc
        if not acc:
            return
        if len(acc) >= 4:
            out.append("".join(acc))
        else:
            out.append(" ".join(acc))
        acc = []

    for p in parts:
        if not p:
            continue
        if p.isspace():
            # spațiile le gestionăm la flush; evităm să acumulăm whitespace în output
            continue
        token = p
        if len(token) == 1 and token.isalpha():
            acc.append(token)
            continue
        flush_acc()
        out.append(token)
    flush_acc()

    # Normalizează spațiile rezultate
    return re.sub(r"\s+", " ", " ".join(out)).strip()


def _normalize_text(text: str) -> str:
    """Lowercase, virgulă -> punct, Unicode NFC, și înlocuire diacritice pentru matching."""
    if not text:
        return ""
    t = text.replace(",", ".")
    t = unicodedata.normalize("NFC", t)
    t = t.lower()
    t = _collapse_spaced_letters(t)
    return t


def extract_lab_values_from_text(text: str) -> Dict[str, Optional[float]]:
    """
    Parsează textul unui raport medical și extrage valorile pentru câmpurile cunoscute.
    Returnează un dict cu chei ca în LabResultItem (hemoglobin, ferritin, vitamin_d, etc.)
    """
    if not text or not isinstance(text, str):
        return _empty_result()

    normalized = _normalize_text(text)
    normalized_lines = [ln.strip() for ln in re.split(r"[\r\n]+", normalized) if ln and ln.strip()]
    # Versiune fără diacritice (pentru PDF-uri care înlocuiesc ă->a etc.)
    normalized_ascii = _remove_diacritics(normalized)
    result = _empty_result()

    # Pattern-uri: (regex, key). Capturăm grupul 1 = valoare numerică.
    # Suportăm: "Parametru: 12.3", "Parametru 12.3", "Parametru  12.3  g/dL", "12.3 Parametru"
    patterns = [
        # Hemoglobină
        # unele PDF-uri pot lipi numărul de etichetă (ex: "Hemoglobină15,2")
        (r"hemoglobina?\s*[:\s]*\s*(\d+[.,]\d+|\d+)\s*(?:g/dl|g\/dl|g\.d\.l)?", "hemoglobin"),
        (r"\bhb\s*[:\s]*\s*(\d+[.,]\d+|\d+)\s*(?:g/dl|g\/dl)?", "hemoglobin"),
        (r"\bhgb\s*[:\s]*\s*(\d+[.,]\d+|\d+)\s*(?:g/dl|g\/dl)?", "hemoglobin"),
        (r"hemoglobin[ăa]?\s*[:\s]*\s*(\d+[.,]\d+|\d+)", "hemoglobin"),
        (r"(\d+[.,]\d+|\d+)\s*(?:g/dl)?\s*hemoglobina?", "hemoglobin"),
        (r"hemoglobina?\s*(\d+[.,]\d+|\d+)", "hemoglobin"),
        # Feritină
        (r"feritina?\s*[:\s]*\s*(\d+[.,]\d+|\d+)\s*(?:ng/ml|μg/l|ug/l)?", "ferritin"),
        (r"ferritin\s*[:\s]*\s*(\d+[.,]\d+|\d+)", "ferritin"),
        (r"feritin[ăa]?\s*[:\s]*\s*(\d+[.,]\d+|\d+)", "ferritin"),
        (r"feritina?\s*(\d+[.,]\d+|\d+)", "ferritin"),
        (r"(\d+[.,]\d+|\d+)\s*(?:ng/ml)?\s*feritina?", "ferritin"),
        # Vitamina D
        (r"(?:25-?oh-?d|vitamina?\s*d|vit\.?\s*d)\s*[:\s]*(\d+[.,]\d+|\d+)\s*(?:ng/ml|nmol/l)?", "vitamin_d"),
        (r"vitamina\s*d\s*[:\s]*(\d+[.,]\d+|\d+)", "vitamin_d"),
        (r"vit\.?\s*d\s*[:\s]*(\d+[.,]\d+|\d+)", "vitamin_d"),
        (r"(\d+[.,]\d+|\d+)\s*(?:ng/ml)?\s*(?:25-?oh-?d|vit\.?\s*d)", "vitamin_d"),
        # Vitamina B12
        (r"(?:vitamina?\s*b\s*12|b\s*12|cobalamina)\s*[:\s]*(\d+[.,]\d+|\d+)\s*(?:pg/ml|pmol/l)?", "vitamin_b12"),
        (r"cobalamina\s*[:\s]*(\d+[.,]\d+|\d+)", "vitamin_b12"),
        (r"vit\.?\s*b12\s*[:\s]*(\d+[.,]\d+|\d+)", "vitamin_b12"),
        (r"b12\s*[:\s]*(\d+[.,]\d+|\d+)", "vitamin_b12"),
        # Calciu
        (r"calciu(?:\s+\w+){0,3}\s*[:\s]*(\d+[.,]\d+|\d+)\s*(?:mg/dl|mmol/l)?", "calcium"),
        (r"\bca\s*[:\s]*(\d+[.,]\d+|\d+)\s*(?:mg/dl|mmol/l)?", "calcium"),
        (r"calciu(?:\s+\w+){0,3}\s+(\d+[.,]\d+|\d+)", "calcium"),
        # Magneziu (evităm confuzia cu Mg = unitate)
        (r"magneziu(?:\s+\w+){0,2}\s*[:\s]*(\d+[.,]\d+|\d+)\s*(?:mg/dl|mmol/l)?", "magnesium"),
        (r"magneziu(?:\s+\w+){0,2}\s+(\d+[.,]\d+|\d+)", "magnesium"),
        # Zinc
        (r"\bzn\s*[:\s]*(\d+[.,]\d+|\d+)", "zinc"),
        (r"zinc\s*[:\s]*(\d+[.,]\d+|\d+)\s*(?:mcg/dl|μg/dl|ug/dl)?", "zinc"),
        (r"zinc\s+(\d+[.,]\d+|\d+)", "zinc"),
        # Proteine
        (r"proteine?\s*(?:totale?)?\s*[:\s]*(\d+[.,]\d+|\d+)\s*(?:g/dl)?", "protein"),
        (r"protein[ăa]?\s*[:\s]*(\d+[.,]\d+|\d+)", "protein"),
        (r"proteine\s+(\d+[.,]\d+|\d+)", "protein"),
        # Folat
        (r"(?:folat|acid\s*folic|vitamina?\s*b9)\s*[:\s]*(\d+[.,]\d+|\d+)\s*(?:ng/ml)?", "folate"),
        (r"folat\s*[:\s]*(\d+[.,]\d+|\d+)", "folate"),
        (r"folat\s+(\d+[.,]\d+|\d+)", "folate"),
        # Vitamina A
        (r"vitamina?\s*a\s*[:\s]*(\d+[.,]\d+|\d+)\s*(?:μg/dl|mcg/dl)?", "vitamin_a"),
        (r"retinol\s*[:\s]*(\d+[.,]\d+|\d+)", "vitamin_a"),
        # Iod
        (r"iod\s*[:\s]*(\d+[.,]\d+|\d+)\s*(?:μg/l|mcg/l)?", "iodine"),
        (r"iod\s+(\d+[.,]\d+|\d+)", "iodine"),
        # Vitamina K
        (r"vitamina?\s*k\s*[:\s]*(\d+[.,]\d+|\d+)", "vitamin_k"),
        # Potasiu (K poate fi confundat cu potasiu - folosim "potasiu" mai întâi)
        (r"potasiu\s*[:\s]*(\d+[.,]\d+|\d+)\s*(?:mmol/l)?", "potassium"),
        (r"potasiu\s+(\d+[.,]\d+|\d+)", "potassium"),
        (r"\bk\s*[:\s]*(\d+[.,]\d+|\d+)\s*mmol/l", "potassium"),
    ]

    def parse_val(s: str) -> Optional[float]:
        s = s.replace(",", ".")
        try:
            v = float(s)
            return v if 0 < v < 10000 else None
        except ValueError:
            return None

    # Căutare în text normalizat
    for pattern, key in patterns:
        if result[key] is not None:
            continue
        match = re.search(pattern, normalized, re.IGNORECASE)
        if match:
            val = parse_val(match.group(1))
            if val is not None:
                result[key] = val

    # Încercare pe variantă fără diacritice (ex: "hemoglobina" în loc de "hemoglobină")
    if normalized_ascii != normalized:
        for pattern, key in patterns:
            if result[key] is not None:
                continue
            match = re.search(pattern, normalized_ascii, re.IGNORECASE)
            if match:
                val = parse_val(match.group(1))
                if val is not None:
                    result[key] = val

    # Pattern-uri generice simple (param: valoare sau param valoare)
    generic = [
        (r"hemoglobina?\s*[:\s]*\s*(\d+[.,]\d+|\d+)", "hemoglobin"),
        (r"feritina?\s*[:\s]*\s*(\d+[.,]\d+|\d+)", "ferritin"),
        (r"(?:25-?oh|vit\.?\s*d)\s*[:\s]*(\d+[.,]\d+|\d+)", "vitamin_d"),
        (r"vit\.?\s*b12\s*[:\s]*(\d+[.,]\d+|\d+)", "vitamin_b12"),
        (r"calciu(?:\s+\w+){0,3}\s*[:\s]*(\d+[.,]\d+|\d+)", "calcium"),
        (r"magneziu(?:\s+\w+){0,2}\s*[:\s]*(\d+[.,]\d+|\d+)", "magnesium"),
        (r"zinc\s*[:\s]*(\d+[.,]\d+|\d+)", "zinc"),
        (r"proteine\s*[:\s]*(\d+[.,]\d+|\d+)", "protein"),
        (r"folat\s*[:\s]*(\d+[.,]\d+|\d+)", "folate"),
        (r"vit\.?\s*a\s*[:\s]*(\d+[.,]\d+|\d+)", "vitamin_a"),
        (r"iod\s*[:\s]*(\d+[.,]\d+|\d+)", "iodine"),
        (r"potasiu\s*[:\s]*(\d+[.,]\d+|\d+)", "potassium"),
    ]
    for pattern, key in generic:
        if result[key] is not None:
            continue
        for text_to_scan in (normalized, normalized_ascii):
            match = re.search(pattern, text_to_scan, re.IGNORECASE)
            if match:
                val = parse_val(match.group(1))
                if val is not None:
                    result[key] = val
                    break

    # Fallback orientat pe linii/tabele:
    # evită cazurile când regex generic prinde capătul inferior al intervalului de referință (ex. "15-150").
    line_key_patterns = {
        "hemoglobin": [r"\bhemoglobina\b", r"\bhgb\b", r"\bhb\b"],
        "ferritin": [r"\bferitina\b", r"\bferritin\b"],
        "vitamin_d": [r"25-?oh-?d", r"\bvit\.?\s*d\b", r"\bvitamina\s*d\b"],
        "vitamin_b12": [r"\bb\s*12\b", r"\bvit\.?\s*b12\b", r"\bcobalamina\b"],
        "calcium": [r"\bcalciu\b", r"\bcalcium\b"],
        "magnesium": [r"\bmagneziu\b", r"\bmagnesium\b"],
        "zinc": [r"\bzinc\b", r"\bzn\b"],
        "protein": [r"\bproteine?\b", r"\bprotein[ae]?\b"],
        "folate": [r"\bfolat\b", r"\bacid\s*folic\b", r"\bvit\.?\s*b9\b"],
        "vitamin_a": [r"\bvit\.?\s*a\b", r"\bvitamina\s*a\b", r"\bretinol\b"],
        "iodine": [r"\biod\b", r"\biodine\b"],
        "vitamin_k": [r"\bvit\.?\s*k\b", r"\bvitamina\s*k\b"],
        "potassium": [r"\bpotasiu\b", r"\bpotassium\b", r"\bk\s*mmol/l\b"],
    }

    def _extract_line_value(line: str) -> Optional[float]:
        # Capturăm numere care NU sunt urmate imediat de un interval (ex "15-150").
        nums = re.finditer(r"(\d+(?:[.,]\d+)?)", line)
        for m in nums:
            tail = line[m.end(): m.end() + 8]
            if re.match(r"\s*[-–]\s*\d", tail):
                continue
            val = parse_val(m.group(1))
            if val is not None:
                return val
        return None

    for key, key_patterns in line_key_patterns.items():
        if result.get(key) is not None:
            continue
        for line in normalized_lines:
            if any(re.search(kp, line, re.IGNORECASE) for kp in key_patterns):
                val = _extract_line_value(line)
                if val is not None:
                    result[key] = val
                    break

    return result


def _remove_diacritics(s: str) -> str:
    """Înlocuiește diacriticele românești cu echivalentul fără diacritice."""
    replacements = {
        "ă": "a", "â": "a", "î": "i", "ș": "s", "ț": "t",
        "Ă": "a", "Â": "a", "Î": "i", "Ș": "s", "Ț": "t",
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    return s


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
