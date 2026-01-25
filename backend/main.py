from fastapi import FastAPI, HTTPException, Depends, Query
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
from services.auth import authenticate_user, create_user
from routers import supabase as supabase_router
from config import get_settings
from supabase_client import get_supabase_client
from pydantic import BaseModel, EmailStr
from typing import Optional
import inspect
import hashlib
import os

# Creează tabelele în baza de date
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="VitaBalance API",
    description="Sistem de recomandare cu explicații personalizate pentru deficiențe nutriționale",
    version="1.0.0"
)

settings = get_settings()

# CORS middleware pentru a permite comunicarea cu frontend-ul
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(supabase_router.router)

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

# Health/config endpoints
@app.get("/health")
async def health_check(settings=Depends(get_settings)):
    """
    Health check simplu care confirmă că aplicația și setările sunt încărcate.
    """
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "debug": settings.debug
    }


@app.get("/debug/rule-engine")
async def debug_rule_engine():
    """
    Debug endpoint: arată exact ce fișier `services/rule_engine.py` este încărcat
    și o amprentă a funcției `evaluate_food` (ca să evităm situațiile cu cod vechi/cached).
    """
    try:
        from services import rule_engine as re_mod
        src = inspect.getsource(re_mod.NutritionalRuleEngine.evaluate_food)
        src_hash = hashlib.md5(src.encode("utf-8")).hexdigest()
        return {
            "module_file": getattr(re_mod, "__file__", None),
            "module_mtime": os.path.getmtime(re_mod.__file__) if getattr(re_mod, "__file__", None) else None,
            "evaluate_food_md5": src_hash,
            "evaluate_food_first_line": src.splitlines()[0] if src else None,
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/config")
async def get_config(settings=Depends(get_settings)):
    """
    Expune configurația de bază pentru debug (fără secrete).
    """
    return {
        "app_name": settings.app_name,
        "debug": settings.debug
    }

# Schemas pentru autentificare
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    fullName: str
    bio: Optional[str] = None

class AuthResponse(BaseModel):
    email: str
    fullName: str
    bio: str

@app.get("/api/profile/by-email/{email}")
async def get_profile_by_email(email: str, db: Session = Depends(get_db)):
    """Obține profilul utilizatorului după email"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Returnează 404 pentru a permite frontend-ului să gestioneze corect
        raise HTTPException(status_code=404, detail="Profilul nu a fost găsit")
    return user

@app.post("/api/auth/login", response_model=AuthResponse)
async def login(credentials: LoginRequest):
    """Autentifică un utilizator"""
    user = authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Email sau parolă incorectă"
        )
    return AuthResponse(
        email=user["email"],
        fullName=user["fullName"],
        bio=user["bio"]
    )

@app.post("/api/auth/register", response_model=AuthResponse)
async def register(user_data: RegisterRequest):
    """Creează un cont nou"""
    try:
        # Validare email
        if not user_data.email or len(user_data.email.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Email-ul este obligatoriu"
            )
        
        # Validare nume complet
        if not user_data.fullName or len(user_data.fullName.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Numele complet este obligatoriu"
            )
        
        # Validare că parola există și nu este goală
        if not user_data.password:
            raise HTTPException(
                status_code=400,
                detail="Parola este obligatorie"
            )
        
        # Elimină spațiile de la început și sfârșit, dar păstrează parola originală pentru hash
        password_stripped = user_data.password.strip()
        if len(password_stripped) == 0:
            raise HTTPException(
                status_code=400,
                detail="Parola nu poate conține doar spații"
            )
        
        # Validare lungime parolă - minim 6 caractere
        if len(password_stripped) < 6:
            raise HTTPException(
                status_code=400,
                detail="Parola trebuie să aibă minim 6 caractere"
            )
        
        # Folosește parola originală (fără trim) pentru hash, dar validăm că nu este doar spații
        new_user = create_user(
            email=user_data.email.strip(),
            password=user_data.password,  # Folosim parola originală pentru hash
            fullName=user_data.fullName.strip(),
            bio=user_data.bio.strip() if user_data.bio else None
        )
        
        return AuthResponse(
            email=new_user["email"],
            fullName=new_user["fullName"],
            bio=new_user["bio"]
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Eroare detaliată la crearea contului: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Eroare la crearea contului: {str(e)}")

@app.post("/api/profile", response_model=UserResponse)
async def create_profile(user: UserCreate, db: Session = Depends(get_db)):
    """Creează sau actualizează profilul utilizatorului"""
    db_user = db.query(User).filter(User.email == user.email).first()
    
    # Verifică dacă s-au schimbat alergiile, diet_type sau medical_conditions
    # pentru a șterge recomandările vechi
    should_delete_recommendations = False
    if db_user:
        old_allergies = db_user.allergies or ''
        old_diet_type = db_user.diet_type or ''
        old_medical_conditions = db_user.medical_conditions or ''
        
        new_allergies = user.allergies or ''
        new_diet_type = user.diet_type or ''
        new_medical_conditions = user.medical_conditions or ''
        
        # Dacă s-au schimbat alergiile, tipul de dietă sau condițiile medicale,
        # șterge recomandările vechi pentru a forța regenerarea
        if (old_allergies != new_allergies or 
            old_diet_type != new_diet_type or 
            old_medical_conditions != new_medical_conditions):
            should_delete_recommendations = True
        
        # Actualizează profilul existent
        for key, value in user.dict(exclude_unset=True).items():
            setattr(db_user, key, value)
    else:
        # Creează profil nou
        db_user = User(**user.dict())
        db.add(db_user)
    
    # Șterge recomandările vechi dacă s-au schimbat criteriile relevante
    if should_delete_recommendations and db_user.id:
        db.query(Recommendation).filter(Recommendation.user_id == db_user.id).delete()
    
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
    
    # Sincronizează cu Supabase
    try:
        supabase = get_supabase_client()
        
        # Pregătește datele pentru Supabase
        supabase_data = {
            "user_id": db_lab_result.user_id,
            "hemoglobin": db_lab_result.hemoglobin,
            "ferritin": db_lab_result.ferritin,
            "vitamin_d": db_lab_result.vitamin_d,
            "vitamin_b12": db_lab_result.vitamin_b12,
            "calcium": db_lab_result.calcium,
            "magnesium": db_lab_result.magnesium,
            "zinc": db_lab_result.zinc,
            "protein": db_lab_result.protein,
            "folate": db_lab_result.folate,
            "vitamin_a": db_lab_result.vitamin_a,
            "iodine": db_lab_result.iodine,
            "vitamin_k": db_lab_result.vitamin_k,
            "potassium": db_lab_result.potassium,
            "notes": db_lab_result.notes,
            "created_at": db_lab_result.created_at.isoformat() if db_lab_result.created_at else None
        }
        
        # Elimină câmpurile None pentru a nu suprascrie cu null în Supabase
        supabase_data = {k: v for k, v in supabase_data.items() if v is not None}
        
        # Inserează în Supabase
        supabase_response = supabase.table('lab_results').insert(supabase_data).execute()
        
        if not supabase_response.data:
            print(f"Warning: Supabase insert returned no data for lab_result user_id {db_lab_result.user_id}")
    except Exception as e:
        # Loghează eroarea dar nu oprește procesul dacă actualizarea în Supabase eșuează
        print(f"Warning: Failed to sync lab_result to Supabase: {str(e)}")
        # Nu aruncăm eroare pentru a nu afecta funcționalitatea principală
    
    return db_lab_result

@app.get("/api/lab-results/{user_id}", response_model=list[LabResultResponse])
async def get_lab_results(user_id: int, db: Session = Depends(get_db)):
    """Obține rezultatele analizelor pentru un utilizator"""
    lab_results = db.query(LabResult).filter(LabResult.user_id == user_id).all()
    return lab_results

@app.post("/api/recommendations", response_model=list[RecommendationResponse])
async def get_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db),
    force_regenerate: bool = Query(False, description="Forțează regenerarea recomandărilor")
):
    """
    Generează recomandări personalizate pentru utilizator
    Dacă există deja recomandări, le returnează pe cele existente.
    Pentru regenerare, folosește DELETE /api/recommendations/{user_id} apoi POST din nou.
    Sau trimite force_regenerate=True în query params.
    """
    try:
        # Obține utilizatorul
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilizatorul nu a fost găsit")
        
        # Reîncarcă utilizatorul pentru a obține datele actualizate
        db.refresh(user)
        
        # Verifică dacă există recomandări existente
        existing_recommendations = db.query(Recommendation).filter(
            Recommendation.user_id == request.user_id
        ).first()
        
        # Flag pentru a indica dacă trebuie să generăm recomandări noi
        should_generate_new = force_regenerate or not existing_recommendations
        
        # Dacă se forțează regenerarea sau nu există recomandări, șterge cele vechi
        if force_regenerate and existing_recommendations:
            db.query(Recommendation).filter(Recommendation.user_id == request.user_id).delete()
            db.commit()
        
        # Obține feedback-urile utilizatorului (dacă există)
        user_feedbacks = db.query(Feedback).filter(Feedback.user_id == request.user_id).all()
        feedback_by_food = {}
        for feedback in user_feedbacks:
            if feedback.recommendation_id:
                rec = db.query(Recommendation).filter(Recommendation.id == feedback.recommendation_id).first()
                if rec:
                    food_id = rec.food_id
                    if food_id not in feedback_by_food:
                        feedback_by_food[food_id] = []
                    feedback_by_food[food_id].append(feedback)
        
        # Obține rezultatele analizelor
        lab_results = db.query(LabResult).filter(
            LabResult.user_id == request.user_id
        ).order_by(LabResult.created_at.desc()).first()
        
        # Obține toate alimentele
        foods = db.query(Food).all()
        
        # Calculează deficiențele
        calculator = DeficitCalculator()
        deficits = calculator.calculate_deficits(user, lab_results)
        
        # Verifică dacă există alimente în baza de date
        if not foods:
            raise HTTPException(
                status_code=404, 
                detail="Nu există alimente în baza de date. Vă rugăm să contactați administratorul."
            )
        
        # Generează recomandări doar dacă trebuie (force_regenerate sau nu există recomandări)
        recommendations = []
        if should_generate_new:
            recommender = RecommenderService()
            recommendations = recommender.generate_recommendations(
                user=user,
                deficits=deficits,
                foods=foods,
                lab_results=lab_results,
                user_feedbacks=user_feedbacks,
                feedback_by_food=feedback_by_food
            )
        
        # Verifică dacă s-au generat recomandări
        if not recommendations and should_generate_new:
            # Încearcă să genereze recomandări generale dacă nu există deficiențe
            if not any(d > 0 for d in deficits.values()):
                # Generează recomandări bazate pe valoarea nutrițională generală
                recommendations = recommender.generate_recommendations(
                    user=user,
                    deficits={},  # Fără deficiențe pentru recomandări generale
                    foods=foods,
                    lab_results=lab_results,
                    user_feedbacks=user_feedbacks,
                    feedback_by_food=feedback_by_food
                )
            
            if not recommendations:
                raise HTTPException(
                    status_code=404,
                    detail="Nu s-au găsit alimente compatibile cu criteriile dumneavoastră. Vă rugăm să verificați profilul și restricțiile dietetice."
                )
        
        # Dacă nu trebuie să generăm recomandări noi și există recomandări, returnează-le pe cele existente
        if not should_generate_new and existing_recommendations and not recommendations:
            existing_recs = db.query(Recommendation).filter(
                Recommendation.user_id == request.user_id
            ).order_by(Recommendation.coverage_percentage.desc(), Recommendation.score.desc()).limit(10).all()
            
            recommendations_with_explanations = []
            for rec in existing_recs:
                food = db.query(Food).filter(Food.id == rec.food_id).first()
                if not food:
                    continue
                
                recommendations_with_explanations.append({
                    'food_id': food.id,
                    'food': {
                        'id': food.id,
                        'name': food.name,
                        'category': food.category,
                        'image_url': food.image_url
                    },
                    'score': rec.score,
                    'coverage': rec.coverage_percentage or 0,
                    'explanation': {
                        'text': rec.explanation,
                        'portion': rec.portion_suggested or 150,
                        'reasons': [rec.explanation],
                        'tips': None,
                        'alternatives': None
                    },
                    'recommendation_id': rec.id
                })
            
            if recommendations_with_explanations:
                return recommendations_with_explanations
        
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
        
        # Sincronizează recomandările cu Supabase
        try:
            supabase = get_supabase_client()
            
            # Pregătește datele pentru Supabase pentru fiecare recomandare
            supabase_recommendations = []
            for rec_explanation in recommendations_with_explanations:
                # Folosește recommendation_id direct din rec_explanation
                recommendation_id = rec_explanation.get('recommendation_id')
                if not recommendation_id:
                    continue
                
                # Găsește recomandarea din baza de date folosind ID-ul
                db_rec = db.query(Recommendation).filter(
                    Recommendation.id == recommendation_id
                ).first()
                
                if db_rec:
                    supabase_data = {
                        "user_id": db_rec.user_id,
                        "food_id": db_rec.food_id,
                        "score": db_rec.score,
                        "explanation": db_rec.explanation,
                        "portion_suggested": db_rec.portion_suggested,
                        "coverage_percentage": db_rec.coverage_percentage,
                        "created_at": db_rec.created_at.isoformat() if db_rec.created_at else None
                    }
                    
                    # Elimină câmpurile None
                    supabase_data = {k: v for k, v in supabase_data.items() if v is not None}
                    supabase_recommendations.append(supabase_data)
            
            # Inserează toate recomandările în Supabase (dacă există)
            if supabase_recommendations:
                # Șterge recomandările vechi pentru acest utilizator în Supabase (dacă există)
                try:
                    supabase.table('recommendations').delete().eq('user_id', user.id).execute()
                except Exception as e:
                    print(f"Warning: Could not delete old recommendations in Supabase: {str(e)}")
                
                # Inserează noile recomandări
                supabase_response = supabase.table('recommendations').insert(supabase_recommendations).execute()
                
                if not supabase_response.data:
                    print(f"Warning: Supabase insert returned no data for recommendations user_id {user.id}")
        except Exception as e:
            # Loghează eroarea dar nu oprește procesul dacă actualizarea în Supabase eșuează
            print(f"Warning: Failed to sync recommendations to Supabase: {str(e)}")
            # Nu aruncăm eroare pentru a nu afecta funcționalitatea principală
        
        return recommendations_with_explanations
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Eroare la generarea recomandărilor: {str(e)}")

@app.post("/api/feedback")
async def create_feedback(feedback: FeedbackCreate, db: Session = Depends(get_db)):
    """Salvează feedback-ul utilizatorului pentru o recomandare"""
    # Validare rating
    if feedback.rating < -1 or feedback.rating > 5:
        raise HTTPException(
            status_code=400, 
            detail="Rating trebuie să fie între -1 (dislike) și 5 (excelent)"
        )
    
    # Verifică dacă utilizatorul există
    user = db.query(User).filter(User.id == feedback.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilizatorul nu a fost găsit")
    
    # Verifică dacă recomandarea există (dacă este specificată)
    if feedback.recommendation_id:
        recommendation = db.query(Recommendation).filter(
            Recommendation.id == feedback.recommendation_id
        ).first()
        if not recommendation:
            raise HTTPException(status_code=404, detail="Recomandarea nu a fost găsită")
    
    try:
        db_feedback = Feedback(**feedback.dict())
        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)
        
        # Sincronizează cu Supabase
        try:
            supabase = get_supabase_client()
            
            # Pregătește datele pentru Supabase
            supabase_data = {
                "user_id": db_feedback.user_id,
                "recommendation_id": db_feedback.recommendation_id,
                "rating": db_feedback.rating,
                "comment": db_feedback.comment,
                "tried": db_feedback.tried,
                "worked": db_feedback.worked,
                "created_at": db_feedback.created_at.isoformat() if db_feedback.created_at else None
            }
            
            # Elimină câmpurile None pentru a nu suprascrie cu null în Supabase
            supabase_data = {k: v for k, v in supabase_data.items() if v is not None}
            
            # Inserează în Supabase
            supabase_response = supabase.table('feedback').insert(supabase_data).execute()
            
            if not supabase_response.data:
                print(f"Warning: Supabase insert returned no data for feedback id {db_feedback.id}")
        except Exception as e:
            # Loghează eroarea dar nu oprește procesul dacă actualizarea în Supabase eșuează
            print(f"Warning: Failed to sync feedback to Supabase: {str(e)}")
            # Nu aruncăm eroare pentru a nu afecta funcționalitatea principală
        
        return {"message": "Feedback salvat cu succes", "id": db_feedback.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Eroare la salvarea feedback-ului: {str(e)}")

@app.get("/api/foods")
async def get_foods(db: Session = Depends(get_db)):
    """Obține lista tuturor alimentelor"""
    foods = db.query(Food).all()
    return foods

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

