"""Leaderboard routes: global and contest-specific."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.dependencies.auth import get_current_user
from src.api.schemas.common import APIResponse
from src.db.models import User
from src.db.session import get_session

router = APIRouter()


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    display_name: str
    avatar_url: str | None
    total_winnings: float
    total_matches: int
    total_contests: int
    skill_score: float


class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry]


@router.get("", response_model=APIResponse[LeaderboardResponse])
async def get_global_leaderboard(
    period: str = Query("all_time", regex="^(weekly|monthly|all_time)$"),
    limit: int = Query(50, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get global leaderboard ranked by total winnings."""
    result = await session.execute(
        select(User)
        .where(User.is_active == True)
        .order_by(User.total_winnings.desc())
        .limit(limit)
    )
    users = result.scalars().all()

    entries = [
        LeaderboardEntry(
            rank=i + 1,
            user_id=u.id,
            username=u.username,
            display_name=u.display_name,
            avatar_url=u.avatar_url,
            total_winnings=u.total_winnings,
            total_matches=u.total_matches,
            total_contests=u.total_contests,
            skill_score=u.skill_score,
        )
        for i, u in enumerate(users)
    ]

    return APIResponse(
        success=True,
        message="Leaderboard fetched",
        data=LeaderboardResponse(entries=entries),
    )
