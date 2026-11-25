import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class UsageQuota(Base):
    __tablename__ = "usage_quotas"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    requests_used = Column(Integer, default=0)
    request_limit = Column(Integer, default=2000)
    reset_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="usage_quota")

    def __repr__(self):
        return f"<UsageQuota user={self.user_id} used={self.requests_used}/{self.request_limit}>"
