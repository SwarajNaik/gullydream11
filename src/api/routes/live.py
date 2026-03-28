"""Live data routes: sync matches, fetch scores, trigger updates."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import get_current_user, require_admin
from src.api.schemas.common import APIResponse
from src.api.services import cricket_data
from src.api.services.scheduler import live_match_api_ids
from src.db.models.models import User
from src.db.session import get_session

router = APIRouter()


class SyncResult(BaseModel):
    matches_synced: int
    details: list[dict]


class LiveScoreResult(BaseModel):
    match_id: int
    status: str
    scores_updated: int
    teams_updated: int
    result: str | None = None


class SetApiIdRequest(BaseModel):
    api_match_id: str


# === Admin: Sync matches from CricAPI ===

@router.post("/sync-matches", response_model=APIResponse[SyncResult])
async def sync_matches(
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
):
    """Fetch current/upcoming IPL matches from CricAPI and sync to database."""
    result = await cricket_data.sync_current_matches(session)
    return APIResponse(
        success=True,
        message=f"Synced {len(result)} matches",
        data=SyncResult(matches_synced=len(result), details=result),
    )


# === Admin: Sync squad for a match ===

@router.post("/sync-squad/{match_id}", response_model=APIResponse[dict])
async def sync_squad(
    match_id: int,
    body: SetApiIdRequest,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
):
    """Fetch squad/playing XI for a match from CricAPI."""
    result = await cricket_data.sync_match_squad(session, match_id, body.api_match_id)
    return APIResponse(success=True, message="Squad synced", data=result)


# === Admin: Set API match ID for live polling ===

@router.post("/set-api-id/{match_id}", response_model=APIResponse[None])
async def set_api_match_id(
    match_id: int,
    body: SetApiIdRequest,
    admin: User = Depends(require_admin),
):
    """Map our match ID to CricAPI match ID for live score polling."""
    live_match_api_ids[match_id] = body.api_match_id
    return APIResponse(
        success=True,
        message=f"Match {match_id} mapped to API ID {body.api_match_id}",
    )


# === Admin: Manually trigger live score update ===

@router.post("/sync-scores/{match_id}", response_model=APIResponse[LiveScoreResult])
async def sync_scores(
    match_id: int,
    body: SetApiIdRequest,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
):
    """Manually fetch live scores from CricAPI for a match."""
    result = await cricket_data.sync_live_scores(session, match_id, body.api_match_id)
    return APIResponse(
        success=True,
        message="Live scores synced",
        data=LiveScoreResult(**result),
    )


# === User: Get live match scores (polling endpoint) ===

@router.get("/scores/{match_id}", response_model=APIResponse[dict])
async def get_live_scores(
    match_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get current fantasy points and scores for a match (for frontend polling)."""
    from sqlalchemy.orm import selectinload
    from sqlmodel import select
    from src.db.models.models import MatchPlayer, PlayerScore

    # Get all player scores for this match
    match_players = (await session.execute(
        select(MatchPlayer)
        .where(MatchPlayer.match_id == match_id)
        .options(
            selectinload(MatchPlayer.player),
            selectinload(MatchPlayer.player_score),
        )
    )).scalars().all()

    player_scores = []
    for mp in match_players:
        ps = mp.player_score
        player_scores.append({
            "match_player_id": mp.id,
            "player_name": mp.player.name if mp.player else "",
            "team": mp.team,
            "role": mp.player.role.value if mp.player else "",
            "fantasy_points": ps.fantasy_points if ps else 0,
            "runs": ps.runs if ps else 0,
            "wickets": ps.wickets if ps else 0,
            "catches": ps.catches if ps else 0,
            "balls": ps.balls if ps else 0,
            "overs": ps.overs if ps else 0,
        })

    # Sort by fantasy points
    player_scores.sort(key=lambda x: x["fantasy_points"], reverse=True)

    return APIResponse(
        success=True,
        message="Live scores",
        data={"match_id": match_id, "players": player_scores},
    )
