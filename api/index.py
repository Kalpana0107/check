import sys
import traceback
from pathlib import Path

# Ensure root workspace directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from app.main import app
except Exception as e:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse

    app = FastAPI(title="Diagnostic Fallback")
    error_trace = traceback.format_exc()
    print(f"[Vercel Startup Error]:\n{error_trace}")

    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
    async def diagnostic_error_handler(full_path: str = ""):
        return HTMLResponse(
            content=f"<html><body><h2>Startup Error</h2><pre>{error_trace}</pre></body></html>",
            status_code=500
        )
