from __future__ import annotations

import re

from domain.models import FoodItem, UserProfile
from services.allergy_mappings import ALLERGY_MAPPINGS, allergy_keyword_matches_norm
from services.food_intelligence_api import assess_hidden_soy_risk_from_api
from services.medical_rules_loader import (
    normalize_clinical_text,
    normalize_diet_type,
    resolve_allergy_token,
)


def is_compatible_diet_and_allergies(food: FoodItem, user: UserProfile) -> bool:
    """
    Compatibilitate de bază partajată între engines:
    - dietă (vegan/vegetarian/pescatarian)
    - alergii declarate + alergeni din catalog
    - risc ascuns la soia pentru produse procesate
    """
    diet = normalize_diet_type(user.diet_type)
    cat_norm = normalize_clinical_text(food.category or "")
    name_norm = normalize_clinical_text(food.name or "")

    if diet in ("vegetarian", "vegan"):
        animal_markers = (
            "carne", "pui", "porc", "vita", "miel", "peste", "fructe de mare",
            "vanat", "ficat",
        )
        if any(m in cat_norm for m in animal_markers):
            return False
        seafood_name_markers = (
            "crevet", "scoic", "midie", "calamar", "sepie", "homar", "lobster",
            "shrimp", "prawn", "somon", "sardine", "macrou", "hering", "anchois",
            "icre", "peste la", "peste ", " peste", "pescarus", "fructe de mare",
            "scallop", "sushi", "sashimi", "file de ton", "ton rosu", "ton roșu",
        )
        if any(m in name_norm for m in seafood_name_markers):
            return False

    if diet == "vegan":
        dairy_egg_honey = (
            "lactate", "lapte", "branza", "branzeturi", "iaurt", "smantana", "unt",
            "oua", "miere",
        )
        if any(m in cat_norm for m in dairy_egg_honey):
            return False
        dairy_egg_honey_name_markers = (
            "mozzarella", "telemea", "ricotta", "camembert", "brie", "cheddar",
            "parmezan", "parmesan", "feta", "caprese", "halloumi", "iaurt", "lapte",
            "ou ", "oua", "egg", "eggs", "honey", "miere",
            "zer", "whey", "casein", "cazeina", "kefir", "chefir",
        )
        if any(m in name_norm for m in dairy_egg_honey_name_markers):
            return False

    if diet == "pescatarian":
        land_meat = ("carne", "pui", "porc", "vita", "miel", "vanat")
        if any(m in cat_norm for m in land_meat):
            return False

    if not user.allergies:
        return True

    user_allergies = [
        a.strip().lower()
        for a in re.split(r"[,;]+", user.allergies)
        if a.strip()
    ]
    food_name_norm = name_norm
    food_category_norm = cat_norm

    for user_allergy in user_allergies:
        user_allergy_clean = user_allergy.strip().lower()
        user_allergy_norm = normalize_clinical_text(user_allergy_clean)
        lookup_norm = resolve_allergy_token(user_allergy_norm)

        allergy_info = None
        for allergy_key, mapping in ALLERGY_MAPPINGS.items():
            key_norm = normalize_clinical_text(allergy_key)
            if (
                allergy_key == user_allergy_clean
                or key_norm == user_allergy_norm
                or key_norm == lookup_norm
                or user_allergy_clean in allergy_key
                or allergy_key in user_allergy_clean
            ):
                allergy_info = mapping
                break
            if len(user_allergy_norm) >= 3 and (
                user_allergy_norm in key_norm or key_norm in user_allergy_norm
            ):
                allergy_info = mapping
                break

        if allergy_info:
            if allergy_info["categories"] and any(
                normalize_clinical_text(cat) in food_category_norm
                for cat in allergy_info["categories"]
            ):
                return False

            for keyword in allergy_info["keywords"]:
                kw = normalize_clinical_text(keyword)
                if allergy_keyword_matches_norm(kw, food_name_norm, food_category_norm):
                    return False

        if food.allergens:
            food_allergens = [
                a.strip().lower()
                for a in re.split(r"[,;]+", food.allergens)
                if a.strip()
            ]
            for allergen in food_allergens:
                ag_norm = normalize_clinical_text(allergen)
                if user_allergy_clean in allergen or allergen in user_allergy_clean:
                    return False
                if ag_norm == user_allergy_norm or ag_norm == lookup_norm:
                    return False
                if len(user_allergy_norm) >= 3 and (
                    user_allergy_norm in ag_norm or ag_norm in user_allergy_norm
                ):
                    return False

        if len(user_allergy_norm) >= 5 and (
            user_allergy_norm in food_name_norm or user_allergy_norm in food_category_norm
        ):
            return False

    has_soy_allergy = any(
        resolve_allergy_token(normalize_clinical_text(x.strip())) == "soia"
        for x in user_allergies
        if x.strip()
    )
    if has_soy_allergy:
        combined_norm = f"{food_name_norm} {food_category_norm}"
        soy_free_markers = ("fara soia", "fără soia", "soy free", "soy-free")
        hidden_soy_risk_markers = (
            "conserva", "la conserva", "procesat", "procesate",
            "prajit", "prăjit", "garnitura", "garnitur", "sos",
            "supa crema", "supa", "guacamole",
        )
        if any(m in combined_norm for m in hidden_soy_risk_markers):
            if not any(m in combined_norm for m in soy_free_markers):
                api_verdict = assess_hidden_soy_risk_from_api(food.name or "", food.category or "")
                if api_verdict is not False:
                    return False

    return True
