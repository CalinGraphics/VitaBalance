"""
Data access layer – Supabase only. Single source of truth.
"""
from .user_repository import UserRepository
from .food_repository import FoodRepository
from .lab_result_repository import LabResultRepository
from .recommendation_repository import RecommendationRepository
from .feedback_repository import FeedbackRepository

__all__ = [
    "UserRepository",
    "FoodRepository",
    "LabResultRepository",
    "RecommendationRepository",
    "FeedbackRepository",
]
