from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Form, Request, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from pathlib import Path
import secrets

from app.database import get_db
from app.models import User, WorkoutPlan
from app.schemas import UserInput, FeedbackRequest
from app.ai_service import generate_workout, generate_tip, update_workout
from app.config import ADMIN_USERNAME, ADMIN_PASSWORD, GOOGLE_API_KEY

router = APIRouter()
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
security = HTTPBasic()

def template(request: Request, name: str, **context):
    return templates.TemplateResponse(request=request, name=name, context=context)

def check_admin(credentials: HTTPBasicCredentials = Depends(security)):
    username_ok = secrets.compare_digest(credentials.username.encode(), ADMIN_USERNAME.encode())
    password_ok = secrets.compare_digest(credentials.password.encode(), ADMIN_PASSWORD.encode())
    if not (username_ok and password_ok):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials", headers={"WWW-Authenticate": "Basic"})
    return credentials.username

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return template(request, "index.html", demo_mode=not bool(GOOGLE_API_KEY))

@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout_route(
    request: Request,
    username: str = Form(...),
    user_id: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        data = UserInput(username=username.strip(), user_id=user_id.strip(), age=age, weight=weight, goal=goal, intensity=intensity)
    except Exception as exc:
        return template(request, "index.html", error=str(exc), demo_mode=not bool(GOOGLE_API_KEY))
    user = db.scalar(select(User).where(User.user_id == data.user_id))
    if user:
        user.username, user.age, user.weight, user.goal, user.intensity = data.username, data.age, data.weight, data.goal, data.intensity
    else:
        user = User(user_id=data.user_id, username=data.username, age=data.age, weight=data.weight, goal=data.goal, intensity=data.intensity)
        db.add(user)
    db.flush()
    plan_text, demo_plan = generate_workout(data.username, data.age, data.weight, data.goal, data.intensity)
    tip, demo_tip = generate_tip(data.goal)
    plan = WorkoutPlan(user_pk=user.id, original_plan=plan_text, nutrition_tip=tip)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return template(request, "result.html", user=user, plan=plan, workout_plan=plan_text, nutrition_tip=tip,
                    is_updated=False, demo_mode=demo_plan or demo_tip, message=None)

@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback(request: Request, user_id: str = Form(...), feedback: str = Form(...), plan_id: int = Form(...), db: Session = Depends(get_db)):
    try:
        data = FeedbackRequest(user_id=user_id.strip(), feedback=feedback.strip())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    plan = db.scalar(select(WorkoutPlan).options(joinedload(WorkoutPlan.user)).where(WorkoutPlan.id == plan_id))
    if not plan or plan.user.user_id != data.user_id:
        raise HTTPException(status_code=404, detail="Plan or user ID not found.")
    revised, demo_plan = update_workout(plan.original_plan, data.feedback, plan.user.goal, plan.user.intensity)
    tip, demo_tip = generate_tip(plan.user.goal)
    plan.updated_plan = revised
    plan.latest_feedback = data.feedback
    plan.nutrition_tip = tip
    plan.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(plan)
    return template(request, "result.html", user=plan.user, plan=plan, workout_plan=revised, nutrition_tip=tip,
                    is_updated=True, demo_mode=demo_plan or demo_tip, message="Your plan has been updated and saved.")

@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(request: Request, _admin: str = Depends(check_admin), db: Session = Depends(get_db)):
    users = db.scalars(select(User).options(joinedload(User.plans)).order_by(User.created_at.desc())).unique().all()
    return template(request, "all_users.html", users=users)

@router.get("/api/users")
def api_users(_admin: str = Depends(check_admin), db: Session = Depends(get_db)):
    users = db.scalars(select(User).options(joinedload(User.plans)).order_by(User.id)).unique().all()
    return [{"user_id": u.user_id, "username": u.username, "age": u.age, "weight": u.weight, "goal": u.goal,
             "intensity": u.intensity, "plans": [{"id": p.id, "original_plan": p.original_plan, "updated_plan": p.updated_plan,
             "nutrition_tip": p.nutrition_tip, "latest_feedback": p.latest_feedback} for p in u.plans]} for u in users]

@router.post("/api/generate-workout")
def api_generate_workout(payload: UserInput, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.user_id == payload.user_id))
    if not user:
        user = User(**payload.model_dump())
        db.add(user)
    else:
        for key, value in payload.model_dump().items():
            setattr(user, key, value)
    db.flush()
    workout, demo_plan = generate_workout(payload.username, payload.age, payload.weight, payload.goal, payload.intensity)
    tip, demo_tip = generate_tip(payload.goal)
    plan = WorkoutPlan(user_pk=user.id, original_plan=workout, nutrition_tip=tip)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return {"user_id": user.user_id, "plan_id": plan.id, "workout_plan": workout, "nutrition_tip": tip, "demo_mode": demo_plan or demo_tip}

@router.post("/api/submit-feedback")
def api_submit_feedback(payload: FeedbackRequest, plan_id: int, db: Session = Depends(get_db)):
    plan = db.scalar(select(WorkoutPlan).options(joinedload(WorkoutPlan.user)).where(WorkoutPlan.id == plan_id))
    if not plan or plan.user.user_id != payload.user_id:
        raise HTTPException(status_code=404, detail="Plan or user ID not found.")
    revised, demo_plan = update_workout(plan.original_plan, payload.feedback, plan.user.goal, plan.user.intensity)
    tip, demo_tip = generate_tip(plan.user.goal)
    plan.updated_plan, plan.latest_feedback, plan.nutrition_tip = revised, payload.feedback, tip
    plan.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"user_id": payload.user_id, "plan_id": plan.id, "updated_plan": revised, "nutrition_tip": tip, "demo_mode": demo_plan or demo_tip}
