import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import ForbiddenError
from app.tontine import announcement_service
from app.tontine import cycle_service
from app.tontine import rotation as rotation_service
from app.tontine import service as tontine_service
from app.tontine.rotation import OrphanHalfHandError
from app.tontine.schemas import (
    AnnouncementCreate,
    AnnouncementResponse,
    AnnouncementsListResponse,
    AuthorPublic,
    CursorMeta,
    ManualRotationRequest,
    MemberResponse,
    RoundResponse,
    StartCycleRequest,
    TontineCreate,
    TontineResponse,
    TontineUpdate,
)
from app.user.models import User

router = APIRouter(prefix="/tontines", tags=["tontines"])


def _tontine_to_response(tontine, stats: dict | None = None) -> TontineResponse:
    return TontineResponse(
        id=tontine.id,
        name=tontine.name,
        hand_amount_cents=tontine.hand_amount_cents,
        frequency=tontine.frequency,
        start_date=tontine.start_date,
        max_members=tontine.max_members,
        max_pot_cents=tontine.max_pot_cents,
        status=tontine.status,
        reserve_enabled=tontine.reserve_enabled,
        reserve_percentage=tontine.reserve_percentage,
        invite_code=tontine.invite_code,
        currency=tontine.currency,
        created_by=tontine.created_by,
        created_at=tontine.created_at,
        member_count=stats["member_count"] if stats else 0,
        total_hands=stats["total_hands"] if stats else Decimal("0"),
        pot_per_turn_cents=stats["pot_per_turn_cents"] if stats else 0,
    )


@router.post("", status_code=201)
async def create_tontine(
    data: TontineCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tontine = await tontine_service.create_tontine(db, user, data)
    stats = await tontine_service.get_tontine_stats(db, tontine.id)
    return {"data": _tontine_to_response(tontine, stats)}


@router.get("")
async def list_tontines(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tontines = await tontine_service.list_user_tontines(db, user.id)
    stats_map = await tontine_service.get_batch_stats(db, tontines)
    results = [_tontine_to_response(t, stats_map.get(t.id)) for t in tontines]
    return {"data": results}


@router.get("/{tontine_id}")
async def get_tontine(
    tontine_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Membership check
    if not await tontine_service.is_member(db, tontine_id, user.id):
        raise ForbiddenError(message="You are not a member of this tontine")

    tontine = await tontine_service.get_tontine(db, tontine_id)
    stats = await tontine_service.get_tontine_stats(db, tontine.id)
    return {"data": _tontine_to_response(tontine, stats)}


@router.patch("/{tontine_id}")
async def update_tontine(
    tontine_id: uuid.UUID,
    data: TontineUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tontine = await tontine_service.update_tontine(db, tontine_id, user, data)
    stats = await tontine_service.get_tontine_stats(db, tontine.id)
    return {"data": _tontine_to_response(tontine, stats)}


@router.get("/{tontine_id}/capacity")
async def get_capacity(
    tontine_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await tontine_service.is_member(db, tontine_id, user.id):
        raise ForbiddenError(message="You are not a member of this tontine")

    capacity = await tontine_service.get_capacity(db, tontine_id)
    return {"data": capacity}


@router.get("/{tontine_id}/members")
async def list_members(
    tontine_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await tontine_service.is_member(db, tontine_id, user.id):
        raise ForbiddenError(message="You are not a member of this tontine")

    members = await tontine_service.get_tontine_members(db, tontine_id)
    results = []
    for m in members:
        await db.refresh(m, ["user"])
        results.append(
            MemberResponse(
                id=m.id,
                user_id=m.user_id,
                display_name=m.user.display_name,
                role=m.role,
                status=m.status,
                hands=m.hands,
                turn_position=m.turn_position,
                joined_at=m.joined_at,
            )
        )
    return {"data": results}


# --- Invite endpoints ---


@router.post("/{tontine_id}/invite")
async def generate_invite(
    tontine_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    code = await tontine_service.generate_invite_link(db, tontine_id, user.id)
    return {"data": {"invite_code": code}}


@router.post("/{tontine_id}/invite/regenerate")
async def regenerate_invite(
    tontine_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    code = await tontine_service.regenerate_invite_link(db, tontine_id, user.id)
    return {"data": {"invite_code": code}}


# --- Rotation endpoints ---


@router.post("/{tontine_id}/rotation/random")
async def generate_random_rotation(
    tontine_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await rotation_service.generate_random_rotation(db, tontine_id, user.id)
    except OrphanHalfHandError as e:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "ORPHAN_HALF_HAND", "message": str(e), "member_ids": [str(mid) for mid in e.member_ids]}},
        )
    return {"data": result}


@router.put("/{tontine_id}/rotation")
async def set_manual_rotation(
    tontine_id: uuid.UUID,
    data: ManualRotationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await rotation_service.set_manual_rotation(db, tontine_id, user.id, data.member_order)
    except OrphanHalfHandError as e:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "ORPHAN_HALF_HAND", "message": str(e), "member_ids": [str(mid) for mid in e.member_ids]}},
        )
    return {"data": result}


@router.get("/{tontine_id}/rotation")
async def get_rotation_order(
    tontine_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await tontine_service.is_member(db, tontine_id, user.id):
        raise ForbiddenError(message="You are not a member of this tontine")

    result = await rotation_service.get_rotation(db, tontine_id)
    members = await rotation_service.get_active_members(db, tontine_id)
    pairing = rotation_service.check_half_hand_pairing(members)

    return {"data": {"rotation": result, **pairing}}


# --- Cycle endpoints ---


@router.get("/{tontine_id}/pre-start-checks")
async def get_pre_start_checks(
    tontine_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await tontine_service.is_member(db, tontine_id, user.id):
        raise ForbiddenError(message="You are not a member of this tontine")

    checks = await cycle_service.pre_start_checks(db, tontine_id)
    return {"data": checks}


@router.post("/{tontine_id}/start")
async def start_cycle(
    tontine_id: uuid.UUID,
    data: StartCycleRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tontine, rounds = await cycle_service.start_cycle(
        db, tontine_id, user.id, data.cycle_start_date
    )
    stats = await tontine_service.get_tontine_stats(db, tontine.id)

    round_responses = [
        RoundResponse(
            id=r.id,
            round_number=r.round_number,
            beneficiary_user_id=r.beneficiary_user_id,
            beneficiary_display_name=r.beneficiary.display_name,
            beneficiary_hands=r.beneficiary_hands,
            expected_collection_date=r.expected_collection_date,
            expected_distribution_date=r.expected_distribution_date,
            status=r.status,
            pot_expected_amount_cents=r.pot_expected_amount_cents,
        )
        for r in rounds
    ]

    return {
        "data": {
            "tontine": _tontine_to_response(tontine, stats),
            "rounds": round_responses,
        }
    }


@router.get("/{tontine_id}/rounds")
async def list_rounds(
    tontine_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await tontine_service.is_member(db, tontine_id, user.id):
        raise ForbiddenError(message="You are not a member of this tontine")

    rounds = await cycle_service.list_rounds(db, tontine_id)
    results = [
        RoundResponse(
            id=r.id,
            round_number=r.round_number,
            beneficiary_user_id=r.beneficiary_user_id,
            beneficiary_display_name=r.beneficiary.display_name,
            beneficiary_hands=r.beneficiary_hands,
            expected_collection_date=r.expected_collection_date,
            expected_distribution_date=r.expected_distribution_date,
            status=r.status,
            pot_expected_amount_cents=r.pot_expected_amount_cents,
        )
        for r in rounds
    ]
    return {"data": results}


# --- Announcement endpoints ---


@router.post("/{tontine_id}/announcements", status_code=201)
async def create_announcement(
    tontine_id: uuid.UUID,
    data: AnnouncementCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ann = await announcement_service.create_announcement(db, tontine_id, user, data.content)
    await db.refresh(ann, ["author"])
    return {
        "data": AnnouncementResponse(
            id=ann.id,
            author=AuthorPublic(id=ann.author.id, display_name=ann.author.display_name),
            content=ann.content,
            created_at=ann.created_at,
        )
    }


@router.get("/{tontine_id}/announcements")
async def list_announcements(
    tontine_id: uuid.UUID,
    limit: int = Query(default=20, gt=0, le=50),
    cursor: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, next_cursor, has_more = await announcement_service.list_announcements(
        db, tontine_id, user.id, cursor, limit
    )
    results = [
        AnnouncementResponse(
            id=ann.id,
            author=AuthorPublic(id=ann.author.id, display_name=ann.author.display_name),
            content=ann.content,
            created_at=ann.created_at,
        )
        for ann in items
    ]
    return AnnouncementsListResponse(
        data=results,
        meta=CursorMeta(cursor=next_cursor, has_more=has_more),
    )


@router.delete("/{tontine_id}/announcements/{announcement_id}", status_code=204)
async def delete_announcement(
    tontine_id: uuid.UUID,
    announcement_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await announcement_service.delete_announcement(db, tontine_id, announcement_id, user)


# --- Public invite preview (no auth) ---

public_router = APIRouter(prefix="/invite", tags=["invite"])


@public_router.get("/{code}")
async def get_invite_preview(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint: returns tontine preview for invite link (no auth required)."""
    tontine = await tontine_service.get_tontine_by_invite_code(db, code)
    stats = await tontine_service.get_tontine_stats(db, tontine.id)

    return {
        "data": {
            "name": tontine.name,
            "hand_amount_cents": tontine.hand_amount_cents,
            "frequency": tontine.frequency.value,
            "currency": tontine.currency,
            "member_count": stats["member_count"],
            "pot_per_turn_cents": stats["pot_per_turn_cents"],
        }
    }
