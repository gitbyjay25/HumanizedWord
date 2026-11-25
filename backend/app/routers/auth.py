from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.config import get_settings
from app.services.auth_service import AuthService
from app.schemas.auth import MeResponse
from app.middleware.auth_middleware import get_current_user, get_optional_user
from app.models.user import User

router = APIRouter()
settings = get_settings()


@router.get("/login/{provider}")
async def login(provider: str):
    """Redirect to OAuth provider login page."""
    if provider not in ("google", "github"):
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    auth_service = AuthService(settings)
    auth_url = auth_service.get_oauth_url(provider)
    return RedirectResponse(url=auth_url)


@router.get("/callback/{provider}")
async def callback(provider: str, code: str, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    """OAuth callback — exchange code for tokens, create/find user, set JWT cookie."""
    if provider not in ("google", "github"):
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    auth_service = AuthService(settings)

    # Exchange code for user info from provider
    user_info = await auth_service.exchange_code(provider, code)
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to authenticate with provider")

    # Find or create user
    user = await auth_service.find_or_create_user(db, user_info, provider)

    # Generate JWT tokens
    access_token = auth_service.create_access_token(user.id)
    refresh_token = await auth_service.create_refresh_token(db, user.id)

    # Set httpOnly cookies
    redirect = RedirectResponse(url=settings.frontend_url, status_code=302)
    redirect.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set True in production with HTTPS
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )
    redirect.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 86400,
    )

    return redirect


@router.get("/me", response_model=MeResponse)
async def get_me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get current authenticated user profile and quota."""
    from app.services.quota_service import QuotaService

    quota_service = QuotaService()
    quota = await quota_service.get_quota(db, user.id)

    return MeResponse(
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "image": user.image,
            "provider": user.provider,
        },
        quota={
            "requests_used": quota.requests_used,
            "request_limit": quota.request_limit,
            "reset_at": quota.reset_at.isoformat(),
        } if quota else None,
    )


@router.post("/logout")
async def logout(response: Response):
    """Clear auth cookies."""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}
