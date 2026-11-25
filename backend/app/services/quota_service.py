from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.quota import UsageQuota


class QuotaService:
    """Manages per-user API usage quotas."""

    async def get_quota(self, db: AsyncSession, user_id: str) -> UsageQuota | None:
        """Get the usage quota for a user, resetting if the period has elapsed."""
        stmt = select(UsageQuota).where(UsageQuota.user_id == user_id)
        result = await db.execute(stmt)
        quota = result.scalar_one_or_none()

        if quota and self._should_reset(quota):
            quota.requests_used = 0
            quota.reset_at = datetime.now(timezone.utc)
            await db.flush()

        return quota

    async def increment_usage(self, db: AsyncSession, user_id: str) -> UsageQuota:
        """Increment the usage counter for a signed-in user."""
        quota = await self.get_quota(db, user_id)
        if not quota:
            quota = UsageQuota(user_id=user_id)
            db.add(quota)
            await db.flush()

        quota.requests_used += 1
        await db.flush()
        return quota

    async def check_limit(self, db: AsyncSession, user_id: str) -> bool:
        """Return True if the user is within their quota limit."""
        quota = await self.get_quota(db, user_id)
        if not quota:
            return True  # No quota record = unlimited
        return quota.requests_used < quota.request_limit

    def _should_reset(self, quota: UsageQuota) -> bool:
        """Check if 30 days have passed since last reset."""
        now = datetime.now(timezone.utc)
        reset_at = quota.reset_at
        if reset_at.tzinfo is None:
            reset_at = reset_at.replace(tzinfo=timezone.utc)
        return now > reset_at + timedelta(days=30)
