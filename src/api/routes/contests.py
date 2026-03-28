"""Contest routes: list, detail, join."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.dependencies.auth import get_current_user
from src.api.exceptions import NotFoundException
from src.api.schemas.common import APIResponse
from src.api.services import contest as contest_service
from src.db.models.models import Contest, ContestEntry, User
from src.db.session import get_session

router = APIRouter()


class ContestResponse(BaseModel):
    id: int
    match_id: int
    name: str
    type: str
    status: str
    entry_fee: float
    total_prize_pool: float
    max_spots: int
    filled_spots: int
    max_teams_per_user: int
    is_guaranteed: bool
    winner_count: int
    prize_breakdown: str | None = None
    invite_code: str | None = None
    model_config = {"from_attributes": True}


class ContestListResponse(BaseModel):
    contests: list[ContestResponse]


class LeaderboardEntry(BaseModel):
    rank: int | None
    user_id: int
    username: str | None = None
    team_name: str | None = None
    total_points: float
    prize: float


class ContestLeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry]


@router.get("", response_model=APIResponse[ContestListResponse])
async def list_contests(
    match_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(Contest).where(Contest.match_id == match_id).order_by(Contest.total_prize_pool.desc())
    )
    contests = result.scalars().all()
    return APIResponse(success=True, message="Contests fetched",
                       data=ContestListResponse(contests=[ContestResponse.model_validate(c) for c in contests]))


@router.get("/{contest_id}", response_model=APIResponse[ContestResponse])
async def get_contest(
    contest_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(Contest).where(Contest.id == contest_id))
    contest = result.scalars().first()
    if not contest:
        raise NotFoundException("Contest not found")
    return APIResponse(success=True, message="Contest fetched",
                       data=ContestResponse.model_validate(contest))


@router.post("/{contest_id}/join", response_model=APIResponse[None], status_code=201)
async def join_contest(
    contest_id: int,
    team_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    await contest_service.join_contest(session, current_user.id, contest_id, team_id)
    return APIResponse(success=True, message="Contest joined")


@router.get("/{contest_id}/leaderboard", response_model=APIResponse[ContestLeaderboardResponse])
async def get_leaderboard(
    contest_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy.orm import selectinload
    entries = list((await session.execute(
        select(ContestEntry).where(ContestEntry.contest_id == contest_id)
        .options(selectinload(ContestEntry.team), selectinload(ContestEntry.user))
        .order_by(ContestEntry.total_points.desc())
    )).scalars().all())

    result = []
    for i, e in enumerate(entries):
        result.append(LeaderboardEntry(
            rank=e.rank or (i + 1),
            user_id=e.user_id,
            username=e.user.username if e.user else None,
            team_name=e.team.name if e.team else None,
            total_points=e.total_points,
            prize=e.prize,
        ))
    return APIResponse(success=True, message="Leaderboard fetched",
                       data=ContestLeaderboardResponse(entries=result))
