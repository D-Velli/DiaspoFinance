"""User service tests — require database connection.

These tests verify the service logic with mocked DB sessions.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.user import service as user_service
from app.user.models import User


def _make_user(**kwargs) -> User:
    """Create a mock User instance."""
    defaults = {
        "id": uuid.uuid4(),
        "clerk_id": "clerk_test_123",
        "display_name": "Test User",
        "email": "test@example.com",
        "phone": None,
        "is_admin": False,
        "preferred_language": "fr",
    }
    defaults.update(kwargs)
    user = MagicMock(spec=User)
    for k, v in defaults.items():
        setattr(user, k, v)
    return user


@pytest.mark.asyncio
async def test_get_user_by_clerk_id_returns_none_when_not_found():
    """Test that get_user_by_clerk_id returns None for unknown clerk_id."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    result = await user_service.get_user_by_clerk_id(mock_db, "unknown_clerk_id")
    assert result is None


@pytest.mark.asyncio
async def test_get_user_by_clerk_id_returns_user():
    """Test that get_user_by_clerk_id returns user when found."""
    mock_user = _make_user()
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute.return_value = mock_result

    result = await user_service.get_user_by_clerk_id(mock_db, "clerk_test_123")
    assert result is not None
    assert result.clerk_id == "clerk_test_123"


@pytest.mark.asyncio
async def test_create_or_sync_creates_new_user():
    """Test that create_or_sync_user creates a user when none exists."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    # Mock refresh to set expected attributes
    async def mock_refresh(user):
        user.id = uuid.uuid4()

    mock_db.refresh = mock_refresh

    user = await user_service.create_or_sync_user(
        mock_db,
        clerk_id="new_clerk",
        email="new@example.com",
        display_name="New User",
    )

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    assert user.clerk_id == "new_clerk"


@pytest.mark.asyncio
async def test_create_or_sync_updates_existing_user():
    """Test that create_or_sync_user updates existing user (idempotent)."""
    existing_user = _make_user(display_name="Old Name")
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_user
    mock_db.execute.return_value = mock_result

    user = await user_service.create_or_sync_user(
        mock_db,
        clerk_id="clerk_test_123",
        email="updated@example.com",
        display_name="New Name",
    )

    assert user.display_name == "New Name"
    assert user.email == "updated@example.com"
    mock_db.commit.assert_called_once()
