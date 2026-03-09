import uuid
from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: uuid.UUID
    display_name: str
    email: str
    phone: str | None = None
    preferred_language: str = "fr"
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    display_name: str | None = None
    phone: str | None = None
    preferred_language: str | None = None
