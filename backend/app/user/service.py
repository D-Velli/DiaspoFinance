import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.user.models import User

logger = structlog.get_logger()


async def get_user_by_clerk_id(db: AsyncSession, clerk_id: str) -> User | None:
    """Return User by clerk_id or None."""
    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    return result.scalar_one_or_none()


async def create_or_sync_user(
    db: AsyncSession,
    *,
    clerk_id: str,
    email: str,
    display_name: str,
    phone: str | None = None,
) -> User:
    """Create or update local user profile from Clerk data."""
    user = await get_user_by_clerk_id(db, clerk_id)

    if user:
        user.email = email
        user.display_name = display_name
        if phone is not None:
            user.phone = phone
        logger.info("user.synced", clerk_id=clerk_id)
    else:
        user = User(
            clerk_id=clerk_id,
            email=email,
            display_name=display_name,
            phone=phone,
        )
        db.add(user)
        logger.info("user.created", clerk_id=clerk_id)

    await db.commit()
    await db.refresh(user)
    return user


async def update_user(
    db: AsyncSession,
    clerk_id: str,
    **kwargs,
) -> User | None:
    """Update user fields by clerk_id."""
    user = await get_user_by_clerk_id(db, clerk_id)
    if not user:
        return None

    for field, value in kwargs.items():
        if value is not None and hasattr(user, field):
            setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    logger.info("user.updated", clerk_id=clerk_id, fields=list(kwargs.keys()))
    return user
