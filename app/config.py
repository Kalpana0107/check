import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = "AutoGrade AI"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "autograde-super-secret-jwt-key-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Gemini AI Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # Storage & DB (Vercel serverless functions have a read-only filesystem except /tmp)
    is_vercel: bool = bool(os.getenv("VERCEL"))
    if is_vercel:
        tmp_db = Path("/tmp/autograde.db")
        orig_db = BASE_DIR / "autograde.db"
        if orig_db.exists() and not tmp_db.exists():
            try:
                shutil.copyfile(orig_db, tmp_db)
            except Exception:
                pass
        DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{tmp_db}")
        UPLOAD_DIR: Path = Path("/tmp/uploads")
    else:
        DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'autograde.db'}")
        UPLOAD_DIR: Path = BASE_DIR / "app" / "static" / "uploads"

settings = Settings()
try:
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

