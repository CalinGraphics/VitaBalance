"""
Limitele de laborator folosite ca să decidem dacă un marker e sub interval și cât de mult (severitatea).

Valorile se introduc fără unitate; se presupune unitatea de mai jos (cea afișată în formularul de analize).
Severitatea:
- unde există benzi publicate (hemoglobină WHO, vitamina D, vitamina C, iod, potasiu) le folosim pe acelea;
- altfel, după cât de mult e valoarea sub limita minimă: < 10% ușor, 10–25% moderat, ≥ 25% sever
  (regulă de modelare a aplicației, nu o clasificare clinică publicată).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

MILD, MODERATE, SEVERE = "mild", "moderate", "severe"
SEVERITY_WEIGHT = {MILD: 1.0, MODERATE: 2.0, SEVERE: 3.0}


@dataclass(frozen=True)
class LabRange:
    marker: str           # coloana din lab_results
    nutrient: str         # nutrientul pe care îl țintesc alimentele
    unit: str
    low_m: float
    low_f: float
    source: str
    # benzi (prag_sever, prag_moderat): valoare < prag_sever => sever; < prag_moderat => moderat; altfel ușor
    bands_m: Optional[Tuple[float, float]] = None
    bands_f: Optional[Tuple[float, float]] = None
    high: Optional[float] = None  # limita maximă, când o valoare mare schimbă recomandările (ex. potasiu)

    def low(self, sex: str, pregnant: bool = False) -> float:
        if self.marker == "hemoglobin" and pregnant:
            return 11.0
        if sex == "M":
            return self.low_m
        if sex == "F":
            return self.low_f
        return max(self.low_m, self.low_f)  # sex necunoscut: limita mai prudentă

    def bands(self, sex: str, pregnant: bool = False) -> Optional[Tuple[float, float]]:
        if self.marker == "hemoglobin" and pregnant:
            return (7.0, 10.0)
        if sex == "F":
            return self.bands_f
        return self.bands_m


LAB_RANGES: Dict[str, LabRange] = {
    # WHO, „Haemoglobin concentrations for the diagnosis of anaemia and assessment of severity”,
    # WHO/NMH/NHD/MNM/11.1 (2011): anemie < 13,0 g/dL bărbați, < 12,0 femei, < 11,0 sarcină.
    # Severitate: sever < 8,0 (sarcină < 7,0), moderat 8,0–10,9 (sarcină 7,0–9,9), ușor peste.
    "hemoglobin": LabRange("hemoglobin", "iron", "g/dL", 13.0, 12.0, "WHO 2011, WHO/NMH/NHD/MNM/11.1",
                           bands_m=(8.0, 11.0), bands_f=(8.0, 11.0)),
    # WHO, „Guideline on use of ferritin concentrations to assess iron status in individuals and populations” (2020):
    # deficit de fier < 15 µg/L (= ng/mL) la adulți, ACEEAȘI limită pentru ambele sexe (WHO nu are praguri pe sexe).
    # TODO: multe laboratoare raportează limita minimă 30 ng/mL la bărbați; dacă vrem intervalul laboratorului,
    # trebuie citit din buletin. În prezența inflamației WHO recomandă < 70 µg/L — nu avem PCR, deci nu aplicăm.
    "ferritin": LabRange("ferritin", "iron", "ng/mL", 15.0, 15.0, "WHO 2020, ferritin guideline"),
    # 25(OH)D: limita de 30 ng/mL (decizie de produs, 7 oct. 2026), cu benzile Endocrine Society
    # (Holick et al., J Clin Endocrinol Metab 2011;96:1911): deficit < 20 ng/mL, insuficiență 21–29 ng/mL;
    # < 10 ng/mL tratat ca sever (deficit sever, uzual în ghiduri).
    "vitamin_d": LabRange("vitamin_d", "vitamin_d", "ng/mL", 30.0, 30.0, "Endocrine Society 2011",
                          bands_m=(10.0, 20.0), bands_f=(10.0, 20.0)),
    # B12 seric < 200 pg/mL (148 pmol/L): Devalia et al., BCSH guideline, Br J Haematol 2014;166:496.
    "vitamin_b12": LabRange("vitamin_b12", "vitamin_b12", "pg/mL", 200.0, 200.0, "BCSH 2014, Br J Haematol 166:496"),
    # Magneziu seric < 1,7 mg/dL (0,70 mmol/L): limita uzuală a intervalului de referință (Costello et al.,
    # Adv Nutr 2016;7:977, propun 0,85 mmol/L ca prag mai sensibil — TODO dacă vrem pragul mai strict).
    "magnesium": LabRange("magnesium", "magnesium", "mg/dL", 1.7, 1.7, "interval de referință uzual; Costello 2016"),
    # Calciu total < 8,5 mg/dL: limita uzuală a intervalului de referință pentru adulți.
    "calcium": LabRange("calcium", "calcium", "mg/dL", 8.5, 8.5, "interval de referință uzual"),
    # Proteine totale < 6,0 g/dL: limita uzuală a intervalului de referință.
    "protein": LabRange("protein", "protein", "g/dL", 6.0, 6.0, "interval de referință uzual"),
    # Zinc seric < 70 µg/dL (dimineața, à jeun): IZiNCG Technical Document #1, Food Nutr Bull 2004;25:S99.
    "zinc": LabRange("zinc", "zinc", "µg/dL", 70.0, 70.0, "IZiNCG 2004"),
    # Folat seric < 3 ng/mL (6,8 nmol/L): WHO, „Serum and red blood cell folate concentrations” VMNIS 2015.
    "folate": LabRange("folate", "folate", "ng/mL", 3.0, 3.0, "WHO 2015, VMNIS"),
    # Retinol seric < 20 µg/dL (0,70 µmol/L): WHO, „Serum retinol concentrations” VMNIS 2011.
    "vitamin_a": LabRange("vitamin_a", "vitamin_a", "µg/dL", 20.0, 20.0, "WHO 2011, VMNIS"),
    # Acid ascorbic plasmatic: < 23 µmol/L hipovitaminoză, < 11 µmol/L deficit (Schleicher et al., Am J Clin Nutr
    # 2009;90:1252). Benzi: sever < 11, moderat 11–17 (TODO: limita de 17 e alegerea aplicației), ușor 17–23.
    "vitamin_c": LabRange("vitamin_c", "vitamin_c", "µmol/L", 23.0, 23.0, "Schleicher 2009, AJCN 90:1252",
                          bands_m=(11.0, 17.0), bands_f=(11.0, 17.0)),
    # Iod urinar < 100 µg/L: WHO/UNICEF/ICCIDD 2007; benzi WHO: sever < 20, moderat 20–49, ușor 50–99.
    # Observație: e un indicator populațional, nu individual (WHO) — îl folosim cu această limită.
    "iodine": LabRange("iodine", "iodine", "µg/L", 100.0, 100.0, "WHO 2007",
                       bands_m=(20.0, 50.0), bands_f=(20.0, 50.0)),
    # Potasiu seric: interval 3,5–5,0 mmol/L. Hipokaliemie: ușoară 3,0–3,4, moderată 2,5–2,9, severă < 2,5
    # (Kardalas et al., Endocr Connect 2018;7:R135). Hiperkaliemie > 5,0 → limităm potasiul din alimente.
    "potassium": LabRange("potassium", "potassium", "mmol/L", 3.5, 3.5, "Kardalas 2018, Endocr Connect 7:R135",
                          bands_m=(2.5, 3.0), bands_f=(2.5, 3.0), high=5.0),
}


def severity_for(lab: LabRange, value: float, sex: str, pregnant: bool = False) -> Optional[str]:
    """None dacă valoarea nu e sub limita minimă."""
    low = lab.low(sex, pregnant)
    if value >= low:
        return None
    bands = lab.bands(sex, pregnant)
    if bands:
        severe_below, moderate_below = bands
        if value < severe_below:
            return SEVERE
        if value < moderate_below:
            return MODERATE
        return MILD
    ratio = (low - value) / low
    if ratio >= 0.25:
        return SEVERE
    if ratio >= 0.10:
        return MODERATE
    return MILD
