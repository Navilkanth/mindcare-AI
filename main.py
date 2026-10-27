"""
MindCare AI — FastAPI Application Entry Point
Run with: uvicorn main:app --reload --host 127.0.0.1 --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
import os

from config import settings
from data.database import init_db
from api.routes import chat, mood, history


# ─── App Setup ────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="An empathetic AI mental health support companion",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Startup ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    """Initialize database on app start."""
    init_db()
    print(f"[OK] {settings.APP_NAME} v{settings.APP_VERSION} started")
    print(f"   -> API docs: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"   -> App:      http://{settings.HOST}:{settings.PORT}/")

# ─── API Routes ───────────────────────────────────────────────────────────────

app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(mood.router, prefix="/api", tags=["Mood"])
app.include_router(history.router, prefix="/api", tags=["History"])

# ─── Serve Frontend ───────────────────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    

    @app.get("/chat", include_in_schema=False)
    async def serve_chat():
        return FileResponse(os.path.join(FRONTEND_DIR, "chat.html"))

    @app.get("/login", include_in_schema=False)
    async def redirect_login_to_chat():
        return RedirectResponse(url="/chat", status_code=302)

# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
