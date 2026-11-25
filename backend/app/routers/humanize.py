import time

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_optional_user
from app.middleware.rate_limit import check_rate_limit
from app.models.user import User
from app.schemas.humanize import HumanizeRequest, HumanizeResponse
from app.services.humanize_service import HumanizeService, UnsupportedToolError
from app.services.quota_service import QuotaService
from app.services.response_builder import build_humanize_response

router = APIRouter()


@router.post("/humanize", response_model=HumanizeResponse)
async def humanize_text(
    body: HumanizeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_optional_user),
):
    """
    Humanize AI-generated text.

    - Guests: 6 requests/hour (IP-based)
    - Signed-in: 2000 requests/month (DB-backed)
    """
    # Rate limiting
    await check_rate_limit(request, db, user)

    # Process
    start = time.time()
    service = HumanizeService()
    try:
        result = await service.humanize(
            text=body.text,
            tone=body.tone,
            locked_keywords=body.locked_keywords,
            tool=body.tool,
        )
    except UnsupportedToolError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    elapsed = round(time.time() - start, 2)

    # Track usage for signed-in users
    if user:
        quota_service = QuotaService()
        await quota_service.increment_usage(db, user.id)

    return build_humanize_response(
        result, body.tool, body.tone, body.locked_keywords, elapsed
    )
