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
    # Diagnostic fallback: If main app fails to import on Vercel,
    # display the exact Python traceback in the browser instead of opaque 500 error
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse

    app = FastAPI(title="Diagnostic Fallback")
    error_trace = traceback.format_exc()
    print(f"[Vercel Startup Error]:\n{error_trace}")

    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
    async def diagnostic_error_handler(full_path: str = ""):
        return HTMLResponse(
            content=f"""<!DOCTYPE html>
<html>
<head><title>Startup Error Diagnostic</title></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #fff1f2; color: #9f1239; padding: 2rem;">
  <div style="max-width: 900px; margin: 0 auto; background: white; border: 1px solid #fecdd3; border-radius: 12px; padding: 2rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
    <h2 style="color: #be123c; margin-top: 0;">⚠️ FastAPI Startup Crash on Vercel</h2>
    <p style="color: #4b5563;">An unhandled error occurred while importing <code>app.main</code> on Vercel serverless runtime:</p>
    <pre style="background: #1e293b; color: #f8fafc; padding: 1.25rem; border-radius: 8px; overflow-x: auto; font-size: 13px; line-height: 1.5;">{error_trace}</pre>
  </div>
</body>
</html>""",
            status_code=500
        )
