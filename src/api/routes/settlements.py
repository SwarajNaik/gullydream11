"""Settlement routes: peer-to-peer settlement tracking."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.api.dependencies.auth import get_current_user
from src.api.schemas.common import APIResponse
from src.api.services import settlement as settlement_service
from src.db.models.models import PeerSettlement, User
from src.db.session import get_session

router = APIRouter()


class PeerSettlementResponse(BaseModel):
    id: int
    payer_user_id: int
    payer_name: str
    payer_username: str
    receiver_user_id: int
    receiver_name: str
    receiver_username: str
    match_id: int
    match_description: str
    contest_id: int
    contest_name: str
    amount: float
    status: str
    payer_confirmed: bool
    receiver_confirmed: bool
    settlement_note: str | None
    created_at: str

    model_config = {"from_attributes": True}


class SettlementListResponse(BaseModel):
    settlements: list[PeerSettlementResponse]
    total: int


class SettlementSummaryResponse(BaseModel):
    total_i_owe: float
    total_owed_to_me: float
    pending_count: int


class MarkSettlementRequest(BaseModel):
    note: str | None = None


def _format_settlement(s: PeerSettlement) -> PeerSettlementResponse:
    match_desc = ""
    if s.match:
        match_desc = f"{s.match.team_a_short} vs {s.match.team_b_short}"
    return PeerSettlementResponse(
        id=s.id,
        payer_user_id=s.payer_user_id,
        payer_name=s.payer.display_name if s.payer else "Unknown",
        payer_username=s.payer.username if s.payer else "unknown",
        receiver_user_id=s.receiver_user_id,
        receiver_name=s.receiver.display_name if s.receiver else "Unknown",
        receiver_username=s.receiver.username if s.receiver else "unknown",
        match_id=s.match_id,
        match_description=match_desc,
        contest_id=s.contest_id,
        contest_name=s.contest.name if s.contest else "",
        amount=s.amount,
        status=s.status.value if hasattr(s.status, "value") else str(s.status),
        payer_confirmed=s.payer_confirmed,
        receiver_confirmed=s.receiver_confirmed,
        settlement_note=s.settlement_note,
        created_at=s.created_at.isoformat() if s.created_at else "",
    )


def _reload_settlement(session, settlement_id):
    """Build a query to reload settlement with all relationships."""
    return (
        select(PeerSettlement)
        .where(PeerSettlement.id == settlement_id)
        .options(
            selectinload(PeerSettlement.payer),
            selectinload(PeerSettlement.receiver),
            selectinload(PeerSettlement.match),
            selectinload(PeerSettlement.contest),
        )
    )


@router.get("/i-owe", response_model=APIResponse[SettlementListResponse])
async def get_settlements_i_owe(
    status: str | None = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get settlements where current user owes money."""
    settlements, total = await settlement_service.get_settlements_i_owe(
        session, current_user.id, status, limit, offset
    )
    return APIResponse(
        success=True,
        message="Settlements fetched",
        data=SettlementListResponse(
            settlements=[_format_settlement(s) for s in settlements],
            total=total,
        ),
    )


@router.get("/owed-to-me", response_model=APIResponse[SettlementListResponse])
async def get_settlements_owed_to_me(
    status: str | None = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get settlements where others owe the current user."""
    settlements, total = await settlement_service.get_settlements_owed_to_me(
        session, current_user.id, status, limit, offset
    )
    return APIResponse(
        success=True,
        message="Settlements fetched",
        data=SettlementListResponse(
            settlements=[_format_settlement(s) for s in settlements],
            total=total,
        ),
    )


@router.get("/summary", response_model=APIResponse[SettlementSummaryResponse])
async def get_settlement_summary(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get summary of pending settlements."""
    summary = await settlement_service.get_settlement_summary(session, current_user.id)
    return APIResponse(
        success=True,
        message="Settlement summary fetched",
        data=SettlementSummaryResponse(**summary),
    )


@router.post("/{settlement_id}/mark-paid", response_model=APIResponse[PeerSettlementResponse])
async def mark_settlement_paid(
    settlement_id: int,
    body: MarkSettlementRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Mark a settlement as paid by the payer."""
    await settlement_service.mark_paid(session, settlement_id, current_user.id, body.note)
    await session.commit()
    result = await session.execute(_reload_settlement(session, settlement_id))
    settlement = result.scalars().first()
    return APIResponse(
        success=True,
        message="Settlement marked as paid",
        data=_format_settlement(settlement),
    )


@router.post("/{settlement_id}/confirm-received", response_model=APIResponse[PeerSettlementResponse])
async def confirm_settlement_received(
    settlement_id: int,
    body: MarkSettlementRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Confirm receipt of a settlement payment."""
    await settlement_service.confirm_received(session, settlement_id, current_user.id, body.note)
    await session.commit()
    result = await session.execute(_reload_settlement(session, settlement_id))
    settlement = result.scalars().first()
    return APIResponse(
        success=True,
        message="Settlement receipt confirmed",
        data=_format_settlement(settlement),
    )


@router.get("/contest/{contest_id}", response_model=APIResponse[SettlementListResponse])
async def get_contest_settlements(
    contest_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get all settlements for a specific contest involving the current user."""
    settlements = await settlement_service.get_contest_settlements(
        session, contest_id, current_user.id
    )
    return APIResponse(
        success=True,
        message="Contest settlements fetched",
        data=SettlementListResponse(
            settlements=[_format_settlement(s) for s in settlements],
            total=len(settlements),
        ),
    )
