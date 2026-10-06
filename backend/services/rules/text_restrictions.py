"""
Restricții alimentare scrise de utilizator în profil sau la observații („nu mănânc pește”, „fără lactate”,
„alergie la roșii”). Parserul vine din vechiul motor (rule_engine), fără regulile pe afecțiuni: afecțiunile au acum
reguli structurate, cu surse, în rules/contraindications.py.

Potrivirea se face pe numele alimentului (RO și EN) și pe eticheta categoriei.
"""
from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional

from domain.models import FoodItem, LabResultItem, UserProfile
from services.rules.medical_rules_loader import normalize_clinical_text as _normalize_text

# Sinonime: când utilizatorul menționează X, verificăm și variantele în numele alimentelor
FOOD_RESTRICTION_SYNONYMS: Dict[str, List[str]] = {
    'pătlăgele': ['pătlăgele', 'patlagele', 'vinete', 'eggplant'],
    'vinete': ['vinete', 'pătlăgele', 'patlagele'],
    'roșii': ['roșii', 'rosii', 'tomate', 'tomatoes'],
    'tomate': ['tomate', 'roșii', 'rosii'],
    'ardei': ['ardei', 'piper', 'pepper'],
    'ciocolată': ['ciocolată', 'ciocolata', 'chocolate', 'ciocolata'],
    'cafea': ['cafea', 'coffee', 'espresso'],
    'alcool': ['alcool', 'bere', 'vin', 'vinuri'],
    'zahăr': ['zahăr', 'zahar', 'sugar', 'dulce'],
    'dulciuri': ['dulciuri', 'dulce', 'bomboane', 'prăjituri'],
    'sare': ['sare', 'sodium', 'sarat'],
    'gluten': ['gluten', 'grâu', 'grau', 'făină', 'faina', 'pâine', 'paine'],
    'spanac': ['spanac', 'spinach'],
    'varză': ['varză', 'varza', 'varza', 'cabbage', 'broccoli'],
    'fasole': ['fasole', 'beans', 'fasole'],
    'linte': ['linte', 'lentils'],
    'mazăre': ['mazăre', 'mazare', 'mazăre', 'peas'],
    'castraveți': ['castraveți', 'castraveti', 'cucumber'],
    'ceapă': ['ceapă', 'ceapa', 'onion'],
    'usturoi': ['usturoi', 'garlic'],
    'cartofi': ['cartofi', 'potato', 'cartof'],
}

def parse_food_restrictions(medical_conditions: str) -> Dict[str, List[str]]:
    """
    Parsează condițiile medicale și identifică interziceri pentru categorii de alimente.
    Extrage și restricțiile din condiții medicale cunoscute.

    Returnează un dicționar cu:
    - 'forbidden_categories': lista de categorii interzise
    - 'forbidden_keywords': lista de cuvinte cheie interzise
    - 'preferred_categories': categorii preferate (ex: vreau carne de porc)
    """
    if not medical_conditions:
        return {'forbidden_categories': [], 'forbidden_keywords': [], 'preferred_categories': []}

    conditions_lower = _normalize_text(medical_conditions)
    forbidden_categories = []
    forbidden_keywords = []

    category_patterns = {
        'legume': [
            'nu mananc legume', 'nu mănânc legume', 'nu mananc leguma', 'nu mănânc leguma',
            'fara legume', 'fără legume', 'no vegetables', 'no veggies',
            'evit legume', 'interzis legume', 'nu pot legume', 'nu pot mânca legume'
        ],
        'fructe': [
            'nu mananc fructe', 'nu mănânc fructe', 'nu mananc fructa', 'nu mănânc fructa',
            'fara fructe', 'fără fructe', 'no fruits', 'no fruit',
            'evit fructe', 'interzis fructe', 'nu pot fructe', 'nu pot mânca fructe'
        ],
        'cereale': [
            'nu mananc cereale', 'nu mănânc cereale', 'nu mananc cereala', 'nu mănânc cereala',
            'fara cereale', 'fără cereale', 'no grains', 'no cereals',
            'evit cereale', 'interzis cereale', 'nu pot cereale', 'nu pot mânca cereale'
        ],
        'carne': [
            'nu mananc carne', 'nu mănânc carne', 'fara carne', 'fără carne',
            'no meat', 'no red meat', 'evit carne', 'interzis carne',
            'nu pot carne', 'nu pot mânca carne'
        ],
        'pui': [
            'nu mananc pui', 'nu mănânc pui', 'fara pui', 'fără pui',
            'no chicken', 'evit pui', 'interzis pui', 'nu pot pui', 'nu pot mânca pui'
        ],
        'porc': [
            'nu mananc porc', 'nu mănânc porc', 'fara porc', 'fără porc',
            'no pork', 'evit porc', 'interzis porc', 'nu pot porc', 'nu pot mânca porc'
        ],
        'vita': [
            'nu mananc vita', 'nu mănânc vită', 'nu mananc vaca', 'nu mănânc vacă',
            'fara vita', 'fără vită', 'no beef', 'evit vita', 'interzis vita'
        ],
        'miel': [
            'nu mananc miel', 'nu mănânc miel', 'fara miel', 'fără miel',
            'no lamb', 'evit miel', 'interzis miel', 'nu pot miel'
        ],
        'peste': [
            'nu mananc peste', 'nu mănânc pește', 'nu mananc pesti', 'nu mănânc pești',
            'fara peste', 'fără pește', 'no fish', 'no seafood',
            'evit peste', 'interzis peste', 'nu pot peste', 'nu pot mânca pește',
            'nu pot consuma peste', 'nu pot consuma pesti',
        ],
        'lactate': [
            'nu mananc lactate', 'nu mănânc lactate', 'nu mananc lapte', 'nu mănânc lapte',
            'fara lactate', 'fără lactate', 'fara lapte', 'fără lapte',
            'no dairy', 'no milk', 'evit lactate', 'interzis lactate',
            'nu pot consuma lactate', 'nu pot consuma lapte',
        ],
        'semințe': [
            'nu mananc seminte', 'nu mănânc semințe', 'nu am voie seminte', 'nu am voie semințe',
            'fara seminte', 'fără semințe', 'no seeds', 'evit seminte', 'interzis seminte',
            'nu pot consuma seminte', 'nu pot consuma seminte de',
        ],
        'nuci': [
            'nu mananc nuci', 'nu mănânc nuci', 'nu mananc nuca', 'nu mănânc nucă',
            'fara nuci', 'fără nuci', 'no nuts', 'evit nuci', 'interzis nuci'
        ],
        'leguminoase': [
            'nu mananc leguminoase', 'nu mănânc leguminoase', 'nu mananc fasole', 'nu mănânc fasole',
            'nu mananc linte', 'nu mănânc linte', 'fara leguminoase', 'fără leguminoase',
            'no legumes', 'no beans', 'evit leguminoase', 'interzis leguminoase'
        ],
        'ouă': [
            'nu mananc oua', 'nu mănânc ouă', 'nu mananc ou', 'nu mănânc ou',
            'fara oua', 'fără ouă', 'no eggs', 'evit oua', 'interzis oua'
        ],
        'soia': [
            'nu mananc soia', 'nu mănânc soia', 'fara soia', 'fără soia',
            'no soy', 'evit soia', 'interzis soia'
        ],
        'roșii': [
            'nu mananc rosii', 'nu mănânc roșii', 'fara rosii', 'fără roșii',
            'no tomatoes', 'evit rosii', 'evit roșii', 'nu pot rosii',
            'alergie la rosii', 'alergie la roșii', 'intoleranță la roșii'
        ],
        'ardei': [
            'nu mananc ardei', 'nu mănânc ardei', 'fara ardei', 'fără ardei',
            'no peppers', 'evit ardei', 'nu pot ardei', 'alergie la ardei'
        ],
        'ciocolată': [
            'nu mananc ciocolata', 'nu mănânc ciocolată', 'fara ciocolata', 'fără ciocolată',
            'no chocolate', 'evit ciocolata', 'nu am voie ciocolata'
        ],
        'cafea': [
            'nu beau cafea', 'nu pot cafea', 'fara cafea', 'fără cafea',
            'no coffee', 'evit cafea', 'nu am voie cafea'
        ],
        'alcool': [
            'nu beau alcool', 'fara alcool', 'fără alcool', 'no alcohol',
            'evit alcool', 'abstinent', 'nu am voie alcool'
        ],
        'zahăr': [
            'nu mananc zahar', 'nu mănânc zahăr', 'fara zahar', 'fără zahăr',
            'low sugar', 'no sugar', 'fără dulciuri', 'evit zahar', 'evit zahăr'
        ],
        'gluten': [
            'fara gluten', 'fără gluten', 'no gluten', 'evit gluten',
            'intoleranță gluten', 'celiachie', 'sensibilitate la gluten'
        ],
    }

    for category, patterns in category_patterns.items():
        patterns_norm = [_normalize_text(p) for p in patterns]
        if any(pattern in conditions_lower for pattern in patterns_norm):
            forbidden_categories.append(category)

    # Extrage explicit liste compuse după negări de tip:
    # "nu mananc peste, pui", "nu am voie peste si pui", etc.
    list_patterns = [
        r'nu\s+(?:mananc|pot manca|am voie)\s+([^.;!?]+)',
        r'nu\s+pot\s+(?:consuma|manca|mananc)\s+([^.;!?]+)',
        r'fara\s+([^.;!?]+)',
        r'evit\s+([^.;!?]+)',
        r'nu\s+consum\s+([^.;!?]+)',
        r'exclud\s+([^.;!?]+)',
        r'interzis\s+([^.;!?]+)',
    ]
    for pattern in list_patterns:
        for m in re.finditer(pattern, conditions_lower):
            segment = m.group(1)
            # Tăiem eventuale continuări care schimbă sensul propoziției.
            segment = re.split(r'\b(?:dar|insa|except|in afara de)\b', segment)[0]
            parts = re.split(r',|\bsi\b|\bsau\b', segment)
            for part in parts:
                token = part.strip()
                if not token:
                    continue
                # Curățare de stop words uzuale din expresii compuse.
                token = re.sub(r'\b(?:de|din|la|cu|pe|care|ce|sa)\b', ' ', token).strip()
                token = re.sub(r'\s+', ' ', token).strip()
                if len(token) > 2 and token not in forbidden_keywords:
                    forbidden_keywords.append(token)

    # Patternuri generale – extrag orice aliment menționat ca interzis
    general_patterns = [
        r'nu\s+(?:mănânc|mananc|pot\s+mânca|pot\s+mananca|am\s+voie)\s+(?:să\s+)?(?:manc|mânc)\s+([a-zăâîșț\s]+?)(?:\.|,|;|$|\s+și\s+|\s+si\s+|\s+sau\s+|\s+or\s+)',
        r'nu\s+(?:mănânc|mananc|pot\s+mânca|pot\s+mananca)\s+([a-zăâîșț]+)',
        r'nu\s+am\s+voie\s+(?:la\s+|să\s+mânc\s+|sa\s+mananc\s+)?([a-zăâîșț\s]+?)(?:\.|,|;|$|\s+și\s+|\s+si\s+|\s+sau\s+)',
        r'nu\s+am\s+voie\s+([a-zăâîșț]+)',
        r'fără\s+([a-zăâîșț\s]+?)(?:\s|\.|,|;|$)',
        r'fara\s+([a-zăâîșț\s]+?)(?:\s|\.|,|;|$)',
        r'evit\s+([a-zăâîșț]+)',
        r'interzis\s+([a-zăâîșț]+)',
        r'(?:nu\s+)?suport\s+([a-zăâîșț]+)',
        r'(?:nu\s+)?suportă\s+([a-zăâîșț]+)',
        r'(?:mă|ma)\s+deranjează\s+([a-zăâîșț]+)',
        r'am\s+probleme\s+(?:cu\s+|la\s+)([a-zăâîșț]+)',
        r'intoleranță\s+(?:la\s+)?([a-zăâîșț]+)',
        r'intoleranta\s+(?:la\s+)?([a-zăâîșț]+)',
        r'alergie\s+(?:la\s+)?([a-zăâîșț]+)',
        r'alergic\s+(?:la\s+)?([a-zăâîșț]+)',
        r'nu\s+pot\s+tolera\s+([a-zăâîșț]+)',
        r'(?:sau|or|și|si)\s+([a-zăâîșț]+)\s+(?:nu\s+)?(?:mănânc|mananc|am\s+voie)',
        # Formulări de tipul „alimente care au cartofi”, „alimente care conțin X”
        r'alimente\s+care\s+au\s+([a-zăâîșț\s]+?)(?:\.|,|;|$)',
        r'alimente\s+care\s+conțin\s+([a-zăâîșț\s]+?)(?:\.|,|;|$)',
    ]

    for pattern in general_patterns:
        matches = re.findall(pattern, conditions_lower)
        for match in matches:
            # Curăță și extrage cuvinte
            words = [w.strip() for w in match.split() if len(w.strip()) > 2 and w.strip() not in ('sau', 'și', 'si', 'sau', 'de', 'la', 'cu')]
            for w in words:
                if w not in forbidden_keywords:
                    forbidden_keywords.append(w)
            if len(match.strip()) > 2 and len(words) == 0 and match.strip() not in forbidden_keywords:
                forbidden_keywords.append(match.strip())

    # Extragem și din enunțuri "X sau Y nu mănânc"
    split_phrases = re.split(r'[.,;!?]', conditions_lower)
    for phrase in split_phrases:
        if 'nu mănânc' in phrase or 'nu mananc' in phrase or 'nu am voie' in phrase or 'fără' in phrase or 'fara' in phrase:
            parts = re.split(r'\s+(?:sau|or|și|si)\s+', phrase)
            for part in parts:
                m = re.search(r'(?:nu\s+(?:mănânc|mananc|am\s+voie)|fără|fara|evit)\s+(.+)', part)
                if m:
                    extracted = m.group(1).strip()
                    words = [w.strip() for w in re.split(r'[\s,]+', extracted) if len(w.strip()) > 2]
                    for w in words:
                        if w not in forbidden_keywords:
                            forbidden_keywords.append(w)

    # Normalizare: scoatem articole/sufixe românești (lactatele->lactate, rosii->roșii)
    def _stem_ro(word: str) -> str:
        w = word.strip().lower()
        for suf in ['le', 'ul', 'ului', 'ei', 'ilor', 'ele']:
            if len(w) > len(suf) + 2 and w.endswith(suf):
                return w[:-len(suf)]
        return w

    # Expandăm cu sinonime + stem
    expanded_keywords: List[str] = []
    seen: set = set()
    for kw in forbidden_keywords:
        kw_norm = _normalize_text(kw)
        for form in [kw_norm, _stem_ro(kw_norm)]:
            if form and len(form) > 2 and form not in seen:
                expanded_keywords.append(form)
                seen.add(form)
        if kw_norm in FOOD_RESTRICTION_SYNONYMS:
            for syn in FOOD_RESTRICTION_SYNONYMS[kw_norm]:
                syn_norm = _normalize_text(syn)
                if syn_norm not in seen:
                    expanded_keywords.append(syn_norm)
                    seen.add(syn_norm)
    forbidden_keywords = expanded_keywords

    simple_food_keywords = {
        'ouă': ['ouă', 'oua', 'ou', 'eggs'],
        'legume': ['legume', 'leguma', 'vegetable', 'vegetables'],
        'fructe': ['fructe', 'fructa', 'fruit', 'fruits'],
        'cereale': ['cereale', 'cereala', 'grain', 'grains', 'cereal'],
        'carne': ['carne', 'meat'],
        'peste': ['peste', 'pește', 'fish', 'seafood'],
        'lactate': ['lactate', 'lapte', 'dairy', 'milk'],
        'semințe': ['semințe', 'seminte', 'seeds'],
        'nuci': ['nuci', 'nucă', 'nuts'],
        'leguminoase': ['leguminoase', 'fasole', 'linte', 'legumes', 'beans'],
        'soia': ['soia', 'soy'],
        'gluten': ['gluten', 'grâu', 'grau', 'wheat'],
        'roșii': ['rosii', 'roșii', 'tomate', 'tomatoes'],
        'ardei': ['ardei', 'piper'],
        'ciocolată': ['ciocolata', 'ciocolată', 'chocolate'],
        'cafea': ['cafea', 'coffee'],
        'alcool': ['alcool', 'bere', 'vin'],
        'zahăr': ['zahar', 'zahăr', 'sugar'],
    }

    positive_patterns = [
        ('vreau', ['porc', 'pui', 'vita', 'vită', 'miel', 'peste', 'pește', 'carne']),
        ('doresc', ['porc', 'pui', 'vita', 'vită', 'miel', 'peste', 'pește', 'carne']),
        ('prefer', ['porc', 'pui', 'vita', 'vită', 'miel', 'peste', 'pește']),
    ]
    preferred_categories: List[str] = []
    for verb, categories in positive_patterns:
        for cat in categories:
            if f'{verb} {cat}' in conditions_lower or f'{verb} carne de {cat}' in conditions_lower:
                preferred_categories.append(cat)

    words = re.split(r'[,\s\.;]+', conditions_lower)
    for word in words:
        word = word.strip()
        if len(word) > 2:
            for category, keywords in simple_food_keywords.items():
                if word in keywords:
                    if category not in forbidden_categories:
                        if not any(positive in conditions_lower for positive in [
                            'pot mânca', 'pot mananca', 'pot consuma', 'mănânc', 'mananc',
                            'consum', 'mănâncă', 'mananca', 'vreau', 'doresc', 'prefer'
                        ]):
                            forbidden_categories.append(category)
                            break

    return {
        'forbidden_categories': forbidden_categories,
        'forbidden_keywords': forbidden_keywords,
        'preferred_categories': list(set(preferred_categories))
    }


CATEGORY_MAPPINGS: Dict[str, List[str]] = {
    'legume': ['legume', 'leguma', 'vegetable', 'vegetables', 'leguminoase'],
    'fructe': ['fructe', 'fructa', 'fruit', 'fruits'],
    'cereale': ['cereale', 'cereala', 'grain', 'grains', 'cereal'],
    'carne': ['carne', 'meat', 'pui', 'porc', 'vita', 'miel'],
    'pui': ['pui', 'puișor', 'puisoare', 'chicken', 'curcan', 'curcană', 'găină', 'gaina'],
    'porc': ['porc', 'porcine', 'pork', 'bacon', 'șuncă', 'sunca', 'ceafă', 'ceafa', 'muschi', 'cârnați', 'carnati'],
    'vita': ['vita', 'vită', 'vaca', 'vacă', 'beef', 'carne de vita', 'carne de vită'],
    'miel': ['miel', 'miel de', 'lamb', 'oaie', 'mouton'],
    'peste': [
        'peste', 'pește', 'pescarus', 'fish', 'seafood', 'fructe de mare',
        'homar', 'lobster', 'crevet', 'crab', 'midie', 'scoici', 'calamar', 'sepie',
        'cod', 'halibut', 'tilapia', 'somon', 'ton', 'macrou', 'merluciu',
    ],
    'lactate': ['lactate', 'lapte', 'dairy', 'milk'],
    'semințe': ['semințe', 'seminte', 'seeds', 'chia', 'flax', 'susan', 'sesam'],
    'nuci': ['nuci', 'nucă', 'nuts'],
    'leguminoase': ['leguminoase', 'fasole', 'linte', 'legumes', 'beans'],
    'ouă': ['ouă', 'oua', 'ou', 'eggs'],
    'soia': ['soia', 'soy'],
    'roșii': ['roșii', 'rosii', 'tomate', 'tomatoes', 'ketchup', 'sos de roșii'],
    'ardei': ['ardei', 'ardei gras', 'piper', 'pepper', 'ardei iute'],
    'ciocolată': ['ciocolată', 'ciocolata', 'chocolate', 'cacao'],
    'cafea': ['cafea', 'coffee', 'espresso', 'cappuccino'],
    'alcool': ['alcool', 'bere', 'vin', 'vinuri', 'alcoholic'],
    'zahăr': ['zahăr', 'zahar', 'sugar', 'dulce', 'dulciuri', 'bomboane', 'prăjituri'],
    'gluten': ['gluten', 'grâu', 'grau', 'făină', 'faina', 'pâine', 'paine', 'paste', 'spaghete'],
}


# Grupele de alimente se recunosc și după câmpurile structurate ale catalogului validat (o brânză nu are „lactate”
# în nume, dar are animal_source = dairy). Cheile sunt normalizate (fără diacritice).
STRUCTURED_GROUPS: Dict[str, Callable[[FoodItem], bool]] = {
    "lactate": lambda f: f.animal_source == "dairy",
    "lapte": lambda f: f.animal_source == "dairy",
    "peste": lambda f: f.animal_source in ("fish", "shellfish"),
    "carne": lambda f: f.animal_source in ("meat", "poultry"),
    "pui": lambda f: f.animal_source == "poultry",
    "oua": lambda f: f.animal_source == "egg",
    "nuci": lambda f: "nuci" in f.allergen_codes,
    "seminte": lambda f: f.category_key == "seeds",
    "leguminoase": lambda f: f.category_key == "legumes",
    "legume": lambda f: f.category_key in ("vegetables", "leafy_greens"),
    "fructe": lambda f: f.category_key in ("fruits", "dried_fruits"),
    "cereale": lambda f: f.category_key in ("whole_grains", "refined_grains", "bakery"),
    "gluten": lambda f: "gluten" in f.allergen_codes,
    "soia": lambda f: "soia" in f.allergen_codes,
}


def _matches(food_text: str, word: str) -> bool:
    return bool(re.search(rf"\b{re.escape(word)}\b", food_text))


def text_restriction_filter(user: UserProfile, lab_results: Optional[LabResultItem] = None) -> Optional[Callable[[FoodItem], bool]]:
    """Funcție food -> permis? sau None dacă utilizatorul nu a scris nicio restricție."""
    notes = getattr(lab_results, "notes", None) if lab_results is not None else None
    text = " ".join(x for x in (user.medical_conditions or "", notes or "") if x).strip()
    if not text:
        return None
    restrictions = parse_food_restrictions(text)
    preferred = set(restrictions.get("preferred_categories") or [])
    categories = [c for c in restrictions["forbidden_categories"] if c not in preferred]
    keywords = [k for k in restrictions["forbidden_keywords"] if k]
    if not categories and not keywords:
        return None

    structured = [STRUCTURED_GROUPS[k] for k in {_normalize_text(x) for x in categories + keywords} if k in STRUCTURED_GROUPS]

    def allows(food: FoodItem) -> bool:
        if any(check(food) for check in structured):
            return False
        food_text = _normalize_text(f"{food.name} {food.name_en or ''} {food.category or ''}")
        for cat in categories:
            for variant in CATEGORY_MAPPINGS.get(cat, [cat]):
                if _matches(food_text, _normalize_text(variant)):
                    return False
        return not any(_matches(food_text, _normalize_text(k)) for k in keywords)

    return allows
