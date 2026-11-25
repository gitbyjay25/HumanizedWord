from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    from app.pipeline.p3_slm_engine import engine_status

    payload = {
        "status": "healthy",
        "service": "humanizedtext-api",
        "version": "0.1.0",
        "model": engine_status(),
    }
    return payload
