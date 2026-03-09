import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError, RateLimitError, ValidationError
from app.tontine.announcement_service import sanitize_content


# --- Sanitization tests ---


def test_sanitize_strips_html_tags():
    assert sanitize_content("<script>alert('xss')</script>Hello") == "alert('xss')Hello"


def test_sanitize_strips_dangerous_tags_keeps_text():
    assert sanitize_content("<b>Bold</b> text") == "Bold text"


def test_sanitize_truncates_long_content():
    long = "x" * 6000
    assert len(sanitize_content(long)) == 5000


def test_sanitize_strips_whitespace():
    assert sanitize_content("  hello  ") == "hello"


# --- Helper to build mocks ---


def _make_member(role="organizer", status="active"):
    m = MagicMock()
    m.role = MagicMock()
    m.role.__eq__ = lambda self, other: role == other.value if hasattr(other, "value") else role == other
    # For the MemberRole.ORGANIZER comparison
    from app.tontine.models import MemberRole
    m.role = MemberRole.ORGANIZER if role == "organizer" else MemberRole.MEMBER
    m.status = status
    return m


def _make_user():
    u = MagicMock()
    u.id = uuid.uuid4()
    u.display_name = "Test User"
    return u


# --- Create announcement tests ---


@pytest.mark.asyncio
@patch("app.tontine.announcement_service._require_organizer")
async def test_create_announcement_success(mock_require):
    from app.tontine.announcement_service import create_announcement

    mock_require.return_value = _make_member("organizer")
    user = _make_user()
    tontine_id = uuid.uuid4()

    db = AsyncMock()
    # Rate limit count query returns 0
    db.execute.return_value = MagicMock(scalar=MagicMock(return_value=0))

    ann = await create_announcement(db, tontine_id, user, "Hello everyone!")
    assert ann.content == "Hello everyone!"
    assert ann.tontine_id == tontine_id
    assert ann.author_id == user.id
    db.add.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.asyncio
@patch("app.tontine.announcement_service._require_organizer")
async def test_create_announcement_sanitizes_html(mock_require):
    from app.tontine.announcement_service import create_announcement

    mock_require.return_value = _make_member("organizer")
    user = _make_user()

    db = AsyncMock()
    db.execute.return_value = MagicMock(scalar=MagicMock(return_value=0))

    ann = await create_announcement(db, uuid.uuid4(), user, "<script>alert(1)</script>Safe text")
    assert "<script>" not in ann.content
    assert "Safe text" in ann.content


@pytest.mark.asyncio
@patch("app.tontine.announcement_service._require_organizer")
async def test_create_announcement_empty_after_sanitize_raises(mock_require):
    from app.tontine.announcement_service import create_announcement

    mock_require.return_value = _make_member("organizer")
    user = _make_user()

    db = AsyncMock()
    db.execute.return_value = MagicMock(scalar=MagicMock(return_value=0))

    with pytest.raises(ValidationError, match="empty"):
        await create_announcement(db, uuid.uuid4(), user, "<script></script>")


@pytest.mark.asyncio
@patch("app.tontine.announcement_service._require_organizer")
async def test_create_announcement_rate_limited(mock_require):
    from app.tontine.announcement_service import create_announcement

    mock_require.return_value = _make_member("organizer")
    user = _make_user()

    db = AsyncMock()
    # Return count of 10 (at limit)
    db.execute.return_value = MagicMock(scalar=MagicMock(return_value=10))

    with pytest.raises(RateLimitError, match="10"):
        await create_announcement(db, uuid.uuid4(), user, "Another one")


@pytest.mark.asyncio
@patch("app.tontine.announcement_service._require_member")
async def test_create_announcement_member_forbidden(mock_require):
    """Regular member cannot create announcements."""
    from app.tontine.announcement_service import create_announcement

    member = _make_member("member")
    mock_require.return_value = member

    user = _make_user()
    db = AsyncMock()

    # _require_organizer will call _require_member then check role
    # We need to NOT mock _require_organizer so it actually runs
    with pytest.raises(ForbiddenError, match="organizer"):
        # Reset the mock so the real function runs
        with patch("app.tontine.announcement_service._require_member", return_value=member):
            from app.tontine.announcement_service import _require_organizer

            await _require_organizer(db, uuid.uuid4(), user.id)


# --- List announcements tests ---


@pytest.mark.asyncio
@patch("app.tontine.announcement_service._require_member")
async def test_list_announcements_returns_items(mock_require):
    from app.tontine.announcement_service import list_announcements

    mock_require.return_value = _make_member()
    user_id = uuid.uuid4()

    ann1 = MagicMock()
    ann1.created_at = datetime.now(timezone.utc)

    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [ann1]
    db.execute.return_value = mock_result

    items, cursor, has_more = await list_announcements(db, uuid.uuid4(), user_id)
    assert len(items) == 1
    assert has_more is False
    assert cursor is None


@pytest.mark.asyncio
@patch("app.tontine.announcement_service._require_member")
async def test_list_announcements_has_more(mock_require):
    from app.tontine.announcement_service import list_announcements

    mock_require.return_value = _make_member()

    # Return limit+1 items to trigger has_more
    items_mock = []
    for i in range(21):
        ann = MagicMock()
        ann.created_at = datetime.now(timezone.utc) - timedelta(minutes=i)
        items_mock.append(ann)

    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = items_mock
    db.execute.return_value = mock_result

    items, cursor, has_more = await list_announcements(db, uuid.uuid4(), uuid.uuid4(), limit=20)
    assert len(items) == 20
    assert has_more is True
    assert cursor is not None


# --- Delete announcement tests ---


@pytest.mark.asyncio
@patch("app.tontine.announcement_service._require_organizer")
async def test_delete_announcement_soft_deletes(mock_require):
    from app.tontine.announcement_service import delete_announcement

    mock_require.return_value = _make_member("organizer")

    ann = MagicMock()
    ann.deleted_at = None

    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = ann
    db.execute.return_value = mock_result

    user = _make_user()
    await delete_announcement(db, uuid.uuid4(), uuid.uuid4(), user)

    assert ann.deleted_at is not None
    db.commit.assert_called_once()


@pytest.mark.asyncio
@patch("app.tontine.announcement_service._require_organizer")
async def test_delete_announcement_not_found(mock_require):
    from app.tontine.announcement_service import delete_announcement

    mock_require.return_value = _make_member("organizer")

    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    user = _make_user()
    with pytest.raises(NotFoundError, match="Announcement not found"):
        await delete_announcement(db, uuid.uuid4(), uuid.uuid4(), user)
