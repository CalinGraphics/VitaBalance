"""
VitaBalance API – production-ready.
Data: Supabase only. Auth: JWT middleware (to be added). No SQLite.
"""
from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import uvicorn
import inspect
import hashlib
import os

from config import get_settings
from routers import supabase as supabase_router
from schemas import (
    UserCreate,
    UserResponse,
    LabResultCreate,
    LabResultResponse,
    LabResultExtractFromTextRequest,
    RecommendationRequest,
    FeedbackCreate,
)
from services.recommender import RecommenderService
from services.deficit_calculator import DeficitCalculator
from services.explanation_generator import ExplanationGenerator
from services.auth import authenticate_user, create_user
from domain.models import UserProfile, FoodItem
from repositories import (
    UserRepository,
    FoodRepository,
    LabResultRepository,
    RecommendationRepository,
    FeedbackRepository,
)
from services.auth import request_magic_link, verify_magic_link
from middleware.auth import get_current_user

app = FastAPI(
    title="VitaBalance API",
    description="Sistem de recomandare cu explicații personalizate pentru deficiențe nutriționale",
    version="2.0.0",
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Asigură că orice excepție neprinsă returnează JSON cu detail, nu HTML."""
    from fastapi.responses import JSONResponse
    import traceback
    traceback.print_exc()
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return JSONResponse(
        status_code=500,
        content={"detail": f"Eroare server: {str(exc)}"},
    )


settings = get_settings()

# CORS foarte permisiv pentru a evita probleme între Vercel și backend.
# Pentru producție publică se poate restrânge la o listă fixă de origin-uri.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(supabase_router.router)


def _profile_to_response(p: UserProfile) -> dict:
    """Map UserProfile to API response shape."""
    return {
        "id": p.id,
        "email": p.email,
        "name": p.name,
        "age": p.age,
        "sex": p.sex,
        "weight": p.weight,
        "height": p.height,
        "activity_level": p.activity_level,
        "diet_type": p.diet_type,
        "allergies": p.allergies,
        "medical_conditions": p.medical_conditions,
        "created_at": p.created_at or None,
    }


# ---------- Public / health ----------
@app.get("/")
async def root():
    return {"message": "VitaBalance API - Sistem de recomandare nutrițională"}


@app.get("/health")
async def health_check(settings=Depends(get_settings)):
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "debug": settings.debug,
    }


@app.get("/debug/rule-engine")
async def debug_rule_engine():
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
    return {"app_name": settings.app_name, "debug": settings.debug}


# ---------- Auth (legacy password – will be replaced by magic link) ----------
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
    access_token: Optional[str] = None
    token_type: str = "bearer"


class MagicLinkRequest(BaseModel):
    email: EmailStr
    fullName: Optional[str] = None  # pentru înregistrare prin magic link


class MagicLinkVerifyRequest(BaseModel):
    token: str


class MagicLinkResponse(BaseModel):
    message: str


class VerifyMagicLinkResponse(BaseModel):
    email: str
    fullName: str
    bio: str
    access_token: str
    token_type: str = "bearer"


@app.post("/api/auth/request-magic-link", response_model=MagicLinkResponse)
async def api_request_magic_link(body: MagicLinkRequest, background_tasks: BackgroundTasks):
    """Trimite link magic pe email. Opțional fullName pentru înregistrare."""
    if not body.email or not str(body.email).strip():
        raise HTTPException(status_code=400, detail="Email obligatoriu")
    try:
        email = str(body.email).strip().lower()
        # Generăm tokenul imediat (rapid), iar trimiterea efectivă a emailului o facem în background
        # ca să nu blocăm UX-ul pentru apelul extern către providerul de email.
        from repositories.magic_link_repository import create_token
        from services.email_service import send_magic_link_email

        token = create_token(email, full_name=body.fullName)
        base = settings.frontend_base_url.rstrip("/")
        link_url = f"{base}/?token={token}"

        if not settings.resend_api_key and not settings.debug:
            raise RuntimeError(
                "Configurația de email lipsește pe server: RESEND_API_KEY nu este setată. "
                "Adaugă RESEND_API_KEY în environment-ul serviciului backend și redeployează aplicația."
            )

        def _safe_send():
            try:
                send_magic_link_email(email, link_url)
            except Exception as e:
                print("[VitaBalance] Eroare la trimitere magic link (background):", e)

        background_tasks.add_task(_safe_send)
        ok = True
    except RuntimeError as e:
        # Propagăm mesajul exact (de ex. lipsă RESEND_API_KEY sau eroare Resend)
        raise HTTPException(status_code=500, detail=str(e))
    if not ok:
        # Fallback generic, dacă pentru vreun motiv funcția întoarce False.
        raise HTTPException(
            status_code=500,
            detail="Nu am putut trimite emailul de autentificare. Încearcă din nou sau contactează administratorul.",
        )
    return MagicLinkResponse(message="Dacă acest email este valid, vei primi un link de autentificare în câteva minute.")


@app.post("/api/auth/verify-magic-link", response_model=VerifyMagicLinkResponse)
async def api_verify_magic_link(body: MagicLinkVerifyRequest):
    """Validează tokenul magic, invalidează tokenul, returnează user + JWT."""
    if not body.token or not body.token.strip():
        raise HTTPException(status_code=400, detail="Token obligatoriu")
    result = verify_magic_link(body.token.strip())
    if not result:
        raise HTTPException(status_code=401, detail="Link invalid, expirat sau deja folosit")
    return VerifyMagicLinkResponse(
        email=result["email"],
        fullName=result["fullName"],
        bio=result["bio"],
        access_token=result["access_token"],
        token_type=result.get("token_type", "bearer"),
    )


@app.get("/api/auth/me", response_model=AuthResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Returnează utilizatorul curent din JWT (pentru restabilire sesiune)."""
    from repositories import UserRepository
    repo = UserRepository()
    profile = repo.get_by_email(current_user["email"])
    full_name = (profile.full_name or profile.name or "") if profile else current_user.get("email", "")
    bio = (profile.bio or "") if profile else ""
    return AuthResponse(
        email=current_user["email"],
        fullName=full_name,
        bio=bio,
    )


def _ensure_user_resource(current_user: dict, user_id: int) -> UserProfile:
    """Verifică că resursa aparține utilizatorului autentificat. Returnează UserProfile."""
    repo = UserRepository()
    profile = repo.get_by_email(current_user["email"])
    if not profile:
        raise HTTPException(status_code=404, detail="Profilul nu a fost găsit")
    if profile.id != user_id:
        raise HTTPException(status_code=403, detail="Nu ai acces la această resursă")
    return profile


@app.get("/api/profile/by-email/{email}")
async def get_profile_by_email(email: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("email", "").lower() != email.lower():
        raise HTTPException(status_code=403, detail="Nu ai acces la acest profil")
    repo = UserRepository()
    user = repo.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="Profilul nu a fost găsit")
    return _profile_to_response(user)


@app.post("/api/auth/login", response_model=AuthResponse)
async def login(credentials: LoginRequest):
    user = authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Email sau parolă incorectă")
    from services.auth import create_access_token
    access_token = create_access_token({"sub": user["email"], "email": user["email"]})
    return AuthResponse(
        email=user["email"],
        fullName=user["fullName"],
        bio=user["bio"],
        access_token=access_token,
        token_type="bearer",
    )


@app.post("/api/auth/register", response_model=AuthResponse)
async def register(user_data: RegisterRequest):
    if not user_data.email or not user_data.email.strip():
        raise HTTPException(status_code=400, detail="Email-ul este obligatoriu")
    if not user_data.fullName or not user_data.fullName.strip():
        raise HTTPException(status_code=400, detail="Numele complet este obligatoriu")
    if not user_data.password:
        raise HTTPException(status_code=400, detail="Parola este obligatorie")
    password_stripped = user_data.password.strip()
    if len(password_stripped) == 0:
        raise HTTPException(status_code=400, detail="Parola nu poate conține doar spații")
    if len(password_stripped) < 6:
        raise HTTPException(status_code=400, detail="Parola trebuie să aibă minim 6 caractere")
    try:
        new_user = create_user(
            email=user_data.email.strip(),
            password=user_data.password,
            fullName=user_data.fullName.strip(),
            bio=user_data.bio.strip() if user_data.bio else None,
        )
        from services.auth import create_access_token
        access_token = create_access_token({"sub": new_user["email"], "email": new_user["email"]})
        # Asigură că toate câmpurile sunt string (niciodată None) pentru AuthResponse
        return AuthResponse(
            email=new_user.get("email") or user_data.email,
            fullName=new_user.get("fullName") or user_data.fullName,
            bio=new_user.get("bio") or "",
            access_token=access_token,
            token_type="bearer",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        err_msg = str(e)
        raise HTTPException(status_code=500, detail=f"Eroare la crearea contului: {err_msg}")


# ---------- Profile (Supabase) – protejat ----------
@app.post("/api/profile", response_model=UserResponse)
async def create_profile(user: UserCreate, current_user: dict = Depends(get_current_user)):
    if current_user.get("email", "").lower() != user.email.lower():
        raise HTTPException(status_code=403, detail="Poți actualiza doar propriul profil")
    try:
        repo = UserRepository()
        rec_repo = RecommendationRepository()
        existing = repo.get_by_email(user.email)
        allergies_val = user.allergies or ""
        medical_val = user.medical_conditions or ""
        if existing:
            # Dacă se schimbă oricare dintre datele care influențează recomandările,
            # invalidăm recomandările curente ca să fie regenerate pe noile valori.
            old_snapshot = {
                "age": existing.age,
                "sex": existing.sex,
                "weight": existing.weight,
                "height": existing.height,
                "activity_level": existing.activity_level,
                "diet_type": existing.diet_type,
                "allergies": existing.allergies or "",
                "medical_conditions": existing.medical_conditions or "",
            }
            new_snapshot = {
                "age": user.age,
                "sex": user.sex,
                "weight": user.weight,
                "height": user.height,
                "activity_level": user.activity_level,
                "diet_type": user.diet_type,
                "allergies": allergies_val,
                "medical_conditions": medical_val,
            }
            if old_snapshot != new_snapshot:
                rec_repo.delete_by_user_id(existing.id)
            updated = repo.upsert(
                user.email,
                name=user.name,
                age=user.age,
                sex=user.sex,
                weight=user.weight,
                height=user.height,
                activity_level=user.activity_level,
                diet_type=user.diet_type,
                allergies=allergies_val,
                medical_conditions=medical_val,
                user_id=existing.id,
            )
        else:
            updated = repo.upsert(
                user.email,
                name=user.name,
                age=user.age,
                sex=user.sex,
                weight=user.weight,
                height=user.height,
                activity_level=user.activity_level,
                diet_type=user.diet_type,
                allergies=allergies_val,
                medical_conditions=medical_val,
            )
        return _profile_to_response(updated)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Eroare la salvarea profilului: {str(e)}")


@app.get("/api/profile/{user_id}", response_model=UserResponse)
async def get_profile(user_id: int, current_user: dict = Depends(get_current_user)):
    _ensure_user_resource(current_user, user_id)
    repo = UserRepository()
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilizatorul nu a fost găsit")
    return _profile_to_response(user)


# ---------- Lab results (Supabase) – protejat ----------
@app.post("/api/lab-results", response_model=LabResultResponse)
async def create_lab_results(lab_result: LabResultCreate, current_user: dict = Depends(get_current_user)):
    _ensure_user_resource(current_user, lab_result.user_id)
    repo = LabResultRepository()
    data = lab_result.model_dump(exclude={"user_id"})
    created = repo.create(lab_result.user_id, data)
    return LabResultResponse(
        id=created.id,
        user_id=created.user_id,
        hemoglobin=created.hemoglobin,
        ferritin=created.ferritin,
        vitamin_d=created.vitamin_d,
        vitamin_b12=created.vitamin_b12,
        calcium=created.calcium,
        magnesium=created.magnesium,
        zinc=created.zinc,
        protein=created.protein,
        folate=created.folate,
        vitamin_a=created.vitamin_a,
        iodine=created.iodine,
        vitamin_k=created.vitamin_k,
        potassium=created.potassium,
        notes=created.notes,
        created_at=created.created_at,
    )


@app.get("/api/lab-results/{user_id}", response_model=List[LabResultResponse])
async def get_lab_results(user_id: int, current_user: dict = Depends(get_current_user)):
    _ensure_user_resource(current_user, user_id)
    repo = LabResultRepository()
    items = repo.get_all_by_user_id(user_id)
    return [
        LabResultResponse(
            id=x.id,
            user_id=x.user_id,
            hemoglobin=x.hemoglobin,
            ferritin=x.ferritin,
            vitamin_d=x.vitamin_d,
            vitamin_b12=x.vitamin_b12,
            calcium=x.calcium,
            magnesium=x.magnesium,
            zinc=x.zinc,
            protein=x.protein,
            folate=x.folate,
            vitamin_a=x.vitamin_a,
            iodine=x.iodine,
            vitamin_k=x.vitamin_k,
            potassium=x.potassium,
            notes=x.notes,
            created_at=x.created_at,
        )
        for x in items
    ]


@app.post("/api/lab-results/extract-from-text")
async def extract_lab_values_from_text(
    body: LabResultExtractFromTextRequest,
    current_user: dict = Depends(get_current_user),
):
    """Extrage valorile analizelor medicale din textul unui raport (ex. din PDF)."""
    from services.lab_text_extractor import extract_lab_values_from_text
    extracted = extract_lab_values_from_text(body.text)
    return extracted


# ---------- Recommendations (Supabase) – protejat ----------
@app.post("/api/recommendations")
async def get_recommendations(
    request: RecommendationRequest,
    force_regenerate: bool = Query(False, description="Forțează regenerarea recomandărilor"),
    current_user: dict = Depends(get_current_user),
):
    _ensure_user_resource(current_user, request.user_id)
    user_repo = UserRepository()
    food_repo = FoodRepository()
    lab_repo = LabResultRepository()
    rec_repo = RecommendationRepository()
    feedback_repo = FeedbackRepository()

    user = user_repo.get_by_id(request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilizatorul nu a fost găsit")

    foods = food_repo.get_all()
    if not foods:
        # Dacă nu există alimente în baza de date, întoarcem o listă goală.
        # Frontend-ul va afișa un mesaj prietenos, în loc de eroare 404.
        return []

    lab_results = lab_repo.get_latest_by_user_id(request.user_id)
    user_feedbacks = feedback_repo.get_by_user_id(request.user_id)
    feedback_counts_by_food = feedback_repo.get_counts_by_food_id()
    user_feedback_by_rec = {fb.recommendation_id: fb.rating for fb in user_feedbacks if fb.recommendation_id is not None}

    feedback_by_food: dict = {}
    for fb in user_feedbacks:
        if fb.recommendation_id is None:
            continue
        recs = rec_repo.get_by_user_id(request.user_id, limit=1000)
        for r in recs:
            if r.id == fb.recommendation_id:
                if r.food_id not in feedback_by_food:
                    feedback_by_food[r.food_id] = []
                feedback_by_food[r.food_id].append(fb)
                break

    existing = rec_repo.get_first_by_user_id(request.user_id)
    should_generate = force_regenerate or (existing is None)

    def _to_dt(v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            s = v.replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(s)
            except Exception:
                return None
        return None

    # Dacă user-ul și-a actualizat analizele după ce s-au generat recomandările,
    # regenerează automat ca să reflecte valorile medicale curente.
    if not force_regenerate and existing is not None and lab_results is not None:
        rec_dt = _to_dt(getattr(existing, "created_at", None))
        lab_dt = _to_dt(getattr(lab_results, "created_at", None))
        if lab_dt and (rec_dt is None or lab_dt > rec_dt):
            should_generate = True

    # Înlocuire unei recomandări (după dislike + "Da, schimb-o")
    exclude_ids = set(request.exclude_food_ids or [])
    is_replace_only = False
    if request.replace_recommendation_id:
        rec_to_replace = next(
            (r for r in rec_repo.get_by_user_id(request.user_id, limit=100) if r.id == request.replace_recommendation_id),
            None
        )
        if rec_to_replace:
            exclude_ids.add(rec_to_replace.food_id)
            rec_repo.delete_by_id(request.replace_recommendation_id)
            is_replace_only = True

    # La înlocuire punctuală („Nu prea” + „Da, schimb-o”), evită să recomandăm
    # din nou un aliment care este deja în lista de recomandări a utilizatorului.
    # Astfel prevenim duplicatele de tip „același preparat de mai multe ori”.
    if is_replace_only:
        existing_recs_for_user = rec_repo.get_by_user_id(request.user_id, limit=100)
        for r in existing_recs_for_user:
            exclude_ids.add(r.food_id)

    # Dacă trebuie să regenerăm recomandările (profil/analize noi) și nu suntem într-un scenariu
    # de înlocuire punctuală, ștergem toate recomandările vechi pentru a evita duplicatele.
    if should_generate and existing is not None and not is_replace_only:
        rec_repo.delete_by_user_id(request.user_id)

    foods_filtered = [f for f in foods if f.id not in exclude_ids] if exclude_ids else foods

    calculator = DeficitCalculator()
    deficits = calculator.calculate_deficits(user, lab_results)

    recommendations: List[dict] = []
    if is_replace_only:
        recommender = RecommenderService()
        rec_list = recommender.generate_recommendations(
            user=user,
            deficits=deficits,
            foods=foods_filtered,
            lab_results=lab_results,
            user_feedbacks=user_feedbacks,
            feedback_by_food=feedback_by_food,
        )
        if rec_list:
            food = next((f for f in foods_filtered if f.id == rec_list[0]["food_id"]), None)
            if food:
                explanation_gen = ExplanationGenerator()
                expl = explanation_gen.generate_explanation(
                    food=food,
                    user=user,
                    deficits=deficits,
                    score=rec_list[0]["score"],
                    coverage=rec_list[0]["coverage"],
                    explanations=rec_list[0].get("explanations"),
                    matched_rules=rec_list[0].get("matched_rules"),
                )
                rec_repo.insert_many([{
                    "user_id": user.id,
                    "food_id": food.id,
                    "score": rec_list[0]["score"],
                    "explanation": expl["text"],
                    "portion_suggested": expl["portion"],
                    "coverage_percentage": rec_list[0]["coverage"],
                }])
        # Reîncarcă counts după insert (noua rec nu e încă în counts)
        feedback_counts_by_food = feedback_repo.get_counts_by_food_id()
        existing_recs = rec_repo.get_by_user_id(request.user_id, limit=20)
        food_by_id = {f.id: f for f in foods}
        explanation_gen = ExplanationGenerator()
        for rec in existing_recs:
            food = food_by_id.get(rec.food_id)
            if not food:
                continue
            expl = explanation_gen.generate_explanation(
                food=food,
                user=user,
                deficits=deficits,
                score=rec.score,
                coverage=rec.coverage_percentage or 0,
                explanations=[rec.explanation] if rec.explanation else None,
                matched_rules=[],
            )
            counts = feedback_counts_by_food.get(rec.food_id, {"likes": 0, "dislikes": 0})
            recommendations.append({
                "food_id": food.id,
                "food": {"id": food.id, "name": food.name, "category": food.category, "image_url": food.image_url},
                "score": rec.score,
                "coverage": rec.coverage_percentage or 0,
                "explanation": expl,
                "recommendation_id": rec.id,
                "feedback": counts,
                "my_rating": user_feedback_by_rec.get(rec.id),
            })
    elif should_generate:
        recommender = RecommenderService()
        rec_list = recommender.generate_recommendations(
            user=user,
            deficits=deficits,
            foods=foods_filtered,
            lab_results=lab_results,
            user_feedbacks=user_feedbacks,
            feedback_by_food=feedback_by_food,
        )
        explanation_gen = ExplanationGenerator()
        to_insert = []
        # Persistăm până la 20 de recomandări, sortate deja descrescător după coverage/score.
        for rec in rec_list[:20]:
            food = next((f for f in foods if f.id == rec["food_id"]), None)
            if not food:
                continue
            explanation = explanation_gen.generate_explanation(
                food=food,
                user=user,
                deficits=deficits,
                score=rec["score"],
                coverage=rec["coverage"],
                explanations=rec.get("explanations"),
                matched_rules=rec.get("matched_rules"),
            )
            to_insert.append({
                "user_id": user.id,
                "food_id": food.id,
                "score": rec["score"],
                "explanation": explanation["text"],
                "portion_suggested": explanation["portion"],
                "coverage_percentage": rec["coverage"],
            })
        if to_insert:
            inserted = rec_repo.insert_many(to_insert)
            food_by_id = {f.id: f for f in foods}
            # Asigurăm același ranking ca `rec_list` pe primele N poziții.
            for i, rec in enumerate(inserted):
                if i >= len(rec_list):
                    break
                food = food_by_id.get(rec.food_id)
                if not food:
                    continue
                orig = rec_list[i]
                expl = explanation_gen.generate_explanation(
                    food=food,
                    user=user,
                    deficits=deficits,
                    score=orig["score"],
                    coverage=orig["coverage"],
                    explanations=orig.get("explanations"),
                    matched_rules=orig.get("matched_rules"),
                )
                counts = feedback_counts_by_food.get(rec.food_id, {"likes": 0, "dislikes": 0})
                recommendations.append({
                    "food_id": food.id,
                    "food": {"id": food.id, "name": food.name, "category": food.category, "image_url": food.image_url},
                    "score": rec.score,
                    "coverage": rec.coverage_percentage or 0,
                    "explanation": expl,
                    "recommendation_id": rec.id,
                    "feedback": counts,
                    "my_rating": user_feedback_by_rec.get(rec.id),
                })
    else:
        existing_recs = rec_repo.get_by_user_id(request.user_id, limit=20)
        food_by_id = {f.id: f for f in foods}
        explanation_gen = ExplanationGenerator()
        for rec in existing_recs:
            food = food_by_id.get(rec.food_id)
            if not food:
                continue
            expl = explanation_gen.generate_explanation(
                food=food,
                user=user,
                deficits=deficits,
                score=rec.score,
                coverage=rec.coverage_percentage or 0,
                explanations=[rec.explanation] if rec.explanation else None,
                matched_rules=[],
            )
            counts = feedback_counts_by_food.get(rec.food_id, {"likes": 0, "dislikes": 0})
            recommendations.append({
                "food_id": food.id,
                "food": {"id": food.id, "name": food.name, "category": food.category, "image_url": food.image_url},
                "score": rec.score,
                "coverage": rec.coverage_percentage or 0,
                "explanation": expl,
                "recommendation_id": rec.id,
                "feedback": counts,
                "my_rating": user_feedback_by_rec.get(rec.id),
            })

    if not recommendations and should_generate:
        recommender = RecommenderService()
        rec_list = recommender.generate_recommendations(
            user=user,
            deficits={},
            foods=foods,
            lab_results=lab_results,
            user_feedbacks=user_feedbacks,
            feedback_by_food=feedback_by_food,
        )
        if not rec_list:
            # Nu s-au găsit alimente compatibile – întoarcem listă goală, nu 404.
            return []
        explanation_gen = ExplanationGenerator()
        to_insert = []
        # Persistăm până la 20 de recomandări fallback.
        for rec in rec_list[:20]:
            food = next((f for f in foods if f.id == rec["food_id"]), None)
            if not food:
                continue
            explanation = explanation_gen.generate_explanation(
                food=food,
                user=user,
                deficits=deficits,
                score=rec["score"],
                coverage=rec["coverage"],
                explanations=rec.get("explanations"),
                matched_rules=rec.get("matched_rules"),
            )
            to_insert.append({
                "user_id": user.id,
                "food_id": food.id,
                "score": rec["score"],
                "explanation": explanation["text"],
                "portion_suggested": explanation["portion"],
                "coverage_percentage": rec["coverage"],
            })
        inserted = rec_repo.insert_many(to_insert)
        food_by_id = {f.id: f for f in foods}
        for i, rec in enumerate(inserted):
            if i >= len(rec_list):
                break
            food = food_by_id.get(rec.food_id)
            if not food:
                continue
            orig = rec_list[i]
            expl = explanation_gen.generate_explanation(
                food=food,
                user=user,
                deficits=deficits,
                score=orig["score"],
                coverage=orig["coverage"],
                explanations=orig.get("explanations"),
                matched_rules=orig.get("matched_rules"),
            )
            counts = feedback_counts_by_food.get(rec.food_id, {"likes": 0, "dislikes": 0})
            recommendations.append({
                "food_id": food.id,
                "food": {"id": food.id, "name": food.name, "category": food.category, "image_url": food.image_url},
                "score": rec.score,
                "coverage": rec.coverage_percentage or 0,
                "explanation": expl,
                "recommendation_id": rec.id,
                "feedback": counts,
                "my_rating": user_feedback_by_rec.get(rec.id),
            })
    # Elimină orice duplicate pe baza food_id (ex. aceeași mâncare inserată de mai multe ori
    # în urma unor regenerări sau înlocuiri anterioare), păstrând doar prima apariție
    # în ordinea deja sortată (coverage/score).
    unique_recommendations: List[dict] = []
    seen_food_ids: set[int] = set()
    for rec in recommendations:
        fid = rec.get("food_id")
        if fid is None:
            unique_recommendations.append(rec)
            continue
        if fid in seen_food_ids:
            continue
        seen_food_ids.add(fid)
        unique_recommendations.append(rec)

    return unique_recommendations


@app.delete("/api/recommendations/{user_id}")
async def delete_recommendations(user_id: int, current_user: dict = Depends(get_current_user)):
    _ensure_user_resource(current_user, user_id)
    rec_repo = RecommendationRepository()
    rec_repo.delete_by_user_id(user_id)
    return {"message": "Recomandări șterse"}


# ---------- Feedback (Supabase) – protejat ----------
@app.post("/api/feedback")
async def create_feedback(feedback: FeedbackCreate, current_user: dict = Depends(get_current_user)):
    _ensure_user_resource(current_user, feedback.user_id)
    if feedback.rating < -1 or feedback.rating > 5:
        raise HTTPException(status_code=400, detail="Rating trebuie să fie între -1 și 5")
    if not feedback.recommendation_id:
        raise HTTPException(status_code=400, detail="recommendation_id este obligatoriu")
    repo = FeedbackRepository()
    result = repo.upsert(
        feedback.user_id,
        feedback.recommendation_id,
        feedback.rating,
        comment=feedback.comment,
        tried=feedback.tried,
        worked=feedback.worked,
    )
    return {"message": "Feedback salvat cu succes", "id": result.id}


# ---------- Foods (Supabase) – protejat (catalog public dar API consistent) ----------
@app.get("/api/foods")
async def get_foods(current_user: dict = Depends(get_current_user)):
    repo = FoodRepository()
    items = repo.get_all()
    return [
        {
            "id": f.id,
            "name": f.name,
            "category": f.category,
            "iron": f.iron,
            "calcium": f.calcium,
            "vitamin_d": f.vitamin_d,
            "vitamin_b12": f.vitamin_b12,
            "magnesium": f.magnesium,
            "protein": f.protein,
            "zinc": f.zinc,
            "vitamin_c": f.vitamin_c,
            "fiber": f.fiber,
            "calories": f.calories,
            "folate": f.folate,
            "vitamin_a": f.vitamin_a,
            "iodine": f.iodine,
            "vitamin_k": f.vitamin_k,
            "potassium": f.potassium,
            "carbs": f.carbs,
            "fat": f.fat,
            "free_sugar": f.free_sugar,
            "cholesterol": f.cholesterol,
            "allergens": f.allergens,
            "image_url": f.image_url,
            "created_at": f.created_at,
        }
        for f in items
    ]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
