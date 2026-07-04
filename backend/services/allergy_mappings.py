"""Mapări alergii — o singură sursă pentru rule_engine și scoped_rules."""
from __future__ import annotations

import re
from typing import Any, Dict

# Specii și preparate frecvente în catalog — multe apar în „Mese/Proteine” fără „pește” în categorie.
_FISH_ALLERGY_KEYWORDS = [
    "peste",
    "pește",
    "pescarus",
    "somon",
    "ton",
    "sardine",
    "macrou",
    "crap",
    "salau",
    "fish",
    "seafood",
    "homar",
    "lobster",
    "crevet",
    "crab",
    "shrimp",
    "prawn",
    "prawns",
    "midie",
    "midii",
    "scoici",
    "scallop",
    "calamar",
    "sepie",
    "icre",
    "hering",
    "anchois",
    "sushi",
    "sashimi",
    "cod",
    "halibut",
    "tilapia",
    "pastrav",
    "trout",
    "bass",
    "haddock",
    "mackerel",
    "merluciu",
    "dorada",
    "biban",
    "somn",
    "stiuca",
    "anghila",
    "calcan",
    "romb",
    "novac",
    "caras",
    "lipan",
    "pike",
    "flounder",
    "turbot",
    "nisetru",
    "sturion",
    "scrumbie",
    "pangasius",
    "basa",
    "perca",
    "file de cod",
    "file de somon",
    "file de ton",
    "file de macrou",
    "file de merluciu",
    "file de salau",
    "file de crap",
    "peste la",
    "peste pane",
    "fish and chips",
]

# Nu folosi categorii prea largi (ex. „legume” pentru soia) — „legume” apare în „leguminoase”.
ALLERGY_MAPPINGS: Dict[str, Dict[str, Any]] = {
    "lactoza": {
        "categories": ["lactate", "lapte", "branza", "branzeturi"],
        "keywords": [
            "lactate", "lapte", "branza", "brânză", "branzeturi", "brânzeturi",
            "iaurt", "smantana", "smântână", "unt", "telemea",
            "cascaval", "cașcaval", "ricotta", "mozzarella", "gorgonzola",
            "parmezan", "cheddar", "feta", "brie", "camembert", "dairy", "lactos",
        ],
    },
    "lactoză": {
        "categories": ["lactate", "lapte", "branza", "branzeturi"],
        "keywords": [
            "lactate", "lapte", "branza", "brânză", "branzeturi", "brânzeturi",
            "iaurt", "smantana", "smântână", "unt", "telemea",
            "cascaval", "cașcaval", "ricotta", "mozzarella", "gorgonzola",
            "parmezan", "cheddar", "feta", "brie", "camembert", "dairy", "lactos",
        ],
    },
    "lactate": {
        "categories": ["lactate", "lapte", "branza", "branzeturi"],
        "keywords": [
            "lactate", "lapte", "branza", "brânză", "branzeturi", "brânzeturi",
            "iaurt", "smantana", "smântână", "unt", "telemea",
            "cascaval", "cașcaval", "ricotta", "mozzarella", "gorgonzola",
            "parmezan", "cheddar", "feta", "brie", "camembert", "dairy", "lactos",
        ],
    },
    "gluten": {
        "categories": ["cereale", "paini", "paste", "faina"],
        "keywords": [
            "gluten", "grâu", "grau", "grău", "făină", "faina",
            "pâine", "paine", "pâini", "paste", "spaghete", "macaroane",
            "tortilla", "cereale", "wheat", "barley", "rye", "seitan",
            "ovăz", "orz", "secară", "malț",
        ],
    },
    "nuci": {
        "categories": [],
        "keywords": [
            "nuci", "nuca", "nucă", "alune", "migdale", "fistic",
            "caju", "macadamia", "pecan", "nuts", "almond", "walnut", "hazelnut",
            "pignoli", "pinoli", "nuci de pin", "nuca de pin",
            "pesto", "kibbeh", "baklava", "nougat", "gianduja", "marzipan", "martipan",
        ],
    },
    "nucă": {
        "categories": [],
        "keywords": [
            "nuci", "nuca", "nucă", "alune", "migdale", "fistic",
            "caju", "macadamia", "pecan", "nuts", "almond", "walnut", "hazelnut",
            "pignoli", "pinoli", "nuci de pin", "nuca de pin",
            "pesto", "kibbeh", "baklava", "nougat", "gianduja", "marzipan", "martipan",
        ],
    },
    "ouă": {
        "categories": [],
        "keywords": [
            "ouă",
            "oua",
            "ou",
            "egg",
            "eggs",
            "albus",
            "galbenus",
            "cobb",
            "piccata",
            "picatta",
            "maionez",
            "majonez",
            "mayonnaise",
            "carbonara",
            "hollandaise",
            "tiramisu",
            "custard",
            "flan",
            "papanasi",
            "clatite",
            "clătite",
            "briosa",
            "brioșa",
            "pancakes",
            "waffle",
            "waffles",
        ],
    },
    "oua": {
        "categories": [],
        "keywords": [
            "ouă",
            "oua",
            "ou",
            "egg",
            "eggs",
            "albus",
            "galbenus",
            "cobb",
            "piccata",
            "picatta",
            "maionez",
            "majonez",
            "mayonnaise",
            "carbonara",
            "hollandaise",
            "tiramisu",
            "custard",
            "flan",
            "papanasi",
            "clatite",
            "clătite",
            "briosa",
            "brioșa",
            "pancakes",
            "waffle",
            "waffles",
        ],
    },
    "soia": {
        "categories": [],
        "keywords": [
            "soia",
            "soy",
            "soja",
            "tofu",
            "tempeh",
            "miso",
            "edamame",
            "yuba",
            "tamari",
            "sos de soia",
            "soy sauce",
            "lecitina",
            "lecithin",
            "textured soy",
            "soia texturata",
            "proteina de soia",
            "lapte de soia",
            "iaurt de soia",
        ],
    },
    "peste": {
        "categories": ["peste", "fructe de mare"],
        "keywords": _FISH_ALLERGY_KEYWORDS,
    },
    "pește": {
        "categories": ["peste", "fructe de mare"],
        "keywords": _FISH_ALLERGY_KEYWORDS,
    },
    "crustacee": {
        "categories": [],
        "keywords": [
            "crustacee",
            "creveți",
            "creveti",
            "crab",
            "homar",
            "langustă",
            "langusta",
            "shrimp",
            "lobster",
        ],
    },
    "arahide": {
        "categories": [],
        "keywords": ["arahide", "alune de pământ", "alune de pamant", "peanut", "peanuts"],
    },
    "sesam": {
        "categories": [],
        "keywords": [
            "sesam",
            "susan",
            "sezam",
            "semințe de susan",
            "seminte de susan",
            "sesame",
            "tahini",
            "halva",
            "halvă",
            "susan",
        ],
    },
    "mustar": {
        "categories": [],
        "keywords": ["mustar", "muștar", "mustard", "condimente cu mustar"],
    },
    "semințe": {
        "categories": [],
        "keywords": [
            "semințe",
            "seminte",
            "semințe de",
            "seminte de",
            "chia",
            "flax",
            "sunflower",
            "pumpkin",
            "sesame",
            "sezam",
            "semințe de in",
            "seminte de in",
            "semințe de chia",
            "semințe de dovleac",
            "semințe de susan",
            "seminte de susan",
            "semințe de floarea-soarelui",
            "seminte de floarea-soarelui",
            "in de floarea",
        ],
    },
    "seminte": {
        "categories": [],
        "keywords": [
            "semințe",
            "seminte",
            "semințe de",
            "seminte de",
            "chia",
            "flax",
            "sunflower",
            "pumpkin",
            "sesame",
            "sezam",
            "semințe de in",
            "seminte de in",
            "semințe de chia",
            "semințe de dovleac",
            "semințe de susan",
            "seminte de susan",
            "semințe de floarea-soarelui",
            "seminte de floarea-soarelui",
            "in de floarea",
        ],
    },
}

# Tokeni scurți (ex. „cod”, „ton”) — potrivire la graniță de cuvânt, nu substring în alte cuvinte.
_FISH_SPECIES_SHORT = frozenset(
    {
        "cod",
        "ton",
        "biban",
        "somn",
        "romb",
        "basa",
        "sole",
        "crab",
    }
)

_OU_BOUNDARY = re.compile(r"(^|\s)ou($|\s)")
# „oua” ca substring apare în „noua” — cerem început de cuvânt (început string sau după spațiu).
_OUA_WORD_START = re.compile(r"(^|\s)oua")
_FISH_WORD_BOUNDARY = re.compile(
    r"(^|[\s/(\-])("
    + "|".join(
        re.escape(s)
        for s in (
            "cod",
            "ton",
            "biban",
            "somn",
            "romb",
            "basa",
            "sole",
            "crab",
            "halibut",
            "tilapia",
            "pastrav",
            "trout",
            "bass",
            "merluciu",
            "dorada",
            "stiuca",
            "anghila",
            "calcan",
            "novac",
            "caras",
            "lipan",
            "pike",
            "turbot",
            "nisetru",
            "sturion",
            "scrumbie",
            "pangasius",
            "perca",
            "somon",
            "sardine",
            "macrou",
            "crap",
            "salau",
            "hering",
            "anchois",
            "crevet",
            "midie",
            "calamar",
            "sepie",
            "homar",
            "haddock",
            "mackerel",
            "flounder",
        )
    )
    + r")($|[\s/),\-.])"
)


def fish_name_matches_norm(name_norm: str) -> bool:
    """Detectează pește/fructe de mare după nume, inclusiv când categoria e generică (Mese/Proteine)."""
    if not name_norm:
        return False
    if _FISH_WORD_BOUNDARY.search(name_norm):
        return True
    for kw in _FISH_ALLERGY_KEYWORDS:
        if kw in _FISH_SPECIES_SHORT:
            continue
        kn = kw  # deja ASCII din normalizare upstream
        if kn and kn in name_norm:
            return True
    return False


def allergy_keyword_matches_norm(kw: str, name_norm: str, cat_norm: str) -> bool:
    """Potrivire cuvânt-cheie; „ou”/„oua” ca token, nu în interiorul „nouă” / „noua”."""
    if not kw:
        return False
    if kw == "ou":
        return bool(_OU_BOUNDARY.search(name_norm)) or bool(_OU_BOUNDARY.search(cat_norm))
    if kw == "oua":
        return bool(_OUA_WORD_START.search(name_norm)) or bool(_OUA_WORD_START.search(cat_norm))
    if kw in _FISH_SPECIES_SHORT:
        pat = re.compile(rf"(^|[\s/(\-]){re.escape(kw)}($|[\s/),\-.])")
        return bool(pat.search(name_norm)) or bool(pat.search(cat_norm))
    return kw in name_norm or kw in cat_norm
