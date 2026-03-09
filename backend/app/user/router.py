from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.user import service as user_service
from app.user.models import User
from app.user.schemas import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=dict)
async def get_me(user: User = Depends(get_current_user)):
    """Return the current user's profile."""
    return {"data": UserResponse.model_validate(user).model_dump(mode="json")}


@router.patch("/me", response_model=dict)
async def update_me(
    body: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's profile."""
    update_data = body.model_dump(exclude_unset=True)
    updated_user = await user_service.update_user(db, user.clerk_id, **update_data)
    return {"data": UserResponse.model_validate(updated_user).model_dump(mode="json")}
