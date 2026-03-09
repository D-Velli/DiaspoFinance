import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError


@pytest.mark.asyncio
@patch("app.tontine.service.get_tontine")
async def test_generate_invite_link_creates_code(mock_get):
    """First call generates a new invite code."""
    from app.tontine.service import generate_invite_link

    tontine = MagicMock()
    tontine.id = uuid.uuid4()
    tontine.created_by = uuid.uuid4()
    tontine.invite_code = None
    mock_get.return_value = tontine

    db = AsyncMock()
    # No existing code with same value
    db.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=None))

    code = await generate_invite_link(db, tontine.id, tontine.created_by)
    assert isinstance(code, str)
    assert len(code) > 0


@pytest.mark.asyncio
@patch("app.tontine.service.get_tontine")
async def test_generate_invite_link_returns_existing(mock_get):
    """If invite code already exists, return it."""
    from app.tontine.service import generate_invite_link

    tontine = MagicMock()
    tontine.id = uuid.uuid4()
    tontine.created_by = uuid.uuid4()
    tontine.invite_code = "existing_code"
    mock_get.return_value = tontine

    db = AsyncMock()
    code = await generate_invite_link(db, tontine.id, tontine.created_by)
    assert code == "existing_code"


@pytest.mark.asyncio
@patch("app.tontine.service.get_tontine")
async def test_generate_invite_link_forbidden_for_non_organizer(mock_get):
    """Non-organizer cannot generate invite link."""
    from app.tontine.service import generate_invite_link

    tontine = MagicMock()
    tontine.created_by = uuid.uuid4()
    mock_get.return_value = tontine

    db = AsyncMock()
    other_user_id = uuid.uuid4()

    with pytest.raises(ForbiddenError):
        await generate_invite_link(db, tontine.id, other_user_id)


@pytest.mark.asyncio
@patch("app.tontine.service.get_tontine")
async def test_regenerate_invite_link(mock_get):
    """Regenerate replaces existing code."""
    from app.tontine.service import regenerate_invite_link

    tontine = MagicMock()
    tontine.id = uuid.uuid4()
    tontine.created_by = uuid.uuid4()
    tontine.invite_code = "old_code"
    mock_get.return_value = tontine

    db = AsyncMock()
    # No existing code collision
    db.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=None))

    code = await regenerate_invite_link(db, tontine.id, tontine.created_by)
    assert code != "old_code"
    assert isinstance(code, str)


@pytest.mark.asyncio
async def test_get_tontine_by_invite_code_not_found():
    """Invalid code raises NotFoundError."""
    from app.tontine.service import get_tontine_by_invite_code

    db = AsyncMock()
    db.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=None))

    with pytest.raises(NotFoundError, match="Invalid or expired invite link"):
        await get_tontine_by_invite_code(db, "bad_code")


@pytest.mark.asyncio
async def test_get_tontine_by_invite_code_found():
    """Valid code returns tontine."""
    from app.tontine.service import get_tontine_by_invite_code

    tontine = MagicMock()
    tontine.id = uuid.uuid4()

    db = AsyncMock()
    db.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=tontine))

    result = await get_tontine_by_invite_code(db, "valid_code")
    assert result.id == tontine.id
