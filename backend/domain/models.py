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
    full_name: Optional[str] = None
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
    recommendation_id: Optional[int] = None
    rating: int = 0
    comment: Optional[str] = None
    tried: bool = False
    worked: Optional[bool] = None
    created_at: Optional[datetime] = None


def row_to_user(row: dict) -> UserProfile:
    """Build UserProfile from Supabase/DB row (snake_case)."""
    return UserProfile(
        id=row["id"],
        email=row.get("email", ""),
        name=row.get("name") or row.get("full_name") or "",
        age=row.get("age", 0),
        sex=row.get("sex", "other"),
        weight=float(row.get("weight", 0)),
        height=float(row.get("height", 0)),
        activity_level=row.get("activity_level", "moderate"),
        diet_type=row.get("diet_type", "omnivore"),
        allergies=row.get("allergies"),
        medical_conditions=row.get("medical_conditions"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        full_name=row.get("full_name"),
        bio=row.get("bio"),
    )


def row_to_food(row: dict) -> FoodItem:
    """Build FoodItem from Supabase/DB row."""
    return FoodItem(
        id=row["id"],
        name=row.get("name", ""),
        category=row.get("category", ""),
        iron=float(row.get("iron", 0)),
        calcium=float(row.get("calcium", 0)),
        vitamin_d=float(row.get("vitamin_d", 0)),
        vitamin_b12=float(row.get("vitamin_b12", 0)),
        magnesium=float(row.get("magnesium", 0)),
        protein=float(row.get("protein", 0)),
        zinc=float(row.get("zinc", 0)),
        vitamin_c=float(row.get("vitamin_c", 0)),
        fiber=float(row.get("fiber", 0)),
        calories=float(row.get("calories", 0)),
        folate=float(row.get("folate", 0)),
        vitamin_a=float(row.get("vitamin_a", 0)),
        iodine=float(row.get("iodine", 0)),
        vitamin_k=float(row.get("vitamin_k", 0)),
        potassium=float(row.get("potassium", 0)),
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
    """Build RecommendationItem from Supabase/DB row."""
    return RecommendationItem(
        id=row["id"],
        user_id=row["user_id"],
        food_id=row["food_id"],
        score=float(row.get("score", 0)),
        explanation=row.get("explanation", ""),
        portion_suggested=float(row.get("portion_suggested", 150)),
        coverage_percentage=row.get("coverage_percentage"),
        created_at=row.get("created_at"),
    )


def row_to_feedback(row: dict) -> FeedbackItem:
    """Build FeedbackItem from Supabase/DB row."""
    return FeedbackItem(
        id=row["id"],
        user_id=row["user_id"],
        recommendation_id=row.get("recommendation_id"),
        rating=row.get("rating", 0),
        comment=row.get("comment"),
        tried=row.get("tried", False),
        worked=row.get("worked"),
        created_at=row.get("created_at"),
    )
