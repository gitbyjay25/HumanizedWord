import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import auth, humanize, tools, health

settings = get_settings()

# Set HW_PRELOAD_MODEL=0 to defer model loading to the first request.
PRELOAD_MODEL = os.environ.get("HW_PRELOAD_MODEL", "1") not in {"0", "false", "False"}


@asynccontextmanager
async def lifespan(app):
    """Application lifespan - startup and shutdown events."""
    print("[*] HumanizedText API starting...")
    if PRELOAD_MODEL:
        try:
            from app.pipeline.p3_slm_engine import get_engine

            engine = get_engine()
            engine.warmup()
            print("[+] SLM engine warm")
        except Exception as exc:  # pragma: no cover - startup diagnostics
            print(f"[!] SLM engine failed to load: {exc}")
            print("   The API will start, but /humanize will fail until it is fixed.")
    yield
    print("[*] HumanizedText API shutting down...")


app = FastAPI(
    title="HumanizedText API",
    description="Backend API for AI text humanization",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(humanize.router, prefix="/api", tags=["humanize"])
app.include_router(tools.router, prefix="/api", tags=["tools"])
