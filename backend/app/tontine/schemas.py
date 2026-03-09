import uuid
from datetime import date, datetime
from decimal import Decimal

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.tontine.models import MemberRole, MemberStatus, RoundStatus, TontineFrequency, TontineStatus


class TontineCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    hand_amount_cents: int = Field(gt=0)
    frequency: TontineFrequency
    start_date: date
    max_members: int | None = Field(default=None, gt=0)
    max_pot_cents: int | None = Field(default=None, gt=0)
    reserve_enabled: bool = False
    reserve_percentage: Decimal | None = Field(default=None, ge=1, le=5)
    organizer_hands: Decimal = Field(default=Decimal("1"))

    @field_validator("start_date")
    @classmethod
    def validate_start_date(cls, v: date) -> date:
        if v < date.today():
            msg = "Start date must be today or in the future"
            raise ValueError(msg)
        return v

    @field_validator("organizer_hands")
    @classmethod
    def validate_hands(cls, v: Decimal) -> Decimal:
        allowed = {Decimal("0.5"), Decimal("1"), Decimal("2")}
        if v not in allowed:
            msg = "Hands must be 0.5, 1, or 2"
            raise ValueError(msg)
        return v

    @field_validator("reserve_percentage")
    @classmethod
    def validate_reserve(cls, v: Decimal | None, info) -> Decimal | None:
        if info.data.get("reserve_enabled") and v is None:
            msg = "reserve_percentage is required when reserve is enabled"
            raise ValueError(msg)
        if not info.data.get("reserve_enabled") and v is not None:
            return None
        return v


class TontineUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=100)
    start_date: date | None = None
    max_members: int | None = Field(default=None, gt=0)
    max_pot_cents: int | None = Field(default=None, gt=0)
    reserve_enabled: bool | None = None
    reserve_percentage: Decimal | None = Field(default=None, ge=1, le=5)

    @field_validator("start_date")
    @classmethod
    def validate_start_date(cls, v: date | None) -> date | None:
        if v is not None and v < date.today():
            msg = "Start date must be today or in the future"
            raise ValueError(msg)
        return v


class TontineResponse(BaseModel):
    id: uuid.UUID
    name: str
    hand_amount_cents: int
    frequency: TontineFrequency
    start_date: date | None
    max_members: int | None
    max_pot_cents: int | None
    status: TontineStatus
    reserve_enabled: bool
    reserve_percentage: Decimal | None
    invite_code: str | None
    currency: str
    created_by: uuid.UUID
    created_at: datetime
    member_count: int = 0
    total_hands: Decimal = Decimal("0")
    pot_per_turn_cents: int = 0

    model_config = {"from_attributes": True}


class MemberResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    display_name: str
    role: MemberRole
    status: MemberStatus
    hands: Decimal
    turn_position: int | None
    joined_at: datetime

    model_config = {"from_attributes": True}


# --- Capacity schemas ---


class CapacityResponse(BaseModel):
    member_count: int
    total_hands: Decimal
    pot_per_turn_cents: int
    max_hands: float | None
    hands_remaining: float | None
    max_members: int | None
    total_turns: int
    estimated_weeks: int
    hand_amount_cents: int
    frequency: str
    is_full: bool


# --- Rotation schemas ---


class ManualRotationRequest(BaseModel):
    member_order: list[uuid.UUID]


class RotationMemberEntry(BaseModel):
    id: str
    user_id: str
    hands: float


class RotationPosition(BaseModel):
    position: int
    members: list[RotationMemberEntry]
    occupies_positions: list[int] | None = None


class RotationPairingInfo(BaseModel):
    half_hand_count: int
    pairs: int
    has_orphan: bool
    orphan_member_id: str | None
    total_turns: int


class RotationResponse(BaseModel):
    rotation: list[RotationPosition]
    half_hand_count: int
    pairs: int
    has_orphan: bool
    orphan_member_id: str | None
    total_turns: int


# --- Announcement schemas ---


class AnnouncementCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class AuthorPublic(BaseModel):
    id: uuid.UUID
    display_name: str

    model_config = {"from_attributes": True}


class AnnouncementResponse(BaseModel):
    id: uuid.UUID
    author: AuthorPublic
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CursorMeta(BaseModel):
    cursor: str | None
    has_more: bool


class AnnouncementsListResponse(BaseModel):
    data: list[AnnouncementResponse]
    meta: CursorMeta


# --- Cycle / Rounds schemas ---


class PreStartCheck(BaseModel):
    code: str
    message: str
    severity: Literal["error", "warning"]


class PreStartResponse(BaseModel):
    can_start: bool
    blockers: list[PreStartCheck]
    warnings: list[PreStartCheck]


class StartCycleRequest(BaseModel):
    cycle_start_date: date | None = None

    @field_validator("cycle_start_date")
    @classmethod
    def validate_cycle_date(cls, v: date | None) -> date | None:
        if v is not None and v < date.today():
            msg = "Cycle start date must be today or in the future"
            raise ValueError(msg)
        return v


class RoundResponse(BaseModel):
    id: uuid.UUID
    round_number: int
    beneficiary_user_id: uuid.UUID
    beneficiary_display_name: str
    beneficiary_hands: Decimal
    expected_collection_date: date
    expected_distribution_date: date
    status: RoundStatus
    pot_expected_amount_cents: int

    model_config = {"from_attributes": True}
