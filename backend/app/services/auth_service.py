import uuid
import urllib.parse
from datetime import datetime, timedelta, timezone
from jose import jwt
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.quota import UsageQuota


class AuthService:
    """Handles OAuth flow, JWT creation, and user management."""

    def __init__(self, settings):
        self.settings = settings

    def get_oauth_url(self, provider):
        """Build the OAuth authorization URL for the given provider."""
        if provider == "google":
            params = {
                "client_id": self.settings.google_client_id,
                "redirect_uri": f"{self.settings.backend_url}/api/auth/callback/google",
                "response_type": "code",
                "scope": "openid email profile",
                "access_type": "offline",
                "prompt": "consent",
            }
            return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

        elif provider == "github":
            params = {
                "client_id": self.settings.github_client_id,
                "redirect_uri": f"{self.settings.backend_url}/api/auth/callback/github",
                "scope": "read:user user:email",
            }
            return f"https://github.com/login/oauth/authorize?{urllib.parse.urlencode(params)}"

    async def exchange_code(self, provider, code):
        """Exchange OAuth authorization code for user info."""
        async with httpx.AsyncClient() as client:
            if provider == "google":
                # Exchange code for tokens
                token_resp = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": code,
                        "client_id": self.settings.google_client_id,
                        "client_secret": self.settings.google_client_secret,
                        "redirect_uri": f"{self.settings.backend_url}/api/auth/callback/google",
                        "grant_type": "authorization_code",
                    },
                )
                if token_resp.status_code != 200:
                    return None
                tokens = token_resp.json()

                # Get user info
                user_resp = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {tokens['access_token']}"},
                )
                if user_resp.status_code != 200:
                    return None
                info = user_resp.json()
                return {
                    "email": info["email"],
                    "name": info.get("name"),
                    "image": info.get("picture"),
                    "provider_id": info["id"],
                }

            elif provider == "github":
                # Exchange code for access token
                token_resp = await client.post(
                    "https://github.com/login/oauth/access_token",
                    json={
                        "client_id": self.settings.github_client_id,
                        "client_secret": self.settings.github_client_secret,
                        "code": code,
                    },
                    headers={"Accept": "application/json"},
                )
                if token_resp.status_code != 200:
                    return None
                tokens = token_resp.json()

                # Get user info
                headers = {"Authorization": f"Bearer {tokens['access_token']}"}
                user_resp = await client.get("https://api.github.com/user", headers=headers)
                if user_resp.status_code != 200:
                    return None
                info = user_resp.json()

                # Get primary email if not public
                email = info.get("email")
                if not email:
                    email_resp = await client.get("https://api.github.com/user/emails", headers=headers)
                    if email_resp.status_code == 200:
                        emails = email_resp.json()
                        primary = next((e for e in emails if e.get("primary")), None)
                        email = primary["email"] if primary else emails[0]["email"]

                return {
                    "email": email,
                    "name": info.get("name") or info.get("login"),
                    "image": info.get("avatar_url"),
                    "provider_id": str(info["id"]),
                }

        return None

    async def find_or_create_user(self, db: AsyncSession, user_info: dict, provider: str):
        """Find existing user by email or create a new one."""
        stmt = select(User).where(User.email == user_info["email"])
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                email=user_info["email"],
                name=user_info.get("name"),
                image=user_info.get("image"),
                provider=provider,
                provider_id=user_info["provider_id"],
            )
            db.add(user)

            # Create initial usage quota
            quota = UsageQuota(user_id=user.id)
            db.add(quota)

            await db.flush()

        return user

    def create_access_token(self, user_id: str) -> str:
        """Create a short-lived JWT access token."""
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.settings.access_token_expire_minutes)
        payload = {
            "sub": user_id,
            "exp": expire,
            "type": "access",
        }
        return jwt.encode(payload, self.settings.jwt_secret, algorithm=self.settings.jwt_algorithm)

    async def create_refresh_token(self, db: AsyncSession, user_id: str) -> str:
        """Create a long-lived refresh token and store in DB."""
        token_str = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.settings.refresh_token_expire_days)

        refresh = RefreshToken(
            token=token_str,
            user_id=user_id,
            expires_at=expires_at,
        )
        db.add(refresh)
        await db.flush()

        return token_str

    def verify_access_token(self, token: str) -> dict | None:
        """Verify and decode a JWT access token."""
        try:
            payload = jwt.decode(token, self.settings.jwt_secret, algorithms=[self.settings.jwt_algorithm])
            if payload.get("type") != "access":
                return None
            return payload
        except Exception:
            return None
