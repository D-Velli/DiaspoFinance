import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TontineStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COLLECTING = "collecting"
    DISTRIBUTING = "distributing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TontineFrequency(StrEnum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


class RoundStatus(StrEnum):
    PENDING = "pending"
    COLLECTING = "collecting"
    COMPLETE = "complete"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class MemberRole(StrEnum):
    ORGANIZER = "organizer"
    MEMBER = "member"


class MemberStatus(StrEnum):
    INVITED = "invited"
    PREVIEW = "preview"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXITED = "exited"


class Tontine(Base):
    __tablename__ = "tontines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    hand_amount_cents: Mapped[int] = mapped_column(BigInteger)
    frequency: Mapped[TontineFrequency] = mapped_column(
        Enum(TontineFrequency, values_callable=lambda e: [x.value for x in e])
    )
    max_members: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_pot_cents: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[TontineStatus] = mapped_column(
        Enum(TontineStatus, values_callable=lambda e: [x.value for x in e]),
        default=TontineStatus.DRAFT,
    )
    reserve_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    reserve_percentage: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    invite_code: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    order_locked_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    cycle_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    currency: Mapped[str] = mapped_column(String(3), default="CAD")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    members: Mapped[list["TontineMember"]] = relationship(back_populates="tontine")
    creator = relationship("User")


class TontineMember(Base):
    __tablename__ = "tontine_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    tontine_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tontines.id"))
    role: Mapped[MemberRole] = mapped_column(
        Enum(MemberRole, values_callable=lambda e: [x.value for x in e])
    )
    status: Mapped[MemberStatus] = mapped_column(
        Enum(MemberStatus, values_callable=lambda e: [x.value for x in e]),
        default=MemberStatus.ACTIVE,
    )
    hands: Mapped[Decimal] = mapped_column(Numeric(2, 1), default=1)
    turn_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    __table_args__ = (UniqueConstraint("user_id", "tontine_id"),)

    user = relationship("User")
    tontine: Mapped["Tontine"] = relationship(back_populates="members")


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tontine_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tontines.id"))
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_announcements_tontine_created", "tontine_id", created_at.desc()),
        Index("ix_announcements_author_created", "author_id", "created_at"),
    )

    tontine = relationship("Tontine")
    author = relationship("User")


class TontineRound(Base):
    __tablename__ = "tontine_rounds"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tontine_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tontines.id"))
    round_number: Mapped[int] = mapped_column(Integer)
    beneficiary_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    beneficiary_hands: Mapped[Decimal] = mapped_column(Numeric(2, 1))
    expected_collection_date: Mapped[date] = mapped_column(Date)
    expected_distribution_date: Mapped[date] = mapped_column(Date)
    status: Mapped[RoundStatus] = mapped_column(
        Enum(RoundStatus, values_callable=lambda e: [x.value for x in e]),
        default=RoundStatus.PENDING,
    )
    pot_expected_amount_cents: Mapped[int] = mapped_column(BigInteger)
    pot_actual_amount_cents: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("tontine_id", "round_number"),
    )

    tontine = relationship("Tontine")
    beneficiary = relationship("User")
