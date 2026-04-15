"""
Domain models – plain dataclasses for business logic.
No DB dependency; populated from Supabase repositories.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    bio: Optional[str] = None


@dataclass
class FoodItem:
    id: int
    name: str
    category: str
    iron: float = 0
    calcium: float = 0
    vitamin_d: float = 0
    vitamin_b12: float = 0
    magnesium: float = 0
    protein: float = 0
    zinc: float = 0
    vitamin_c: float = 0
    fiber: float = 0
    calories: float = 0
    folate: float = 0
    vitamin_a: float = 0
    iodine: float = 0
    vitamin_k: float = 0
    potassium: float = 0
    carbs: float = 0          # nou
    fat: float = 0            # nou
    free_sugar: float = 0     # nou
    cholesterol: float = 0    # nou
    allergens: Optional[str] = None
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class LabResultItem:
    id: int
    user_id: int
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
    iodine: Optional[float] = None
    vitamin_k: Optional[float] = None
    potassium: Optional[float] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class RecommendationItem:
    id: int
    user_id: int
    food_id: int
    score: float
    explanation: str
    portion_suggested: float
    coverage_percentage: Optional[float] = None
    created_at: Optional[datetime] = None


@dataclass
class FeedbackItem:
    id: int
    user_id: int
    recommendation_id: int
    rating: int = 0
    created_at: Optional[datetime] = None


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
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        bio=row.get("bio"),
    )


def row_to_food(row: dict) -> FoodItem:
    return FoodItem(
        id=row["id"],
        name=row.get("name") or "",
        category=row.get("category") or "necunoscut",
        iron=_num(row.get("iron")),
        calcium=_num(row.get("calcium")),
        vitamin_d=_num(row.get("vitamin_d")),
        vitamin_b12=_num(row.get("vitamin_b12")),
        magnesium=_num(row.get("magnesium")),
        protein=_num(row.get("protein")),
        zinc=_num(row.get("zinc")),
        vitamin_c=_num(row.get("vitamin_c")),
        fiber=_num(row.get("fiber")),
        calories=_num(row.get("calories")),
        folate=_num(row.get("folate")),
        vitamin_a=_num(row.get("vitamin_a")),
        iodine=_num(row.get("iodine")),
        vitamin_k=_num(row.get("vitamin_k")),
        potassium=_num(row.get("potassium")),
        carbs=_num(row.get("carbs")),           # nou
        fat=_num(row.get("fat")),               # nou
        free_sugar=_num(row.get("free_sugar")), # nou
        cholesterol=_num(row.get("cholesterol")), # nou
        allergens=row.get("allergens"),
        image_url=row.get("image_url"),
        created_at=row.get("created_at"),
    )


def row_to_lab_result(row: dict) -> LabResultItem:
    """Build LabResultItem from Supabase/DB row."""
    return LabResultItem(
        id=row["id"],
        user_id=row["user_id"],
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
        iodine=row.get("iodine"),
        vitamin_k=row.get("vitamin_k"),
        potassium=row.get("potassium"),
        notes=row.get("notes"),
        created_at=row.get("created_at"),
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
        created_at=row.get("created_at"),
    )


def row_to_feedback(row: dict) -> FeedbackItem:
    """Build FeedbackItem from Supabase/DB row."""
    return FeedbackItem(
        id=row["id"],
        user_id=row["user_id"],
        recommendation_id=row["recommendation_id"],
        rating=row.get("rating", 0),
        created_at=row.get("created_at"),
    )
