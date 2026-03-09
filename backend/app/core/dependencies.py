from collections.abc import AsyncGenerator

import structlog
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, settings
from app.core.database import async_session_factory
from app.core.exceptions import DiaspoFinanceError
from app.core.security import verify_clerk_jwt
from app.user import service as user_service
from app.user.models import User

logger = structlog.get_logger()

bearer_scheme = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


def get_settings() -> Settings:
    return settings


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and verify Clerk JWT, load local profile."""
    token = credentials.credentials

    try:
        claims = await verify_clerk_jwt(token, settings.CLERK_JWKS_URL)
    except JWTError as e:
        raise DiaspoFinanceError(
            message=f"Invalid token: {e}",
            code="UNAUTHORIZED",
            status_code=401,
        ) from e

    clerk_id = claims["sub"]

    user = await user_service.get_user_by_clerk_id(db, clerk_id)

    if not user:
        logger.warning("user.fallback_creation", clerk_id=clerk_id)
        user = await user_service.create_or_sync_user(
            db,
            clerk_id=clerk_id,
            email=claims.get("email", ""),
            display_name=claims.get("name", claims.get("email", "")),
            phone=claims.get("phone_number"),
        )

    return user


class RequireRole:
    """Stub for future RBAC — checks user role."""

    def __init__(self, role: str):
        self.role = role

    async def __call__(self, user: User = Depends(get_current_user)) -> User:
        # RBAC will be implemented in future stories
        return user
