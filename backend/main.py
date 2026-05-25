"""API FastAPI VitaBalance."""
from fastapi import BackgroundTasks, FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from datetime import datetime
import uvicorn
import inspect
import hashlib
import os

from config import get_settings
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
from services.auth import authenticate_user, create_user
from domain.models import UserProfile
from repositories import (
    UserRepository,
    FoodRepository,
    LabResultRepository,
    RecommendationRepository,
    FeedbackRepository,
)
from services.auth import verify_magic_link
from middleware.auth import get_current_user
from middleware.rate_limit import RateLimitMiddleware
from services.recommendation_materialize import materialize_recommendations

app = FastAPI(
    title="VitaBalance API",
    description="Sistem de recomandare cu explicații personalizate pentru deficiențe nutriționale",
    version="2.0.0",
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    from fastapi.responses import JSONResponse
    import traceback

    traceback.print_exc()
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    cfg = get_settings()
    detail = (
        f"Eroare server: {str(exc)}"
        if cfg.debug
        else "Eroare la procesare. Încearcă din nou; dacă persistă, contactează suportul."
    )
    return JSONResponse(status_code=500, content={"detail": detail})


try:
    settings = get_settings()
except Exception as exc:  # noqa: BLE001
    import sys

    sys.stderr.write(f"\n[FATAL] Config: {type(exc).__name__}: {exc}\n")
    raise

_cors_origins = ["*"] if settings.cors_allow_all else settings.get_cors_origins_list()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    RateLimitMiddleware,
    enabled=settings.rate_limit_enabled,
    auth_max_per_window=settings.rate_limit_auth_per_min,
    recommendations_max_per_window=settings.rate_limit_recommendations_per_min,
)


def _profile_to_response(p: UserProfile) -> dict:
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
        "updated_at": getattr(p, "updated_at", None),
    }


@app.get("/")
async def root():
    return {"message": "VitaBalance API - Sistem de recomandare nutrițională"}


@app.get("/health")
async def health_check(settings=Depends(get_settings)):
    checks: Dict[str, str] = {"app": "ok"}
    checks["supabase"] = "skipped"
    if settings.supabase_url and settings.effective_supabase_secret_key():
        try:
            from supabase_client import get_supabase_client

            client = get_supabase_client()
            client.table("users").select("id").limit(1).execute()
            checks["supabase"] = "ok"
        except Exception as exc:  # noqa: BLE001
            checks["supabase"] = "error"
            if settings.debug:
                checks["supabase_detail"] = str(exc)[:200]
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "debug": settings.debug,
        "checks": checks,
    }


if settings.debug:

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


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    fullName: str


class AuthResponse(BaseModel):
    email: str
    fullName: str
    access_token: Optional[str] = None
    token_type: str = "bearer"


class MagicLinkRequest(BaseModel):
    email: EmailStr
    fullName: Optional[str] = None


class MagicLinkVerifyRequest(BaseModel):
    token: str


class MagicLinkResponse(BaseModel):
    message: str


class VerifyMagicLinkResponse(BaseModel):
    email: str
    fullName: str
    access_token: str
    token_type: str = "bearer"


class RecommendationAuditResponse(BaseModel):
    user_id: int
    has_lab_data: bool
    active_deficits: Dict[str, float]
    recommendation_count: int
    top_recommendation_food_ids: List[int]
    top_recommendation_names: List[str]
    covered_deficit_nutrients: List[str]
    missing_deficit_nutrients: List[str]
    warnings: List[str]


@app.post("/api/auth/request-magic-link", response_model=MagicLinkResponse)
async def api_request_magic_link(body: MagicLinkRequest, background_tasks: BackgroundTasks):
    if not body.email or not str(body.email).strip():
        raise HTTPException(status_code=400, detail="Email obligatoriu")
    ok = False
    try:
        email = str(body.email).strip().lower()
        from repositories.magic_link_repository import create_token
        from services.email_service import send_magic_link_email

        token = create_token(email)
        base = settings.frontend_base_url.rstrip("/")
        link_url = f"{base}/?token={token}"

        if not settings.resend_api_key and not settings.debug:
            raise RuntimeError(
                "Configurația de email lipsește pe server: RESEND_API_KEY nu este setată. "
                "Adaugă RESEND_API_KEY în environment-ul serviciului backend și redeployează aplicația."
            )

        def _safe_send():
            import logging

            try:
                send_magic_link_email(email, link_url)
            except Exception:
                logging.getLogger(__name__).exception("Eroare la trimitere magic link (background)")

        background_tasks.add_task(_safe_send)
        ok = True
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    if not ok:
        raise HTTPException(
            status_code=500,
            detail="Nu am putut trimite emailul de autentificare. Încearcă din nou sau contactează administratorul.",
        )
    return MagicLinkResponse(message="Dacă acest email este valid, vei primi un link de autentificare în câteva minute.")


@app.post("/api/auth/verify-magic-link", response_model=VerifyMagicLinkResponse)
async def api_verify_magic_link(body: MagicLinkVerifyRequest):
    if not body.token or not body.token.strip():
        raise HTTPException(status_code=400, detail="Token obligatoriu")
    result = verify_magic_link(body.token.strip())
    if not result:
        raise HTTPException(status_code=401, detail="Link invalid, expirat sau deja folosit")
    return VerifyMagicLinkResponse(
        email=result["email"],
        fullName=result["fullName"],
        access_token=result["access_token"],
        token_type=result.get("token_type", "bearer"),
    )


@app.get("/api/auth/me", response_model=AuthResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    from repositories import UserRepository
    repo = UserRepository()
    profile = repo.get_by_email(current_user["email"])
    full_name = profile.name if profile else current_user.get("email", "")
    return AuthResponse(
        email=current_user["email"],
        fullName=full_name,
    )


def _ensure_user_resource(current_user: dict, user_id: int) -> UserProfile:
    repo = UserRepository()
    profile = repo.get_by_email(current_user["email"])
    if not profile:
        raise HTTPException(status_code=404, detail="Profilul nu a fost găsit")
    if profile.id != user_id:
        raise HTTPException(status_code=403, detail="Nu ai acces la această resursă")
    return profile


def _stored_recommendations_payload(
    user_id: int,
    _rec_repo: RecommendationRepository,
    _food_repo: FoodRepository,
    _feedback_repo: FeedbackRepository,
) -> List[dict]:
    from services.recommendation_materialize import list_stored_recommendations_fast

    return list_stored_recommendations_fast(user_id)


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
        )
        from services.auth import create_access_token
        access_token = create_access_token({"sub": new_user["email"], "email": new_user["email"]})
        return AuthResponse(
            email=new_user.get("email") or user_data.email,
            fullName=new_user.get("fullName") or user_data.fullName,
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


@app.post("/api/profile", response_model=UserResponse)
async def create_profile(user: UserCreate, current_user: dict = Depends(get_current_user)):
    if current_user.get("email", "").lower() != user.email.lower():
        raise HTTPException(status_code=403, detail="Poți actualiza doar propriul profil")
    try:
        repo = UserRepository()
        existing = repo.get_by_email(user.email)
        allergies_val = user.allergies or ""
        medical_val = user.medical_conditions or ""
        if existing:
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
            snapshot_changed = old_snapshot != new_snapshot
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
                bump_updated_at=snapshot_changed,
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
                bump_updated_at=True,
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


@app.post("/api/lab-results", response_model=LabResultResponse)
async def create_lab_results(lab_result: LabResultCreate, current_user: dict = Depends(get_current_user)):
    _ensure_user_resource(current_user, lab_result.user_id)
    repo = LabResultRepository()
    data = lab_result.model_dump(exclude={"user_id"})
    created = repo.upsert_for_user(lab_result.user_id, data)
    return LabResultResponse(
        id=created.id,
        user_id=created.user_id,
        user_email=created.user_email or "",
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
        vitamin_c=created.vitamin_c,
        iodine=created.iodine,
        vitamin_k=created.vitamin_k,
        potassium=created.potassium,
        notes=created.notes,
        created_at=created.created_at,
        updated_at=getattr(created, "updated_at", None) or created.created_at,
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
            user_email=x.user_email or "",
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
            vitamin_c=x.vitamin_c,
            iodine=x.iodine,
            vitamin_k=x.vitamin_k,
            potassium=x.potassium,
            notes=x.notes,
            created_at=x.created_at,
            updated_at=getattr(x, "updated_at", None) or x.created_at,
        )
        for x in items
    ]


@app.post("/api/lab-results/extract-from-text")
async def extract_lab_values_from_text(
    body: LabResultExtractFromTextRequest,
    current_user: dict = Depends(get_current_user),
):
    from services.lab_text_extractor import extract_lab_values_from_text
    extracted = extract_lab_values_from_text(body.text)
    return extracted


@app.get("/api/recommendations/stored/{user_id}")
async def list_stored_recommendations(user_id: int, current_user: dict = Depends(get_current_user)):
    _ensure_user_resource(current_user, user_id)
    rec_repo = RecommendationRepository()
    food_repo = FoodRepository()
    feedback_repo = FeedbackRepository()
    return _stored_recommendations_payload(user_id, rec_repo, food_repo, feedback_repo)


@app.post("/api/recommendations")
async def get_recommendations(
    request: RecommendationRequest,
    force_regenerate: bool = Query(False, description="Forțează regenerarea recomandărilor"),
    current_user: dict = Depends(get_current_user),
):
    _ensure_user_resource(current_user, request.user_id)
    if request.replace_recommendation_id is not None and request.replace_feedback_rating is not None:
        r = request.replace_feedback_rating
        if r < -1 or r > 5:
            raise HTTPException(status_code=400, detail="Rating de feedback invalid.")
        feedback_repo = FeedbackRepository()
        feedback_repo.upsert(
            request.user_id,
            request.replace_recommendation_id,
            r,
            food_id=None,
        )
    return materialize_recommendations(
        request.user_id,
        current_user["email"],
        force_regenerate,
        request.replace_recommendation_id,
        request.exclude_food_ids,
    )


@app.get("/api/recommendations/sync-meta/{user_id}")
async def recommendations_sync_meta(user_id: int, current_user: dict = Depends(get_current_user)):
    _ensure_user_resource(current_user, user_id)
    urepo = UserRepository()
    rrepo = RecommendationRepository()
    lrepo = LabResultRepository()
    u = urepo.get_by_id(user_id)
    first = rrepo.get_first_by_user_id(user_id)
    labs = lrepo.get_latest_by_user_id(user_id)

    def iso(v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v)

    def _parse_ts(v):
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

    labs_fresh_at = None
    if labs is not None:
        ca = _parse_ts(getattr(labs, "created_at", None))
        ua = _parse_ts(getattr(labs, "updated_at", None))
        candidates = [t for t in (ca, ua) if t is not None]
        if candidates:
            labs_fresh_at = max(candidates)

    refresh_status = getattr(u, "rec_refresh_status", None) or "idle" if u else "idle"
    refresh_error = getattr(u, "rec_refresh_error", None) if u else None
    refresh_at = iso(getattr(u, "rec_refresh_at", None)) if u else None

    return {
        "user_updated_at": iso(getattr(u, "updated_at", None)) if u else None,
        "latest_rec_created_at": iso(getattr(first, "created_at", None)) if first else None,
        "labs_fresh_at": iso(labs_fresh_at) if labs_fresh_at else None,
        "refresh_status": refresh_status,
        "refresh_error": refresh_error,
        "refresh_at": refresh_at,
    }


@app.post("/api/recommendations/refresh-async/{user_id}")
async def recommendations_refresh_async(
    user_id: int,
    background_tasks: BackgroundTasks,
    force_regenerate: bool = Query(False, description="Dacă true, forțează regenerarea ca la Încearcă din nou"),
    current_user: dict = Depends(get_current_user),
):
    _ensure_user_resource(current_user, user_id)
    rec_repo = RecommendationRepository()
    food_repo = FoodRepository()
    feedback_repo = FeedbackRepository()
    stale = _stored_recommendations_payload(user_id, rec_repo, food_repo, feedback_repo)

    owner_email = current_user["email"]
    user_repo = UserRepository()
    user_repo.set_rec_refresh_status(user_id, "pending", error=None)

    def _job():
        try:
            materialize_recommendations(
                user_id,
                owner_email,
                force_regenerate,
                None,
                None,
            )
            user_repo.set_rec_refresh_status(user_id, "done", error=None)
        except Exception as exc:
            import logging

            logging.getLogger(__name__).exception("refresh-async job failed user_id=%s", user_id)
            user_repo.set_rec_refresh_status(
                user_id,
                "failed",
                error=str(exc)[:500],
            )

    background_tasks.add_task(_job)
    return {"status": "accepted", "recommendations": stale, "refresh_status": "pending"}


@app.get("/api/recommendations/audit/{user_id}", response_model=RecommendationAuditResponse)
async def audit_recommendations_quality(
    user_id: int,
    top_n: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    _ensure_user_resource(current_user, user_id)
    user_repo = UserRepository()
    food_repo = FoodRepository()
    lab_repo = LabResultRepository()

    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilizatorul nu a fost găsit")

    foods = food_repo.get_all()
    if not foods:
        return RecommendationAuditResponse(
            user_id=user_id,
            has_lab_data=False,
            active_deficits={},
            recommendation_count=0,
            top_recommendation_food_ids=[],
            top_recommendation_names=[],
            covered_deficit_nutrients=[],
            missing_deficit_nutrients=[],
            warnings=["Nu există alimente în catalog."],
        )

    lab_results = lab_repo.get_latest_by_user_id(user_id)
    has_lab_data = False
    if lab_results is not None:
        for key in [
            "hemoglobin", "ferritin", "calcium", "vitamin_d", "vitamin_b12", "magnesium",
            "protein", "zinc", "folate", "vitamin_a", "vitamin_c", "iodine", "vitamin_k", "potassium"
        ]:
            if getattr(lab_results, key, None) is not None:
                has_lab_data = True
                break

    calculator = DeficitCalculator()
    deficits = calculator.calculate_deficits(user, lab_results)
    active_deficits = {k: float(v) for k, v in deficits.items() if v and v > 0}

    recommender = RecommenderService()
    rec_list = recommender.generate_recommendations(
        user=user,
        deficits=deficits,
        foods=foods,
        lab_results=lab_results,
        user_feedbacks=[],
        feedback_by_food={},
    )
    top = rec_list[:top_n]
    food_by_id = {f.id: f for f in foods}
    top_ids: List[int] = [int(x["food_id"]) for x in top if x.get("food_id") is not None]
    top_names: List[str] = [food_by_id[i].name for i in top_ids if i in food_by_id]

    covered = set()
    for item in top:
        for n in item.get("nutrients_covered", []) or []:
            if n in active_deficits:
                covered.add(n)
    missing = [n for n in active_deficits.keys() if n not in covered]

    warnings: List[str] = []
    if active_deficits and not top:
        warnings.append("Există deficite active, dar nu s-au generat recomandări.")
    if missing:
        warnings.append("Deficite active neacoperite în top: " + ", ".join(sorted(missing)))
    if "vitamin_b12" in active_deficits and (user.diet_type or "").strip().lower() == "vegan":
        b12_in_top = any("vitamin_b12" in (x.get("nutrients_covered") or []) for x in top)
        if not b12_in_top:
            warnings.append("Profil vegan cu deficit B12: topul nu include suficient suport pentru B12.")
    if "vitamin_d" in active_deficits:
        d_in_top = any("vitamin_d" in (x.get("nutrients_covered") or []) for x in top)
        if not d_in_top:
            warnings.append("Deficit vitamina D activ: topul nu include suficient suport pentru vitamina D.")

    return RecommendationAuditResponse(
        user_id=user_id,
        has_lab_data=has_lab_data,
        active_deficits=active_deficits,
        recommendation_count=len(top),
        top_recommendation_food_ids=top_ids,
        top_recommendation_names=top_names,
        covered_deficit_nutrients=sorted(list(covered)),
        missing_deficit_nutrients=sorted(missing),
        warnings=warnings,
    )


@app.delete("/api/recommendations/{user_id}")
async def delete_recommendations(user_id: int, current_user: dict = Depends(get_current_user)):
    _ensure_user_resource(current_user, user_id)
    rec_repo = RecommendationRepository()
    rec_repo.delete_by_user_id(user_id)
    return {"message": "Recomandări șterse"}


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
        food_id=getattr(feedback, "food_id", None),
    )
    return {"message": "Feedback salvat cu succes", "id": result.id}


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
            "created_at": f.created_at,
        }
        for f in items
    ]


if __name__ == "__main__":
    _port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=_port)
