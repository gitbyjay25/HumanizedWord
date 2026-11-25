from pydantic import BaseModel
from typing import Optional


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    image: Optional[str] = None
    provider: str

    class Config:
        from_attributes = True


class AuthURLResponse(BaseModel):
    auth_url: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class QuotaResponse(BaseModel):
    requests_used: int
    request_limit: int
    reset_at: str


class MeResponse(BaseModel):
    user: UserResponse
    quota: Optional[QuotaResponse] = None
