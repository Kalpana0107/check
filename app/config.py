import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Detect if running in Vercel Serverless environment
IS_VERCEL = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))

class Settings:
    PROJECT_NAME: str = "AutoGrade AI"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "autograde-super-secret-jwt-key-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Gemini AI Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # Storage & DB
    if IS_VERCEL:
        # Vercel serverless filesystem is read-only except for /tmp
        _tmp_db = Path("/tmp/autograde.db")
        _src_db = BASE_DIR / "autograde.db"
        if not _tmp_db.exists():
            if _src_db.exists():
                try:
                    shutil.copy2(_src_db, _tmp_db)
                except Exception as e:
                    print(f"[Vercel] Warning copying pre-seeded database to /tmp: {e}")
            else:
                _cwd_db = Path.cwd() / "autograde.db"
                if _cwd_db.exists():
                    try:
                        shutil.copy2(_cwd_db, _tmp_db)
                    except Exception as e:
                        print(f"[Vercel] Warning copying CWD db to /tmp: {e}")

        # If user explicitly provided a remote database (Postgres, Supabase, Neon), use it.
        # Otherwise, use the writable /tmp SQLite database.
        _env_db = os.getenv("DATABASE_URL", "")
        if _env_db and not _env_db.startswith("sqlite"):
            DATABASE_URL: str = _env_db
        else:
            DATABASE_URL: str = f"sqlite:///{_tmp_db}"

        UPLOAD_DIR: Path = Path("/tmp/uploads")
    else:
        DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'autograde.db'}")
        UPLOAD_DIR: Path = BASE_DIR / "app" / "static" / "uploads"

settings = Settings()
try:
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass


