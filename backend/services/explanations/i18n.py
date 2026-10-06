"""
Catalog RO/EN pentru explicațiile recomandărilor.

Explicațiile se construiesc din FAPTE structurate (vezi explanation_facts.py), nu din text liber: aici stau doar
etichetele și șabloanele de propoziții, pe limbi. Fiecare cheie trebuie să existe în ambele limbi
(verificat de tests/test_explanation_render.py).
"""
from __future__ import annotations

from typing import Dict

SUPPORTED_LANGS = ("ro", "en")
DEFAULT_LANG = "ro"


def normalize_lang(value) -> str:
    """'en', 'EN', 'en-GB', 'en_US' -> 'en'; orice altceva -> 'ro'."""
    raw = str(value or "").strip().lower().replace("_", "-").split("-")[0]
    return raw if raw in SUPPORTED_LANGS else DEFAULT_LANG


# Unitatea în care sunt exprimate cantitățile per porție (aceeași în ambele limbi).
NUTRIENT_UNITS: Dict[str, str] = {
    "protein": "g",
    "iron": "mg", "calcium": "mg", "magnesium": "mg", "zinc": "mg", "vitamin_c": "mg", "potassium": "mg",
    "vitamin_b12": "µg", "folate": "µg", "vitamin_a": "µg", "iodine": "µg", "vitamin_k": "µg", "vitamin_d": "µg",
}

NUTRIENT_LABELS: Dict[str, Dict[str, str]] = {
    "ro": {
        "iron": "fier", "calcium": "calciu", "vitamin_d": "vitamina D", "vitamin_b12": "vitamina B12",
        "magnesium": "magneziu", "protein": "proteine", "zinc": "zinc", "folate": "folat (B9)",
        "vitamin_a": "vitamina A", "vitamin_c": "vitamina C", "iodine": "iod", "vitamin_k": "vitamina K",
        "potassium": "potasiu",
    },
    "en": {
        "iron": "iron", "calcium": "calcium", "vitamin_d": "vitamin D", "vitamin_b12": "vitamin B12",
        "magnesium": "magnesium", "protein": "protein", "zinc": "zinc", "folate": "folate (B9)",
        "vitamin_a": "vitamin A", "vitamin_c": "vitamin C", "iodine": "iodine", "vitamin_k": "vitamin K",
        "potassium": "potassium",
    },
}

# Marker de laborator afișat când diferă de numele nutrientului (fier -> feritină / hemoglobină).
MARKER_LABELS: Dict[str, Dict[str, str]] = {
    "ro": {"ferritin": "Feritină", "hemoglobin": "Hemoglobină"},
    "en": {"ferritin": "Ferritin", "hemoglobin": "Hemoglobin"},
}

DIET_LABELS: Dict[str, Dict[str, str]] = {
    "ro": {"vegan": "dieta vegană", "vegetarian": "dieta vegetariană", "pescatarian": "dieta pescetariană"},
    "en": {"vegan": "a vegan diet", "vegetarian": "a vegetarian diet", "pescatarian": "a pescatarian diet"},
}

ALLERGY_LABELS: Dict[str, Dict[str, str]] = {
    "ro": {"lactoza": "lactoză", "gluten": "gluten", "nuci": "nuci", "oua": "ouă", "soia": "soia", "peste": "pește",
           "crustacee": "crustacee", "arahide": "arahide", "sesam": "susan", "mustar": "muștar", "moluste": "moluște"},
    "en": {"lactoza": "lactose", "gluten": "gluten", "nuci": "tree nuts", "oua": "eggs", "soia": "soy",
           "peste": "fish", "crustacee": "crustaceans", "arahide": "peanuts", "sesam": "sesame", "mustar": "mustard",
           "moluste": "molluscs"},
}

# Afecțiuni cu reguli alimentare: (etichetă, ce s-a respectat). Cheile = ProfileContext.conditions
# (services/nutrition/profile_context.py); restricțiile descriu regulile din rules/contraindications.py.
CONDITION_LABELS: Dict[str, Dict[str, tuple]] = {
    "ro": {
        "pregnancy": ("sarcină", "fără pește sau fructe de mare crude, pește bogat în mercur, ficat sau brânzeturi moi cu mucegai"),
        "lactation": ("alăptare", "fără pește bogat în mercur"),
        "immunocompromised": ("imunitate scăzută", "fără pește sau fructe de mare crude și brânzeturi moi cu mucegai"),
        "anticoagulant": ("tratament anticoagulant", "fără porții foarte bogate în vitamina K, pentru un aport constant"),
        "ckd": ("boală cronică de rinichi", "fără alimente bogate în potasiu; fosforul e limitat"),
        "hemochromatosis": ("hemocromatoză", "fără alimente alese pentru creșterea fierului și fără ficat"),
        "hypertension": ("hipertensiune", "fără alimente bogate în sare"),
        "diabetes": ("diabet", "preferăm porțiile cu puțini carbohidrați disponibili și fără zahăr adăugat"),
        "celiac": ("boală celiacă", "fără gluten"),
        "gout": ("gută", "fără organe și fructe de mare; puțină carne roșie"),
        "cardiovascular": ("colesterol ridicat / risc cardiovascular", "fără mezeluri"),
    },
    "en": {
        "pregnancy": ("pregnancy", "no raw fish or shellfish, high-mercury fish, liver or soft mould-ripened cheese"),
        "lactation": ("breastfeeding", "no high-mercury fish"),
        "immunocompromised": ("weakened immunity", "no raw fish or shellfish and no soft mould-ripened cheese"),
        "anticoagulant": ("anticoagulant treatment", "no portions very high in vitamin K, to keep intake steady"),
        "ckd": ("chronic kidney disease", "no high-potassium foods; phosphorus is limited"),
        "hemochromatosis": ("haemochromatosis", "no foods chosen to raise iron and no liver"),
        "hypertension": ("high blood pressure", "no high-salt foods"),
        "diabetes": ("diabetes", "we prefer portions low in available carbohydrate and without added sugar"),
        "celiac": ("coeliac disease", "gluten-free"),
        "gout": ("gout", "no offal or shellfish; little red meat"),
        "cardiovascular": ("high cholesterol / cardiovascular risk", "no processed meat"),
    },
}

# Șabloane de propoziții. Placeholderele {…} sunt umplute de explanation_renderer.
SENTENCES: Dict[str, Dict[str, str]] = {
    "ro": {
        "and": "și",
        "headline_lab": "**{food}** este recomandat pentru că analizele tale arată valori sub pragul clinic pentru: {list}.",
        "headline_notes": "**{food}** este recomandat pentru că ai menționat nevoia de: {list}.",
        "headline_general": "**{food}** este compatibil cu profilul tău și contribuie la aportul zilnic de: {list}.",
        "headline_none": "**{food}** este o opțiune compatibilă cu profilul și restricțiile tale.",
        "also_notes": "Ai menționat și nevoia de: {list}.",
        "portion_line": "La porția sugerată (~{portion}): {parts}.",
        "portion_part": "{nutrient} ~{amount} {unit} (~{pct}% din necesarul zilnic estimat)",
        "reason_lab": "{marker}: {value} {unit} (prag: {threshold} {unit}) — {food} aduce {per100} {nutrient_unit} {nutrient} la 100 g.",
        "reason_notes": "Ai menționat nevoia de {nutrient}; {food} aduce {per100} {nutrient_unit} la 100 g.",
        "reason_general": "{food} aduce {per100} {nutrient_unit} {nutrient} la 100 g.",
        "reason_diet": "Compatibil cu {diet}.",
        "reason_allergies": "Ales cu respectarea alergiilor declarate: {list}.",
        "reason_condition": "Adaptat pentru {condition}: {restriction}.",
        "reason_no_labs": "Recomandare bazată pe profilul tău; nu ai încă analize introduse.",
        "alt_prefix": "",
    },
    "en": {
        "and": "and",
        "headline_lab": "**{food}** is recommended because your lab results are below the clinical threshold for: {list}.",
        "headline_notes": "**{food}** is recommended because you mentioned needing: {list}.",
        "headline_general": "**{food}** fits your profile and adds to your daily intake of: {list}.",
        "headline_none": "**{food}** is an option compatible with your profile and restrictions.",
        "also_notes": "You also mentioned needing: {list}.",
        "portion_line": "At the suggested portion (~{portion}): {parts}.",
        "portion_part": "{nutrient} ~{amount} {unit} (~{pct}% of the estimated daily need)",
        "reason_lab": "{marker}: {value} {unit} (threshold: {threshold} {unit}) — {food} provides {per100} {nutrient_unit} {nutrient} per 100 g.",
        "reason_notes": "You mentioned needing {nutrient}; {food} provides {per100} {nutrient_unit} per 100 g.",
        "reason_general": "{food} provides {per100} {nutrient_unit} {nutrient} per 100 g.",
        "reason_diet": "Suitable for {diet}.",
        "reason_allergies": "Chosen respecting your declared allergies: {list}.",
        "reason_condition": "Adapted for {condition}: {restriction}.",
        "reason_no_labs": "Recommendation based on your profile; you have not entered lab results yet.",
        "alt_prefix": "",
    },
}

# Sfaturi practice. Fiecare sfat are o sursă (TIP_SOURCES); un sfat fără sursă nu are voie să apară.
TIP_SOURCES: Dict[str, str] = {
    # Hallberg et al., Am J Clin Nutr 1989;49:140 (acidul ascorbic crește absorbția fierului non-hem);
    # Hurrell et al., Br J Nutr 1999;81:289 (polifenolii din ceai/cafea o reduc).
    "iron": "Hallberg 1989 AJCN 49:140; Hurrell 1999 BJN 81:289",
    # Hallberg et al., Am J Clin Nutr 1991;53:112: calciul consumat la aceeași masă scade absorbția fierului.
    "calcium_iron": "Hallberg 1991 AJCN 53:112",
    # Vitaminele D și A sunt liposolubile: Dawson-Hughes et al., J Acad Nutr Diet 2015;115:225 (vitamina D3 se
    # absoarbe mai bine la o masă cu grăsimi); NIH ODS, Vitamin A fact sheet (2023).
    "vitamin_d": "Dawson-Hughes 2015 JAND 115:225",
    "vitamin_a": "NIH ODS 2023 Vitamin A fact sheet",
    # EFSA 2015 (B12): sursele vegetale nu conțin B12 activă în cantități utile; veganii au nevoie de alimente
    # fortificate sau suplimente (NIH ODS, Vitamin B12 fact sheet, 2024).
    "vitamin_b12_vegan": "EFSA 2015 EFSA Journal 13(7):4150; NIH ODS 2024 Vitamin B12",
    # NIH ODS, Vitamin K fact sheet (2021): aport constant la persoanele care iau warfarină.
    "vitamin_k_anticoagulant": "NIH ODS 2021 Vitamin K",
    # Gibson et al., Food Nutr Bull 2010;31:S134: înmuierea și fermentarea reduc fitații și cresc absorbția zincului.
    "zinc": "Gibson 2010 FNB 31:S134",
    # McKillop et al., Br J Nutr 2002;88:681: fierberea prelungită pierde o mare parte din folat; aburul mai puțin.
    "folate": "McKillop 2002 BJN 88:681",
    # Vitamina C se degradează la căldură și în apa de fierbere: Lee & Kader, Postharvest Biol Technol 2000;20:207.
    "vitamin_c": "Lee & Kader 2000 PBT 20:207",
}

TIPS: Dict[str, Dict[str, str]] = {
    "ro": {
        "iron": "Mănâncă-l împreună cu o sursă de vitamina C (ardei, lămâie, kiwi), care ajută absorbția fierului din plante. Ceaiul și cafeaua la aceeași masă o reduc.",
        "calcium_iron": "Calciul consumat la aceeași masă scade absorbția fierului: mănâncă alimentele bogate în calciu la altă masă decât cele pentru fier.",
        "vitamin_d": "Vitamina D se absoarbe mai bine la o masă care conține și puțină grăsime.",
        "vitamin_a": "Vitamina A se absoarbe mai bine împreună cu puțină grăsime (de exemplu un strop de ulei).",
        "vitamin_b12_vegan": "În dieta vegană, B12 vine doar din alimente fortificate sau suplimente. Discută cu medicul despre supliment.",
        "vitamin_k_anticoagulant": "Dacă iei warfarină sau acenocumarol, păstrează constantă cantitatea de verdețuri de la o zi la alta.",
        "zinc": "Înmuiază leguminoasele câteva ore înainte de fiert: zincul se absoarbe mai bine.",
        "folate": "Gătește-l scurt, la abur: fierberea lungă distruge o parte din folat.",
        "vitamin_c": "Mănâncă-l crud sau gătit scurt: vitamina C se pierde la căldură.",
    },
    "en": {
        "iron": "Eat it with a source of vitamin C (peppers, lemon, kiwi), which helps you absorb iron from plants. Tea and coffee at the same meal reduce it.",
        "calcium_iron": "Calcium at the same meal lowers iron absorption: have calcium-rich foods at a different meal from your iron foods.",
        "vitamin_d": "Vitamin D is absorbed better at a meal that also contains a little fat.",
        "vitamin_a": "Vitamin A is absorbed better with a little fat (for example a drizzle of oil).",
        "vitamin_b12_vegan": "On a vegan diet, B12 only comes from fortified foods or supplements. Talk to your doctor about a supplement.",
        "vitamin_k_anticoagulant": "If you take warfarin or acenocoumarol, keep the amount of leafy greens steady from day to day.",
        "zinc": "Soak legumes for a few hours before cooking: zinc is absorbed better.",
        "folate": "Cook it briefly, by steaming: long boiling destroys part of the folate.",
        "vitamin_c": "Eat it raw or briefly cooked: vitamin C is lost with heat.",
    },
}
