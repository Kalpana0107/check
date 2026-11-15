import os
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from app.config import settings
from app.database import engine, Base
from app.routes import auth_routes, exam_routes, submission_routes, analytics_routes

# Create DB tables safely
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Database table initialization warning: {e}")

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

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    error_trace = traceback.format_exc()
    print(f"[AutoGrade Error] Unhandled Exception: {error_trace}")
    return HTMLResponse(
        content=f"<html><body style='font-family:sans-serif;padding:2rem;'><h2>Application Error</h2><pre style='background:#f1f5f9;padding:1rem;border-radius:8px;'>{error_trace}</pre></body></html>",
        status_code=500
    )

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

try:
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    (STATIC_DIR / "uploads").mkdir(parents=True, exist_ok=True)
except Exception:
    pass

# Fallback: check CWD templates, CWD app templates if __file__ based resolution misses on serverless
if not TEMPLATES_DIR.exists():
    for candidate in [Path.cwd() / "templates", Path.cwd() / "app" / "templates"]:
        if candidate.exists():
            TEMPLATES_DIR = candidate
            break

if not STATIC_DIR.exists():
    for candidate in [Path.cwd() / "public" / "static", Path.cwd() / "static", Path.cwd() / "app" / "static"]:
        if candidate.exists():
            STATIC_DIR = candidate
            break

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

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Frontend Page Routes
@app.get("/")
@app.get("/api/index.py")
@app.get("/api")
@app.get("/api/")
def home_page(request: Request):
    index_file = TEMPLATES_DIR / "index.html"
    if index_file.exists():
        return templates.TemplateResponse(request=request, name="index.html")
    return HTMLResponse(f"<h3>AutoGrade AI</h3><p>Template not found at {TEMPLATES_DIR}. Checking directory...</p>")

@app.get("/teacher")
@app.get("/api/index.py/teacher")
@app.get("/api/teacher")
def teacher_page(request: Request):
    teacher_file = TEMPLATES_DIR / "teacher.html"
    if teacher_file.exists():
        return templates.TemplateResponse(request=request, name="teacher.html")
    return HTMLResponse(f"<h3>Teacher Portal</h3><p>Template not found at {TEMPLATES_DIR}.</p>")

@app.get("/student")
@app.get("/api/index.py/student")
@app.get("/api/student")
def student_page(request: Request):
    student_file = TEMPLATES_DIR / "student.html"
    if student_file.exists():
        return templates.TemplateResponse(request=request, name="student.html")
    return HTMLResponse(f"<h3>Student Portal</h3><p>Template not found at {TEMPLATES_DIR}.</p>")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "gemini_ready": bool(settings.GEMINI_API_KEY)
    }

# Vercel ASGI handler
handler = app

