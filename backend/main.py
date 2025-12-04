from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uvicorn

from database import SessionLocal, engine, Base
from models import User, LabResult, Food, Recommendation, Feedback
from schemas import (
    UserCreate, UserResponse,
    LabResultCreate, LabResultResponse,
    RecommendationRequest, RecommendationResponse,
    FeedbackCreate
)
from services.recommender import RecommenderService
from services.deficit_calculator import DeficitCalculator
from services.explanation_generator import ExplanationGenerator

# Creează tabelele în baza de date
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="VitaBalance API",
    description="Sistem de recomandare cu explicații personalizate pentru deficiențe nutriționale",
    version="1.0.0"
)

# CORS middleware pentru a permite comunicarea cu frontend-ul
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency pentru a obține sesiunea de bază de date
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "VitaBalance API - Sistem de recomandare nutrițională"}

@app.post("/api/profile", response_model=UserResponse)
async def create_profile(user: UserCreate, db: Session = Depends(get_db)):
    """Creează sau actualizează profilul utilizatorului"""
    db_user = db.query(User).filter(User.email == user.email).first()
    
    if db_user:
        # Actualizează profilul existent
        for key, value in user.dict(exclude_unset=True).items():
            setattr(db_user, key, value)
    else:
        # Creează profil nou
        db_user = User(**user.dict())
        db.add(db_user)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/api/profile/{user_id}", response_model=UserResponse)
async def get_profile(user_id: int, db: Session = Depends(get_db)):
    """Obține profilul utilizatorului"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilizatorul nu a fost găsit")
    return user

@app.post("/api/lab-results", response_model=LabResultResponse)
async def create_lab_results(lab_result: LabResultCreate, db: Session = Depends(get_db)):
    """Salvează rezultatele analizelor medicale"""
    db_lab_result = LabResult(**lab_result.dict())
    db.add(db_lab_result)
    db.commit()
    db.refresh(db_lab_result)
    return db_lab_result

@app.get("/api/lab-results/{user_id}", response_model=list[LabResultResponse])
async def get_lab_results(user_id: int, db: Session = Depends(get_db)):
    """Obține rezultatele analizelor pentru un utilizator"""
    lab_results = db.query(LabResult).filter(LabResult.user_id == user_id).all()
    return lab_results

@app.post("/api/recommendations", response_model=list[RecommendationResponse])
async def get_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):
    """Generează recomandări personalizate pentru utilizator"""
    try:
        # Obține utilizatorul
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilizatorul nu a fost găsit")
        
        # Obține rezultatele analizelor
        lab_results = db.query(LabResult).filter(
            LabResult.user_id == request.user_id
        ).order_by(LabResult.created_at.desc()).first()
        
        # Obține toate alimentele
        foods = db.query(Food).all()
        
        # Calculează deficiențele
        calculator = DeficitCalculator()
        deficits = calculator.calculate_deficits(user, lab_results)
        
        # Generează recomandări
        recommender = RecommenderService()
        recommendations = recommender.generate_recommendations(
            user=user,
            deficits=deficits,
            foods=foods,
            lab_results=lab_results
        )
        
        # Generează explicații pentru fiecare recomandare
        explanation_gen = ExplanationGenerator()
        recommendations_with_explanations = []
        
        for rec in recommendations[:10]:  # Top 10 recomandări
            food = next((f for f in foods if f.id == rec['food_id']), None)
            if food:
                explanation = explanation_gen.generate_explanation(
                    food=food,
                    user=user,
                    deficits=deficits,
                    score=rec['score'],
                    coverage=rec['coverage']
                )
                
                # Pregătește recomandarea pentru salvare
                db_recommendation = Recommendation(
                    user_id=user.id,
                    food_id=food.id,
                    score=rec['score'],
                    explanation=explanation['text'],
                    portion_suggested=explanation['portion'],
                    coverage_percentage=rec['coverage']
                )
                db.add(db_recommendation)
                db.flush()  # Flush pentru a obține ID-ul fără commit complet
                
                recommendations_with_explanations.append({
                    'food_id': food.id,
                    'food': {
                        'id': food.id,
                        'name': food.name,
                        'category': food.category,
                        'image_url': food.image_url
                    },
                    'score': rec['score'],
                    'coverage': rec['coverage'],
                    'explanation': explanation,
                    'recommendation_id': db_recommendation.id
                })
        
        db.commit()  # Commit toate recomandările odată
        
        return recommendations_with_explanations
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Eroare la generarea recomandărilor: {str(e)}")

@app.post("/api/feedback")
async def create_feedback(feedback: FeedbackCreate, db: Session = Depends(get_db)):
    """Salvează feedback-ul utilizatorului pentru o recomandare"""
    db_feedback = Feedback(**feedback.dict())
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return {"message": "Feedback salvat cu succes", "id": db_feedback.id}

@app.get("/api/foods")
async def get_foods(db: Session = Depends(get_db)):
    """Obține lista tuturor alimentelor"""
    foods = db.query(Food).all()
    return foods

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

