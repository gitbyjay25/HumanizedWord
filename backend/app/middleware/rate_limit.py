import os
import time
from collections import defaultdict
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.quota_service import QuotaService
from app.models.user import User

# In-memory store for guest rate limiting (IP -> list of timestamps)
_guest_requests: dict[str, list[float]] = defaultdict(list)

GUEST_LIMIT = int(os.environ.get("HW_GUEST_LIMIT", "6"))
GUEST_WINDOW = 3600  # 1 hour in seconds


def reset_guest_limits():
    """Reset in-memory guest rate limit tracking (used in tests)."""
    _guest_requests.clear()


async def check_rate_limit(request: Request, db: AsyncSession, user: User | None):
    """
    Enforce rate limits.
    
    - Guests: 6 requests per hour (IP-based, in-memory, configurable via HW_GUEST_LIMIT)
    - Signed-in users: 2000 requests per month (DB-backed)
    """
    if user:
        # DB-backed rate limiting for signed-in users
        quota_service = QuotaService()
        within_limit = await quota_service.check_limit(db, user.id)
        if not within_limit:
            raise HTTPException(
                status_code=429,
                detail="Monthly request limit reached. Upgrade for unlimited access.",
            )
    else:
        # IP-based rate limiting for guests
        client_ip = _get_client_ip(request)
        now = time.time()

        # Clean old timestamps outside the window
        _guest_requests[client_ip] = [
            ts for ts in _guest_requests[client_ip] if now - ts < GUEST_WINDOW
        ]

        if len(_guest_requests[client_ip]) >= GUEST_LIMIT:
            raise HTTPException(
                status_code=429,
                detail=f"Guest limit reached ({GUEST_LIMIT} requests/hour). Sign in for more.",
            )

        _guest_requests[client_ip].append(now)


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For header."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
