import os
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import settings
from app.database import engine, Base
from app.routes import auth_routes, exam_routes, submission_routes, analytics_routes

# Create DB tables safely
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Database table initialization warning: {e}")

# If on Vercel and DB has no teacher yet, run seed
if bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME")):
    try:
        from seed_data import seed
        seed()
    except Exception as e:
        print(f"Auto-seed warning on Vercel: {e}")

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

# Include API Routers
app.include_router(auth_routes.router)
app.include_router(exam_routes.router)
app.include_router(submission_routes.router)
app.include_router(analytics_routes.router)

# Route for uploaded files (handles /tmp/uploads on Vercel and pre-bundled uploads)
@app.get("/static/uploads/{filename}")
async def get_uploaded_file(filename: str):
    tmp_path = settings.UPLOAD_DIR / filename
    if tmp_path.exists():
        return FileResponse(str(tmp_path))
    static_path = STATIC_DIR / "uploads" / filename
    if static_path.exists():
        return FileResponse(str(static_path))
    raise HTTPException(status_code=404, detail="File not found")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

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


