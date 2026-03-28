"""Player routes: list players for a match."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.api.dependencies.auth import get_current_user
from src.api.schemas.common import APIResponse
from src.db.models import MatchPlayer, User
from src.db.session import get_session

router = APIRouter()


class MatchPlayerResponse(BaseModel):
    id: int
    match_id: int
    player_id: int
    team: str
    credits: float
    is_playing: bool | None
    selection_pct: float
    captain_pct: float
    vice_captain_pct: float
    # Player info (joined)
    player_name: str | None = None
    player_short_name: str | None = None
    player_role: str | None = None
    player_image_url: str | None = None
    player_country: str | None = None

    model_config = {"from_attributes": True}


class PlayerListResponse(BaseModel):
    players: list[MatchPlayerResponse]


@router.get("", response_model=APIResponse[PlayerListResponse])
async def list_players(
    match_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List players for a match with credits and stats."""
    result = await session.execute(
        select(MatchPlayer)
        .where(MatchPlayer.match_id == match_id)
        .options(selectinload(MatchPlayer.player))
    )
    match_players = result.scalars().all()

    players = []
    for mp in match_players:
        resp = MatchPlayerResponse(
            id=mp.id,
            match_id=mp.match_id,
            player_id=mp.player_id,
            team=mp.team,
            credits=mp.credits,
            is_playing=mp.is_playing,
            selection_pct=mp.selection_pct,
            captain_pct=mp.captain_pct,
            vice_captain_pct=mp.vice_captain_pct,
            player_name=mp.player.name if mp.player else None,
            player_short_name=mp.player.short_name if mp.player else None,
            player_role=mp.player.role.value if mp.player else None,
            player_image_url=mp.player.image_url if mp.player else None,
            player_country=mp.player.country if mp.player else None,
        )
        players.append(resp)

    return APIResponse(
        success=True,
        message="Players fetched",
        data=PlayerListResponse(players=players),
    )
