import time

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_optional_user
from app.middleware.rate_limit import check_rate_limit
from app.models.user import User
from app.schemas.humanize import (
    EvaluateRequest,
    EvaluateResponse,
    HumanizeRequest,
    HumanizeResponse,
)
from app.services.humanize_service import HumanizeService, UnsupportedToolError
from app.services.quota_service import QuotaService
from app.services.response_builder import build_humanize_response

router = APIRouter()


@router.post("/tools", response_model=HumanizeResponse)
async def run_tool(
    body: HumanizeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_optional_user),
):
    """
    Run a text transformation tool (rewrite, expand, shorten, summarize, grammar).
    Uses the same request/response contract as /humanize.
    """
    await check_rate_limit(request, db, user)

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

    if user:
        quota_service = QuotaService()
        await quota_service.increment_usage(db, user.id)

    return build_humanize_response(
        result, body.tool, body.tone, body.locked_keywords, elapsed
    )


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_context(
    body: EvaluateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_optional_user),
):
    """
    Score a candidate rewrite against an original passage across the five
    context-preservation dimensions (P4), without generating anything.
    """
    await check_rate_limit(request, db, user)

    service = HumanizeService()
    report = await service.evaluate_only(body.original_text, body.candidate_text)

    return EvaluateResponse(**report)
