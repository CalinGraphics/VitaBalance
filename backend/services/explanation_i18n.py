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
           "crustacee": "crustacee", "arahide": "arahide", "sesam": "susan", "mustar": "muștar"},
    "en": {"lactoza": "lactose", "gluten": "gluten", "nuci": "tree nuts", "oua": "eggs", "soia": "soy",
           "peste": "fish", "crustacee": "shellfish", "arahide": "peanuts", "sesam": "sesame", "mustar": "mustard"},
}

# Afecțiuni cu restricții alimentare: (etichetă, restricția respectată). Cheile = ids din explanation_facts.CONDITION_PATTERNS.
CONDITION_LABELS: Dict[str, Dict[str, tuple]] = {
    "ro": {
        "celiac": ("boală celiacă / sensibilitate la gluten", "fără gluten (grâu, făină, pâine, paste, ovăz, orz)"),
        "lactose": ("intoleranță la lactoză", "fără lactate (lapte, brânză, iaurt, smântână)"),
        "reflux": ("reflux gastroesofagian", "fără alimente picante, cafea, ciocolată sau prăjeli"),
        "gastritis": ("gastrită / ulcer", "fără alimente picante, alcool sau cafea"),
        "gout": ("gută", "fără organe, fructe de mare sau carne roșie"),
        "renal": ("afecțiune renală", "fără alimente bogate în oxalați (spanac, rabarbar) sau sare adăugată"),
        "diabetes": ("diabet", "fără zahăr adăugat, siropuri sau dulciuri"),
        "hypertension": ("hipertensiune", "fără sare adăugată, mezeluri sau conserve"),
        "ibs": ("colon iritabil", "fără lactate, fructoză în exces sau grâu"),
        "colitis": ("colită / boală Crohn", "fără lactate, grâu sau alimente grase"),
        "diverticulitis": ("diverticulită", "fără semințe, nuci sau floricele de porumb"),
        "liver_pancreas": ("afecțiune hepatică, pancreatică sau biliară", "fără alcool, grăsimi în exces sau prăjeli"),
        "cholesterol_cardio": ("colesterol ridicat / risc cardiovascular",
                               "fără prăjeli, mezeluri, brânzeturi grase sau unt"),
    },
    "en": {
        "celiac": ("celiac disease / gluten sensitivity", "gluten-free (wheat, flour, bread, pasta, oats, barley)"),
        "lactose": ("lactose intolerance", "no dairy (milk, cheese, yogurt, cream)"),
        "reflux": ("acid reflux", "no spicy food, coffee, chocolate or fried food"),
        "gastritis": ("gastritis / ulcer", "no spicy food, alcohol or coffee"),
        "gout": ("gout", "no organ meats, seafood or red meat"),
        "renal": ("kidney disease", "no oxalate-rich foods (spinach, rhubarb) or added salt"),
        "diabetes": ("diabetes", "no added sugar, syrups or sweets"),
        "hypertension": ("hypertension", "no added salt, cured meats or canned food"),
        "ibs": ("irritable bowel", "no dairy, excess fructose or wheat"),
        "colitis": ("colitis / Crohn's disease", "no dairy, wheat or fatty food"),
        "diverticulitis": ("diverticulitis", "no seeds, nuts or popcorn"),
        "liver_pancreas": ("liver, pancreas or gallbladder condition", "no alcohol, excess fat or fried food"),
        "cholesterol_cardio": ("high cholesterol / cardiovascular risk",
                               "no fried food, cured meats, fatty cheeses or butter"),
    },
}

# Șabloane de propoziții. Placeholderele {…} sunt umplute de explanation_renderer.
SENTENCES: Dict[str, Dict[str, str]] = {
    "ro": {
        "and": "și",
        "headline_lab": "**{food}** este recomandat pentru că analizele tale arată valori sub pragul clinic pentru: {list}.",
        "headline_notes": "**{food}** este recomandat pentru că ai menționat nevoia de: {list}.",
        "headline_profile": "**{food}** este recomandat pentru a acoperi necesarul zilnic estimat din profilul tău: {list}.",
        "headline_general": "**{food}** este compatibil cu profilul tău și contribuie la aportul zilnic de: {list}.",
        "headline_none": "**{food}** este o opțiune compatibilă cu profilul și restricțiile tale.",
        "also_notes": "Ai menționat și nevoia de: {list}.",
        "portion_line": "La porția sugerată (~{portion}): {parts}.",
        "portion_part": "{nutrient} ~{amount} {unit} (~{pct}% din necesarul zilnic estimat)",
        "reason_lab": "{marker}: {value} {unit} (prag: {threshold} {unit}) — {food} contribuie cu {nutrient}.",
        "reason_notes": "Ai menționat nevoia de {nutrient} în profil sau observații.",
        "reason_profile": "Necesar de {nutrient} estimat din profil (fără valori relevante în analize).",
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
        "headline_profile": "**{food}** is recommended to cover the daily need estimated from your profile: {list}.",
        "headline_general": "**{food}** fits your profile and adds to your daily intake of: {list}.",
        "headline_none": "**{food}** is an option compatible with your profile and restrictions.",
        "also_notes": "You also mentioned needing: {list}.",
        "portion_line": "At the suggested portion (~{portion}): {parts}.",
        "portion_part": "{nutrient} ~{amount} {unit} (~{pct}% of the estimated daily need)",
        "reason_lab": "{marker}: {value} {unit} (threshold: {threshold} {unit}) — {food} provides {nutrient}.",
        "reason_notes": "You mentioned needing {nutrient} in your profile or notes.",
        "reason_profile": "{nutrient} need estimated from your profile (no relevant lab values).",
        "reason_diet": "Suitable for {diet}.",
        "reason_allergies": "Chosen respecting your declared allergies: {list}.",
        "reason_condition": "Adapted for {condition}: {restriction}.",
        "reason_no_labs": "Recommendation based on your profile; you have not entered lab results yet.",
        "alt_prefix": "",
    },
}

# Sfaturi: cheie -> text. Alese în explanation_renderer după nutrienți și afecțiunile pacientului.
TIPS: Dict[str, Dict[str, str]] = {
    "ro": {
        "iron": "Combină cu o sursă de vitamina C (lămâie, ardei) pentru o absorbție mai bună a fierului și evită ceaiul sau cafeaua la aceeași masă.",
        "calcium": "Evită să-l consumi la aceeași masă cu alimente foarte bogate în fier, pentru o absorbție optimă.",
        "vitamin_d": "Consumă-l împreună cu puțină grăsime pentru o absorbție mai bună; 10–15 minute de soare zilnic ajută la sinteza vitaminei D.",
        "vitamin_b12_vegan": "La dieta vegană, B12 provine doar din alimente fortificate sau suplimente: discută suplimentarea cu medicul tău.",
        "vitamin_b12": "Consumat regulat, ajută la menținerea valorilor de B12; repetă analizele la recomandarea medicului.",
        "magnesium": "Magneziul se absoarbe mai bine împreună cu vitamina D; evită dozele mari de calciu la aceeași masă.",
        "zinc": "Leguminoasele și cerealele integrale conțin fitați care reduc absorbția zincului: înmoaie-le sau fermentează-le.",
        "folate": "Folatul se pierde la gătit prelungit: preferă prepararea scurtă sau consumul crud.",
        "vitamin_c": "Vitamina C se degradează la căldură: consumă alimentul crud sau gătit scurt.",
        "vitamin_a": "Vitamina A este liposolubilă: se absoarbe mai bine împreună cu puțină grăsime.",
        "vitamin_k": "Dacă urmezi tratament anticoagulant, păstrează un aport constant de vitamina K și întreabă medicul înainte de schimbări.",
        "iodine": "Echilibrează aportul de iod și evită excesul, mai ales dacă ai o afecțiune tiroidiană.",
        "potassium": "Acoperă necesarul de potasiu din surse variate, distribuite pe parcursul zilei.",
        "potassium_renal": "Cu o afecțiune renală, discută cu medicul înainte de a crește aportul de potasiu.",
        "protein": "Distribuie proteinele pe parcursul zilei, nu doar la o singură masă.",
        "protein_renal": "Cu o afecțiune renală, cantitatea potrivită de proteine se stabilește împreună cu medicul.",
        "default": "Folosește porția sugerată în mesele zilnice.",
    },
    "en": {
        "iron": "Pair it with a vitamin C source (lemon, peppers) for better iron absorption, and avoid tea or coffee at the same meal.",
        "calcium": "Avoid having it at the same meal as foods very rich in iron, for optimal absorption.",
        "vitamin_d": "Have it with a little fat for better absorption; 10–15 minutes of daily sun helps your body make vitamin D.",
        "vitamin_b12_vegan": "On a vegan diet, B12 only comes from fortified foods or supplements: talk to your doctor about supplementation.",
        "vitamin_b12": "Eaten regularly, it helps maintain your B12 levels; repeat your tests as your doctor advises.",
        "magnesium": "Magnesium is absorbed better together with vitamin D; avoid high doses of calcium at the same meal.",
        "zinc": "Legumes and whole grains contain phytates that reduce zinc absorption: soak or ferment them.",
        "folate": "Folate is lost during long cooking: prefer short preparation or eating it raw.",
        "vitamin_c": "Vitamin C breaks down with heat: eat it raw or briefly cooked.",
        "vitamin_a": "Vitamin A is fat-soluble: it is absorbed better together with a little fat.",
        "vitamin_k": "If you take anticoagulant medication, keep your vitamin K intake steady and ask your doctor before changes.",
        "iodine": "Keep your iodine intake balanced and avoid excess, especially if you have a thyroid condition.",
        "potassium": "Cover your potassium needs from varied sources spread through the day.",
        "potassium_renal": "With a kidney condition, talk to your doctor before increasing your potassium intake.",
        "protein": "Spread your protein through the day rather than at a single meal.",
        "protein_renal": "With a kidney condition, the right amount of protein should be set together with your doctor.",
        "default": "Use the suggested portion in your daily meals.",
    },
}
