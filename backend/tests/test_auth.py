import pytest
from app.config import get_settings
from app.services.auth_service import AuthService


def test_auth_service_tokens():
    settings = get_settings()
    auth_service = AuthService(settings)

    user_id = "test-user-12345"
    token = auth_service.create_access_token(user_id)
    assert isinstance(token, str)
    assert len(token) > 20

    payload = auth_service.verify_access_token(token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["type"] == "access"


def test_auth_service_invalid_token():
    settings = get_settings()
    auth_service = AuthService(settings)

    assert auth_service.verify_access_token("invalid-token-string") is None


def test_auth_service_oauth_urls():
    settings = get_settings()
    auth_service = AuthService(settings)

    google_url = auth_service.get_oauth_url("google")
    assert "accounts.google.com" in google_url
    assert "redirect_uri" in google_url

    github_url = auth_service.get_oauth_url("github")
    assert "github.com/login/oauth/authorize" in github_url


@pytest.mark.asyncio
async def test_auth_me_unauthorized(async_client):
    response = await async_client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_logout(async_client):
    response = await async_client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json() == {"message": "Logged out"}
