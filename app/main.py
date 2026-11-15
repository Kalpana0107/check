from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routes import auth_routes, exam_routes, submission_routes, analytics_routes

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Online Exam Checking and Student Conceptual Analytics Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

try:
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    (STATIC_DIR / "uploads").mkdir(parents=True, exist_ok=True)
except Exception:
    pass

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include API Routers
app.include_router(auth_routes.router)
app.include_router(exam_routes.router)
app.include_router(submission_routes.router)
app.include_router(analytics_routes.router)

# Frontend Page Routes
@app.get("/")
def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/teacher")
def teacher_page(request: Request):
    return templates.TemplateResponse("teacher.html", {"request": request})

@app.get("/student")
def student_page(request: Request):
    return templates.TemplateResponse("student.html", {"request": request})

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "gemini_ready": bool(settings.GEMINI_API_KEY)
    }

# Vercel ASGI handler
handler = app

