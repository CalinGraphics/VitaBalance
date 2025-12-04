from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str
    age: int
    sex: str
    weight: float
    height: float
    activity_level: str
    diet_type: str
    allergies: Optional[str] = None
    medical_conditions: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Lab Result Schemas
class LabResultBase(BaseModel):
    user_id: int
    hemoglobin: Optional[float] = None
    ferritin: Optional[float] = None
    vitamin_d: Optional[float] = None
    vitamin_b12: Optional[float] = None
    calcium: Optional[float] = None
    magnesium: Optional[float] = None
    zinc: Optional[float] = None
    protein: Optional[float] = None
    notes: Optional[str] = None

class LabResultCreate(LabResultBase):
    pass

class LabResultResponse(LabResultBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Recommendation Schemas
class RecommendationRequest(BaseModel):
    user_id: int

class FoodInfo(BaseModel):
    id: int
    name: str
    category: str
    image_url: Optional[str] = None

class ExplanationDetail(BaseModel):
    text: str
    portion: float
    reasons: List[str]
    tips: Optional[List[str]] = None
    alternatives: Optional[List[str]] = None

class RecommendationResponse(BaseModel):
    food_id: int
    food: FoodInfo
    score: float
    coverage: float
    explanation: ExplanationDetail
    recommendation_id: int

# Feedback Schemas
class FeedbackCreate(BaseModel):
    user_id: int
    recommendation_id: Optional[int] = None
    rating: int
    comment: Optional[str] = None
    tried: bool = False
    worked: Optional[bool] = None

