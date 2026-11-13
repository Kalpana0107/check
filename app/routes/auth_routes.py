from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import datetime

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserLogin, UserOut, Token
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=Token)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists"
        )
    
    role = user_in.role.lower() if user_in.role.lower() in ["teacher", "student"] else "student"
    new_user = User(
        email=user_in.email,
        password_hash=hash_password(user_in.password),
        full_name=user_in.full_name,
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.email, "role": new_user.role, "id": new_user.id})
    return Token(access_token=token, token_type="bearer", user=UserOut.model_validate(new_user))

@router.post("/login", response_model=Token)
def login(creds: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == creds.email).first()
    if not user or not verify_password(creds.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    token = create_access_token({"sub": user.email, "role": user.role, "id": user.id})
    return Token(access_token=token, token_type="bearer", user=UserOut.model_validate(user))

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    token = create_access_token({"sub": user.email, "role": user.role, "id": user.id})
    return Token(access_token=token, token_type="bearer", user=UserOut.model_validate(user))

@router.post("/demo-login/{role}", response_model=Token)
def demo_login(role: str, db: Session = Depends(get_db)):
    role = role.lower()
    if role not in ["teacher", "student"]:
        role = "student"
    
    user = db.query(User).filter(User.role == role).first()
    if not user:
        # Create default demo user if not present
        if role == "teacher":
            user = User(
                email="teacher@autograde.ai",
                password_hash=hash_password("demo123"),
                full_name="Prof. Sarah Jenkins",
                role="teacher"
            )
        else:
            user = User(
                email="alex@student.edu",
                password_hash=hash_password("demo123"),
                full_name="Alex Chen",
                role="student"
            )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": user.email, "role": user.role, "id": user.id})
    return Token(access_token=token, token_type="bearer", user=UserOut.model_validate(user))

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/system-status")
def system_status():
    has_api_key = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())
    masked_key = f"{settings.GEMINI_API_KEY[:6]}...{settings.GEMINI_API_KEY[-4:]}" if has_api_key and len(settings.GEMINI_API_KEY) > 10 else ("Configured" if has_api_key else "Not set (Using Intelligent Simulation Fallback)")
    return {
        "status": "online",
        "gemini_api_configured": has_api_key,
        "gemini_model": settings.GEMINI_MODEL,
        "api_key_preview": masked_key,
        "server_time": datetime.datetime.utcnow().isoformat()
    }

