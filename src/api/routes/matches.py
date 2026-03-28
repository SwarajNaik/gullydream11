"""Match routes: list and detail."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.api.dependencies.auth import get_current_user
from src.api.exceptions import NotFoundException
from src.api.schemas.common import APIResponse
from src.db.models import Match, MatchStatus, User
from src.db.session import get_session

router = APIRouter()


class MatchResponse(BaseModel):
    id: int
    tournament_id: int
    team_a: str
    team_a_short: str
    team_a_logo: str | None
    team_b: str
    team_b_short: str
    team_b_logo: str | None
    format: str
    status: str
    venue: str | None
    start_time: datetime
    lock_time: datetime
    result_summary: str | None

    model_config = {"from_attributes": True}


class MatchListResponse(BaseModel):
    matches: list[MatchResponse]


@router.get("", response_model=APIResponse[MatchListResponse])
async def list_matches(
    status: MatchStatus | None = Query(None),
    tournament_id: int | None = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List matches with optional status and tournament filters."""
    query = select(Match)
    if status:
        query = query.where(Match.status == status)
    if tournament_id:
        query = query.where(Match.tournament_id == tournament_id)
    query = query.order_by(Match.start_time.asc())

    result = await session.execute(query)
    matches = result.scalars().all()

    return APIResponse(
        success=True,
        message="Matches fetched",
        data=MatchListResponse(matches=[MatchResponse.model_validate(m) for m in matches]),
    )


@router.get("/{match_id}", response_model=APIResponse[MatchResponse])
async def get_match(
    match_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get match detail with players."""
    result = await session.execute(
        select(Match).where(Match.id == match_id).options(selectinload(Match.players))
    )
    match = result.scalars().first()
    if not match:
        raise NotFoundException("Match not found")

    return APIResponse(
        success=True,
        message="Match fetched",
        data=MatchResponse.model_validate(match),
    )
