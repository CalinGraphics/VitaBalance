"""
Domain models – plain dataclasses for business logic.
No DB dependency; populated from Supabase repositories.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Any, Tuple


@dataclass
class UserProfile:
    id: int
    email: str
    name: str
    age: int
    sex: str
    weight: float
    height: float
    activity_level: str
    diet_type: str
    allergies: Optional[str] = None
    medical_conditions: Optional[str] = None
    rec_refresh_status: Optional[str] = "idle"
    rec_refresh_error: Optional[str] = None
    rec_refresh_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Obiectiv caloric zilnic (kcal), opțional. Strict informativ: nu influențează recomandările (vezi services/nutrition/energy.py pentru avertisment).
    caloric_goal: Optional[float] = None
    # Calea pozei de profil în bucket-ul privat `avatars` (migrarea 010); None = fără poză.
    avatar_path: Optional[str] = None


@dataclass
class FoodItem:
    """
    Aliment din catalog. Valorile nutriționale sunt la 100 g (100 ml); None = necunoscut (NU „zero”).
    Doar alimentele cu validated=True (catalogul USDA, migrările 011–012) intră în recomandări.
    """
    id: int
    name: str
    category: str
    iron: Optional[float] = None
    calcium: Optional[float] = None
    vitamin_d: Optional[float] = None
    vitamin_b12: Optional[float] = None
    magnesium: Optional[float] = None
    protein: Optional[float] = None
    zinc: Optional[float] = None
    vitamin_c: Optional[float] = None
    fiber: Optional[float] = None
    calories: Optional[float] = None
    folate: Optional[float] = None
    vitamin_a: Optional[float] = None
    iodine: Optional[float] = None
    vitamin_k: Optional[float] = None
    potassium: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    free_sugar: Optional[float] = None
    cholesterol: Optional[float] = None
    allergens: Optional[str] = None
    created_at: Optional[datetime] = None
    name_en: Optional[str] = None  # numele în engleză (foods.name_en); dacă lipsește se folosește `name`
    # --- catalogul validat (migrarea 011) ---
    food_key: Optional[str] = None
    fdc_id: Optional[int] = None
    validated: bool = False
    category_key: Optional[str] = None
    portion_g: Optional[float] = None
    portion_label_ro: Optional[str] = None
    portion_label_en: Optional[str] = None
    animal_source: Optional[str] = None
    allergen_codes: Tuple[str, ...] = ()
    flags: Tuple[str, ...] = ()
    sugars: Optional[float] = None
    alcohol: Optional[float] = None
    phosphorus: Optional[float] = None
    sodium: Optional[float] = None

    def has_flag(self, flag: str) -> bool:
        return flag in self.flags


def food_display_name(food: "FoodItem", lang: str = "ro") -> str:
    """Numele alimentului în limba cerută ('en' -> name_en, cu revenire la nume dacă nu e tradus)."""
    if str(lang or "").lower().startswith("en") and food.name_en:
        return food.name_en
    return food.name


@dataclass
class LabResultItem:
    id: int
    user_id: int
    user_email: Optional[str] = None
    hemoglobin: Optional[float] = None
    ferritin: Optional[float] = None
    vitamin_d: Optional[float] = None
    vitamin_b12: Optional[float] = None
    calcium: Optional[float] = None
    magnesium: Optional[float] = None
    zinc: Optional[float] = None
    protein: Optional[float] = None
    folate: Optional[float] = None
    vitamin_a: Optional[float] = None
    vitamin_c: Optional[float] = None
    iodine: Optional[float] = None
    vitamin_k: Optional[float] = None
    potassium: Optional[float] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class RecommendationItem:
    id: int
    user_id: int
    food_id: int
    score: float
    explanation: str
    portion_suggested: float
    coverage_percentage: Optional[float] = None
    explanation_json: Optional[Any] = None
    reasons: Optional[List[str]] = None
    tips: Optional[List[str]] = None
    created_at: Optional[datetime] = None


@dataclass
class FeedbackItem:
    """Votul unui utilizator pentru un aliment; recomandarea asociată e opțională (dispare la regenerare)."""

    id: int
    user_id: int
    food_id: int
    recommendation_id: Optional[int] = None
    rating: int = 0
    created_at: Optional[datetime] = None


@dataclass
class CheckIn:
    """O zi din jurnalul de stare (wellbeing_checkins, migrarea 015)."""

    id: int
    user_id: int
    checked_on: str  # ISO date (YYYY-MM-DD)
    symptoms: Tuple[str, ...] = ()
    severity: Optional[int] = None  # 1 ușor, 2 moderat, 3 puternic
    energy: Optional[int] = None    # 1..5
    weight: Optional[float] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


def row_to_checkin(row: dict) -> CheckIn:
    return CheckIn(
        id=int(row["id"]),
        user_id=int(row["user_id"]),
        checked_on=str(row.get("checked_on"))[:10],
        symptoms=tuple(row.get("symptoms") or ()),
        severity=row.get("severity"),
        energy=row.get("energy"),
        weight=row.get("weight"),
        notes=row.get("notes"),
        created_at=row.get("created_at"),
    )


def _num(val, default: float = 0) -> float:
    """Convert value to float, use default if None or invalid."""
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def row_to_user(row: dict) -> UserProfile:
    """Build UserProfile from Supabase/DB row (snake_case). Toleră NULL pentru câmpuri numerice."""
    return UserProfile(
        id=row["id"],
        email=row.get("email") or "",
        name=row.get("name") or "",
        age=int(row.get("age") or 0),
        sex=row.get("sex") or "other",
        weight=_num(row.get("weight"), 0),
        height=_num(row.get("height"), 0),
        activity_level=row.get("activity_level") or "moderate",
        diet_type=row.get("diet_type") or "omnivore",
        allergies=row.get("allergies"),
        medical_conditions=row.get("medical_conditions"),
        rec_refresh_status=row.get("rec_refresh_status") or "idle",
        rec_refresh_error=row.get("rec_refresh_error"),
        rec_refresh_at=row.get("rec_refresh_at"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        caloric_goal=_num(row.get("caloric_goal"), 0) or None,
        avatar_path=row.get("avatar_path") or None,
    )


def _opt(val) -> Optional[float]:
    """Ca _num, dar păstrează lipsa valorii (None) — o valoare nutrițională lipsă nu e zero."""
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


_FOOD_NUTRIENT_COLUMNS = (
    "iron", "calcium", "vitamin_d", "vitamin_b12", "magnesium", "protein", "zinc", "vitamin_c", "fiber", "calories",
    "folate", "vitamin_a", "iodine", "vitamin_k", "potassium", "carbs", "fat", "free_sugar", "cholesterol",
    "sugars", "alcohol", "phosphorus", "sodium",
)


def row_to_food(row: dict) -> FoodItem:
    return FoodItem(
        id=row["id"],
        name=row.get("name") or "",
        category=row.get("category") or "necunoscut",
        allergens=row.get("allergens"),
        created_at=row.get("created_at"),
        name_en=row.get("name_en") or None,
        food_key=row.get("food_key"),
        fdc_id=row.get("fdc_id"),
        validated=bool(row.get("validated")),
        category_key=row.get("category_key"),
        portion_g=_opt(row.get("portion_g")),
        portion_label_ro=row.get("portion_label_ro"),
        portion_label_en=row.get("portion_label_en"),
        animal_source=row.get("animal_source"),
        allergen_codes=tuple(row.get("allergen_codes") or ()),
        flags=tuple(row.get("flags") or ()),
        **{col: _opt(row.get(col)) for col in _FOOD_NUTRIENT_COLUMNS},
    )


def food_from_catalog_entry(entry: dict, food_id: int) -> FoodItem:
    """FoodItem din data/foods_catalog.json (teste offline și verificări fără baza de date)."""
    from data.food_catalog_spec import CATEGORIES

    row = {
        "id": food_id, "name": entry["name_ro"], "name_en": entry["name_en"],
        "category": CATEGORIES[entry["category"]][0], "category_key": entry["category"],
        "food_key": entry["key"], "fdc_id": entry["fdc_id"], "validated": entry["validation"]["ok"],
        "portion_g": entry["portion_g"], "portion_label_ro": entry["portion_ro"], "portion_label_en": entry["portion_en"],
        "animal_source": entry["animal"], "allergen_codes": entry["allergens"], "flags": entry["flags"],
        **entry["per100g"],
    }
    return row_to_food(row)


def row_to_lab_result(row: dict) -> LabResultItem:
    """Build LabResultItem from Supabase/DB row."""
    return LabResultItem(
        id=row["id"],
        user_id=row["user_id"],
        user_email=row.get("user_email"),
        hemoglobin=row.get("hemoglobin"),
        ferritin=row.get("ferritin"),
        vitamin_d=row.get("vitamin_d"),
        vitamin_b12=row.get("vitamin_b12"),
        calcium=row.get("calcium"),
        magnesium=row.get("magnesium"),
        zinc=row.get("zinc"),
        protein=row.get("protein"),
        folate=row.get("folate"),
        vitamin_a=row.get("vitamin_a"),
        vitamin_c=row.get("vitamin_c"),
        iodine=row.get("iodine"),
        vitamin_k=row.get("vitamin_k"),
        potassium=row.get("potassium"),
        notes=row.get("notes"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def row_to_recommendation(row: dict) -> RecommendationItem:
    """Build RecommendationItem from Supabase/DB row. Toleră NULL pentru numerice."""
    return RecommendationItem(
        id=row["id"],
        user_id=row["user_id"],
        food_id=row["food_id"],
        score=_num(row.get("score"), 0),
        explanation=row.get("explanation") or "",
        portion_suggested=_num(row.get("portion_suggested"), 150),
        coverage_percentage=row.get("coverage_percentage"),
        explanation_json=row.get("explanation_json"),
        reasons=row.get("reasons"),
        tips=row.get("tips"),
        created_at=row.get("created_at"),
    )


def row_to_feedback(row: dict) -> FeedbackItem:
    """Build FeedbackItem from Supabase/DB row."""
    rid = row.get("recommendation_id")
    return FeedbackItem(
        id=row["id"],
        user_id=row["user_id"],
        food_id=int(row["food_id"]),
        recommendation_id=int(rid) if rid is not None else None,
        rating=row.get("rating", 0),
        created_at=row.get("created_at"),
    )
