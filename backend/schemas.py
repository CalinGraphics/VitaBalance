from pydantic import BaseModel, EmailStr, Field
from typing import Literal, Optional, List
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
    # Obiectiv caloric zilnic (kcal), opțional și doar informativ (nu influențează recomandările).
    caloric_goal: Optional[float] = None

class UserCreate(UserBase):
    # Limite aplicate doar la scriere: UserResponse (moștenit din UserBase) nu trebuie să pice pe rânduri vechi.
    # Oglindesc CHECK-urile din migrările 001 și 004 (users_caloric_goal_range, users_body_metrics_range, users_*_check).
    caloric_goal: Optional[float] = Field(default=None, ge=500, le=10000)
    age: int = Field(ge=1, le=120)
    sex: Literal["F", "M", "other"]
    weight: float = Field(ge=20, le=400)  # kg
    height: float = Field(ge=50, le=260)  # cm
    activity_level: Literal["sedentary", "moderate", "active", "very_active"]
    diet_type: Literal["omnivore", "vegetarian", "vegan", "pescatarian"]

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Lab Result Schemas
class LabResultBase(BaseModel):
    user_id: int
    hemoglobin: Optional[float] = None
    ferritin: Optional[float] = None  # ng/mL - pentru fier
    vitamin_d: Optional[float] = None  # ng/mL (25(OH)D)
    vitamin_b12: Optional[float] = None  # pg/mL
    calcium: Optional[float] = None  # mg/dL
    magnesium: Optional[float] = None  # mg/dL
    zinc: Optional[float] = None  # mcg/dL
    protein: Optional[float] = None  # g/dL
    # Nutrienți suplimentari conform tabelului
    folate: Optional[float] = None  # ng/mL (B9)
    vitamin_a: Optional[float] = None  # μg/dL
    vitamin_c: Optional[float] = None  # μmol/L (acid ascorbic plasmatic)
    iodine: Optional[float] = None  # μg/L
    vitamin_k: Optional[float] = None  # ng/mL (vit. K1 / filochinonă, dacă e raportat)
    potassium: Optional[float] = None  # mmol/L
    notes: Optional[str] = None

class LabResultCreate(LabResultBase):
    pass


class LabResultExtractFromTextRequest(BaseModel):
    text: str


class LabResultResponse(LabResultBase):
    id: int
    user_email: str = ""
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Recommendation Schemas
class RecommendationRequest(BaseModel):
    user_id: int
    exclude_food_ids: Optional[List[int]] = None
    replace_recommendation_id: Optional[int] = None
    # Opțional: înregistrează feedback înainte de înlocuire (un singur round-trip față de POST /feedback + replace).
    replace_feedback_rating: Optional[int] = None

# Feedback Schemas
class FeedbackCreate(BaseModel):
    user_id: int
    recommendation_id: int
    rating: int
    food_id: Optional[int] = None

