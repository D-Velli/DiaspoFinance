"""User router tests — verify GET/PATCH /api/v1/users/me endpoints."""

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.core.dependencies import get_current_user
from app.main import app
from app.user.models import User


def _make_user(**kwargs) -> User:
    """Create a mock User instance with default values."""
    defaults = {
        "id": uuid.uuid4(),
        "clerk_id": "clerk_test_123",
        "display_name": "Test User",
        "email": "test@example.com",
        "phone": None,
        "is_admin": False,
        "preferred_language": "fr",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(kwargs)
    user = MagicMock(spec=User)
    for k, v in defaults.items():
        setattr(user, k, v)
    return user


@pytest.mark.asyncio
async def test_get_me_returns_user_profile(client):
    """Test GET /api/v1/users/me returns authenticated user's profile."""
    mock_user = _make_user()

    app.dependency_overrides[get_current_user] = lambda: mock_user
    try:
        response = await client.get("/api/v1/users/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    assert body["data"]["email"] == "test@example.com"
    assert body["data"]["display_name"] == "Test User"
    assert "clerk_id" not in body["data"]


@pytest.mark.asyncio
async def test_get_me_unauthenticated_returns_401(client):
    """Test GET /api/v1/users/me without auth returns 401."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401
