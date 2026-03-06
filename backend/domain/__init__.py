"""
Domain models – plain data structures used by business logic.
No SQLAlchemy; populated from Supabase or API input.
"""
from .models import (
    UserProfile,
    FoodItem,
    LabResultItem,
    RecommendationItem,
    FeedbackItem,
)

__all__ = [
    "UserProfile",
    "FoodItem",
    "LabResultItem",
    "RecommendationItem",
    "FeedbackItem",
]
