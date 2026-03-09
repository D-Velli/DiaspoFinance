import uuid
from datetime import datetime, timedelta, timezone

import bleach
import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenError, NotFoundError, RateLimitError, ValidationError
from app.tontine.models import Announcement, MemberRole, MemberStatus, TontineMember
from app.user.models import User

logger = structlog.get_logger()

ALLOWED_TAGS: list[str] = []  # Plain text only at MVP
MAX_CONTENT_LENGTH = 5000
MAX_ANNOUNCEMENTS_PER_DAY = 10


def sanitize_content(content: str) -> str:
    """Strip dangerous HTML tags from announcement content."""
    cleaned = bleach.clean(content, tags=ALLOWED_TAGS, strip=True)
    return cleaned.strip()[:MAX_CONTENT_LENGTH]


async def _require_member(
    db: AsyncSession, tontine_id: uuid.UUID, user_id: uuid.UUID
) -> TontineMember:
    """Check user is an active/preview member of the tontine."""
    result = await db.execute(
        select(TontineMember)
        .where(TontineMember.tontine_id == tontine_id)
        .where(TontineMember.user_id == user_id)
        .where(TontineMember.status.in_([MemberStatus.ACTIVE, MemberStatus.PREVIEW]))
    )
    member = result.scalar_one_or_none()
    if not member:
        raise ForbiddenError(message="You are not a member of this tontine")
    return member


async def _require_organizer(
    db: AsyncSession, tontine_id: uuid.UUID, user_id: uuid.UUID
) -> TontineMember:
    """Check user is the organizer of the tontine."""
    member = await _require_member(db, tontine_id, user_id)
    if member.role != MemberRole.ORGANIZER:
        raise ForbiddenError(message="Only the organizer can perform this action")
    return member


async def create_announcement(
    db: AsyncSession, tontine_id: uuid.UUID, user: User, content: str
) -> Announcement:
    """Create an announcement. Organizer only, with rate limiting."""
    await _require_organizer(db, tontine_id, user.id)

    # Rate limit: max 10 announcements/day per organizer per tontine
    since = datetime.now(timezone.utc) - timedelta(days=1)
    count_q = (
        select(func.count())
        .select_from(Announcement)
        .where(Announcement.tontine_id == tontine_id)
        .where(Announcement.author_id == user.id)
        .where(Announcement.created_at >= since)
        .where(Announcement.deleted_at.is_(None))
    )
    count = (await db.execute(count_q)).scalar() or 0
    if count >= MAX_ANNOUNCEMENTS_PER_DAY:
        raise RateLimitError(
            message=f"Maximum {MAX_ANNOUNCEMENTS_PER_DAY} announcements per day"
        )

    sanitized = sanitize_content(content)
    if not sanitized:
        raise ValidationError(message="Announcement content cannot be empty")

    announcement = Announcement(
        tontine_id=tontine_id,
        author_id=user.id,
        content=sanitized,
    )
    db.add(announcement)
    await db.commit()
    await db.refresh(announcement)

    logger.info(
        "announcement.created",
        announcement_id=str(announcement.id),
        tontine_id=str(tontine_id),
        author_id=str(user.id),
    )

    return announcement


async def list_announcements(
    db: AsyncSession,
    tontine_id: uuid.UUID,
    user_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = 20,
) -> tuple[list[Announcement], str | None, bool]:
    """List announcements with cursor-based pagination. Members only."""
    await _require_member(db, tontine_id, user_id)

    query = (
        select(Announcement)
        .options(selectinload(Announcement.author))
        .where(Announcement.tontine_id == tontine_id)
        .where(Announcement.deleted_at.is_(None))
        .order_by(Announcement.created_at.desc())
        .limit(limit + 1)
    )

    if cursor:
        try:
            cursor_date = datetime.fromisoformat(cursor)
        except ValueError as e:
            raise ValidationError(message=f"Invalid cursor format: {e}") from e
        query = query.where(Announcement.created_at < cursor_date)

    results = list((await db.execute(query)).scalars().all())
    has_more = len(results) > limit
    items = results[:limit]
    next_cursor = items[-1].created_at.isoformat() if has_more and items else None

    return items, next_cursor, has_more


async def delete_announcement(
    db: AsyncSession,
    tontine_id: uuid.UUID,
    announcement_id: uuid.UUID,
    user: User,
) -> None:
    """Soft-delete an announcement. Organizer only."""
    await _require_organizer(db, tontine_id, user.id)

    result = await db.execute(
        select(Announcement)
        .where(Announcement.id == announcement_id)
        .where(Announcement.tontine_id == tontine_id)
        .where(Announcement.deleted_at.is_(None))
    )
    announcement = result.scalar_one_or_none()
    if not announcement:
        raise NotFoundError(message="Announcement not found")

    announcement.deleted_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info(
        "announcement.deleted",
        announcement_id=str(announcement_id),
        tontine_id=str(tontine_id),
    )
