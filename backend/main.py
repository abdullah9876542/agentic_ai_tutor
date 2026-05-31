"""
main.py — FastAPI application entry point
Run: uvicorn backend.main:app --reload --port 8000
"""

import os, logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
logging.basicConfig(level=logging.INFO)

_IS_VERCEL = bool(os.getenv("VERCEL"))
_DEFAULT_UPLOAD = "/tmp/uploads" if _IS_VERCEL else "uploads"
_DEFAULT_DATA = "/tmp/data" if _IS_VERCEL else "data"


def _cors_config():
    origins = ["http://localhost:8501", "http://127.0.0.1:8501"]
    extra = os.getenv("CORS_ORIGINS", "")
    if extra:
        origins.extend(o.strip() for o in extra.split(",") if o.strip())
    return {
        "allow_origins": origins,
        "allow_origin_regex": os.getenv(
            "CORS_ORIGIN_REGEX",
            r"https://(.*\.streamlit\.app|.*\.vercel\.app)",
        ),
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }


from backend.database import engine, Base
from backend.auth.routes               import router as auth_router
from backend.ocr.routes                import router as ocr_router
from backend.routes.analyzer_routes    import router as analyzer_router
from backend.routes.career_routes      import router as career_router
from backend.routes.tutor_routes       import router as tutor_router
from backend.routes.quiz_routes        import router as quiz_router
from backend.routes.dashboard_routes   import router as dashboard_router
from backend.routes.notification_routes import router as notification_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\nAgentic AI Tutor API starting...")
    os.makedirs(os.getenv("UPLOAD_DIR", _DEFAULT_UPLOAD), exist_ok=True)
    os.makedirs(_DEFAULT_DATA, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print("Database tables ready.")
    print("Swagger docs: http://localhost:8000/docs\n")
    yield
    print("Shutting down.")


app = FastAPI(
    title="Agentic AI Tutor API",
    description="Backend for the Agentic AI Tutor — FYP Project.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, **_cors_config())

app.include_router(auth_router)
app.include_router(ocr_router)
app.include_router(analyzer_router)
app.include_router(career_router)
app.include_router(tutor_router)
app.include_router(quiz_router)
app.include_router(dashboard_router)
app.include_router(notification_router)


@app.get("/", tags=["Health"])
def root():
    return {"status":"online","docs":"http://localhost:8000/docs"}

@app.get("/health", tags=["Health"])
def health():
    return {"status":"healthy"}
