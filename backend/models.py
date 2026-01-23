from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    age = Column(Integer)
    sex = Column(String)  # 'M', 'F', 'other'
    weight = Column(Float)  # kg
    height = Column(Float)  # cm
    activity_level = Column(String)  # 'sedentary', 'moderate', 'active', 'very_active'
    diet_type = Column(String)  # 'omnivore', 'vegetarian', 'vegan', 'pescatarian'
    allergies = Column(Text)  # JSON string sau comma-separated
    medical_conditions = Column(Text)  # JSON string sau comma-separated
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    lab_results = relationship("LabResult", back_populates="user")
    recommendations = relationship("Recommendation", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")

class LabResult(Base):
    __tablename__ = "lab_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    hemoglobin = Column(Float, nullable=True)  # g/dL
    ferritin = Column(Float, nullable=True)  # ng/mL - pentru fier
    vitamin_d = Column(Float, nullable=True)  # ng/mL (25(OH)D)
    vitamin_b12 = Column(Float, nullable=True)  # pg/mL
    calcium = Column(Float, nullable=True)  # mg/dL
    magnesium = Column(Float, nullable=True)  # mg/dL
    zinc = Column(Float, nullable=True)  # mcg/dL
    protein = Column(Float, nullable=True)  # g/dL
    # Nutrienți suplimentari conform tabelului
    folate = Column(Float, nullable=True)  # ng/mL (B9)
    vitamin_a = Column(Float, nullable=True)  # μg/dL
    iodine = Column(Float, nullable=True)  # μg/L
    vitamin_k = Column(Float, nullable=True)  # PT/INR (indirect, poate fi null)
    potassium = Column(Float, nullable=True)  # mmol/L
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="lab_results")

class Food(Base):
    __tablename__ = "foods"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String)  # 'legume', 'carne', 'lactate', 'cereale', etc.
    # Valori nutriționale per 100g
    iron = Column(Float, default=0)  # mg
    calcium = Column(Float, default=0)  # mg
    vitamin_d = Column(Float, default=0)  # IU
    vitamin_b12 = Column(Float, default=0)  # mcg
    magnesium = Column(Float, default=0)  # mg
    protein = Column(Float, default=0)  # g
    zinc = Column(Float, default=0)  # mg
    vitamin_c = Column(Float, default=0)  # mg
    fiber = Column(Float, default=0)  # g
    calories = Column(Float, default=0)  # kcal
    # Nutrienți suplimentari conform tabelului
    folate = Column(Float, default=0)  # mcg (B9)
    vitamin_a = Column(Float, default=0)  # mcg
    iodine = Column(Float, default=0)  # mcg
    vitamin_k = Column(Float, default=0)  # mcg
    potassium = Column(Float, default=0)  # mg
    allergens = Column(Text, nullable=True)  # JSON string sau comma-separated
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    recommendations = relationship("Recommendation", back_populates="food")

class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    food_id = Column(Integer, ForeignKey("foods.id"))
    score = Column(Float)
    explanation = Column(Text)
    portion_suggested = Column(Float)  # grame
    coverage_percentage = Column(Float)  # procent din deficit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="recommendations")
    food = relationship("Food", back_populates="recommendations")
    feedbacks = relationship("Feedback", back_populates="recommendation")

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), nullable=True)
    rating = Column(Integer)  # 1-5 sau -1 (dislike), 1 (like)
    comment = Column(Text, nullable=True)
    tried = Column(Boolean, default=False)
    worked = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="feedbacks")
    recommendation = relationship("Recommendation", back_populates="feedbacks")